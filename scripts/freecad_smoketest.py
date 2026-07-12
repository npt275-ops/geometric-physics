# -*- coding: utf-8 -*-
"""Smoke test DoD-1.7 TU DONG - chay bang FreeCADCmd (headless) hoac GUI.

File nay THUAN ASCII (khong dau): FreeCADCmd 1.1 tren Windows vo encoding
voi duong dan/noi dung Unicode ("Nha Kho" -> "Nh? Kho", loi thuc te 12/07).
RUN_FREECAD_TEST.bat copy file nay sang %TEMP% (ASCII) roi chay; vi tri
repo truyen qua bien moi truong GP_ROOT (Python doc Unicode env chuan).

Pipeline: STL -> Solid -> FEM (thep generic, ngam mat x0, luc -Y 100N
dau tu do) -> Gmsh -> CalculiX -> doc Von Mises -> bang chung vao bench/.
Script chi THU bang chung - phan quyet cuoi cung la mat NGUOI.
"""

import importlib
import json
import os
import tempfile
import traceback

ROOT = os.environ.get("GP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
ROOT = ROOT.rstrip("\\/")
STL = os.path.join(ROOT, "media", "cantilever3d_60x20x4.stl")
BENCH = os.path.join(ROOT, "bench")
REPORT = os.path.join(BENCH, "freecad_report.json")
FCSTD = os.path.join(BENCH, "cantilever_smoketest.FCStd")
PNG = os.path.join(BENCH, "freecad_vonmises.png")

report = {"status": "FAIL", "gp_root": ROOT, "steps": []}


def step(msg):
    report["steps"].append(msg)
    print("[smoketest] " + msg, flush=True)


def finish():
    os.makedirs(BENCH, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=True, indent=2)
    print("[smoketest] report -> " + REPORT, flush=True)


def _fc_module(name):
    # Cac module nay CHI ton tai trong Python nhung cua FreeCAD - nap qua
    # importlib de tram gac repo khong nham ghost-import, va ai chay nham
    # bang python thuong se nhan thong bao ro rang.
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise SystemExit(
            "File nay phai chay bang FreeCADCmd.exe hoac trong FreeCAD GUI "
            "(Macro > Macros...), khong phai python thuong. Thieu: "
            + str(exc))


try:
    FreeCAD = _fc_module("FreeCAD")
    Mesh = _fc_module("Mesh")
    ObjectsFem = _fc_module("ObjectsFem")
    Part = _fc_module("Part")

    if not os.path.isfile(STL):
        raise RuntimeError("Khong thay STL: " + STL
                           + " - kiem tra bien GP_ROOT")

    doc = FreeCAD.newDocument("smoketest")
    step("FreeCAD %s - tao document" % ".".join(
        str(v) for v in FreeCAD.Version()[:3]))

    Mesh.insert(STL, doc.Name)
    mesh_obj = [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")][0]
    step("import STL: %d mat tam giac" % mesh_obj.Mesh.CountFacets)

    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)
    solid = Part.makeSolid(shape)
    part_obj = doc.addObject("Part::Feature", "GP_Solid")
    part_obj.Shape = solid
    step("Shape->Solid OK: volume=%.1f, %d faces"
         % (solid.Volume, len(solid.Faces)))

    bb = solid.BoundBox
    fixed_faces = ["Face%d" % (i + 1) for i, f in enumerate(solid.Faces)
                   if f.BoundBox.XMax < bb.XMin + 0.8]
    load_faces = ["Face%d" % (i + 1) for i, f in enumerate(solid.Faces)
                  if f.BoundBox.XMin > bb.XMax - 2.5]
    step("chon mat: ngam=%d (x~%.1f), tai=%d (x~%.1f)"
         % (len(fixed_faces), bb.XMin, len(load_faces), bb.XMax))
    if not fixed_faces or not load_faces:
        raise RuntimeError("Khong tim duoc mat ngam/tai - kiem tra STL")

    analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
    analysis.addObject(solver)

    mat = ObjectsFem.makeMaterialSolid(doc, "Steel")
    m = dict(mat.Material)
    m.update({"Name": "Steel-Generic", "YoungsModulus": "210000 MPa",
              "PoissonRatio": "0.30", "Density": "7900 kg/m^3"})
    mat.Material = m
    analysis.addObject(mat)

    fixed = ObjectsFem.makeConstraintFixed(doc, "NgamX0")
    fixed.References = [(part_obj, tuple(fixed_faces))]
    analysis.addObject(fixed)

    # Huong luc -Y: muon canh mot doan thang lam tham chieu huong
    dir_line = doc.addObject("Part::Feature", "HuongY")
    dir_line.Shape = Part.makeLine(
        FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
    force = ObjectsFem.makeConstraintForce(doc, "Luc100N")
    force.References = [(part_obj, tuple(load_faces))]
    force.Force = "100 N"
    force.Direction = (dir_line, ["Edge1"])
    force.Reversed = True
    analysis.addObject(force)
    step("rang buoc: ngam + luc 100N huong -Y")

    fem_mesh = ObjectsFem.makeMeshGmsh(doc, "GmshMesh")
    fem_mesh.Shape = part_obj
    fem_mesh.CharacteristicLengthMax = 2.0
    analysis.addObject(fem_mesh)
    gmshtools = _fc_module("femmesh.gmshtools")
    err = gmshtools.GmshTools(fem_mesh).create_mesh()
    if err:
        raise RuntimeError("Gmsh: " + str(err))
    step("Gmsh: %d nodes, %d volume elements"
         % (fem_mesh.FemMesh.NodeCount, fem_mesh.FemMesh.VolumeCount))

    doc.recompute()
    ccxtools = _fc_module("femtools.ccxtools")
    fea = ccxtools.FemToolsCcx(analysis, solver)
    fea.update_objects()
    fea.setup_working_dir(tempfile.mkdtemp())
    msg = fea.check_prerequisites()
    if msg:
        raise RuntimeError("Prerequisites: " + msg)
    fea.purge_results()
    fea.run_all_tasks()
    step("CalculiX chay xong")

    results = [o for o in doc.Objects
               if o.isDerivedFrom("Fem::FemResultObject")]
    if not results:
        raise RuntimeError("Khong co object ket qua - CalculiX loi?")
    res = results[0]
    vm = list(res.vonMises)
    if not vm or max(vm) <= 0:
        raise RuntimeError("Von Mises rong/0 - ket qua khong hop le")
    imax = vm.index(max(vm))
    node_id = res.NodeNumbers[imax]
    pos = fem_mesh.FemMesh.Nodes[node_id]
    span = bb.XMax - bb.XMin
    near_fixed = (pos.x - bb.XMin) < 0.5 * span
    report.update({
        "n_nodes": fem_mesh.FemMesh.NodeCount,
        "von_mises_max_MPa": round(max(vm), 3),
        "von_mises_mean_MPa": round(sum(vm) / len(vm), 3),
        "vi_tri_max": {"x": round(pos.x, 1), "y": round(pos.y, 1),
                       "z": round(pos.z, 1)},
        "max_o_nua_gan_ngam": bool(near_fixed),
    })
    step("Von Mises max %.2f MPa tai x=%.1f (%s ngam)" % (
        max(vm), pos.x, "GAN" if near_fixed else "XA"))

    doc.saveAs(FCSTD)
    step("luu " + FCSTD)

    if FreeCAD.GuiUp:
        Gui = _fc_module("FreeCADGui")
        res.ViewObject.Visibility = True
        try:
            res.ViewObject.DisplayMode = "Surface"
        except Exception as exc:  # ten DisplayMode khac nhau giua ban FreeCAD
            step("khong dat duoc DisplayMode (%s) - dung mac dinh" % exc)
        Gui.SendMsgToActiveView("ViewFit")
        Gui.activeDocument().activeView().saveImage(PNG, 1600, 900)
        step("screenshot GUI -> " + PNG)
    else:
        step("headless - mo file FCStd trong GUI de xem mau + screenshot")

    report["status"] = "PASS-MAY (cho mat nguoi xac nhan + screenshot GUI)"
except Exception:
    report["error"] = traceback.format_exc()
    print(report["error"], flush=True)
finally:
    finish()
