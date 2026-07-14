# -*- coding: utf-8 -*-
"""PHIEN TOA DoD-2.3 - ban dap phanh nhom 6061 truoc FreeCAD/CalculiX.

Cau hoi duy nhat: Von Mises max < 276 MPa duoi 1200N?
File THUAN ASCII + chay tu %TEMP% + GP_ROOT env (bai hoc encoding 1.5).
Script chi THU bang chung va tinh verdict - NGUOI ky quyet dinh cuoi.
"""

import importlib
import json
import os
import tempfile
import traceback

ROOT = os.environ.get("GP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
ROOT = ROOT.rstrip("\\/")
STL = os.path.join(ROOT, "media", "brake_pedal.stl")
SPEC = os.path.join(ROOT, "examples", "spec_brake_pedal.json")
BENCH = os.path.join(ROOT, "bench")
REPORT = os.path.join(BENCH, "freecad_brake_verdict.json")
FCSTD = os.path.join(BENCH, "brake_pedal_verdict.FCStd")
PNG = os.path.join(BENCH, "brake_verdict_vonmises.png")

YIELD_MPA = 276.0
F_MAIN_N = 1200.0
PIVOT_XY_MM = (20.0, 40.0)   # tam truc pivot sau scale
HOLE_R_MM = 7.5              # ban kinh chon mat lo truc
PAD_X_MIN_MM = 140.0         # vung pad (x >= 140mm)

report = {"status": "FAIL", "yield_MPa": YIELD_MPA, "steps": []}


def step(msg):
    report["steps"].append(msg)
    print("[verdict] " + msg, flush=True)


def finish():
    os.makedirs(BENCH, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=True, indent=2)
    print("[verdict] report -> " + REPORT, flush=True)


def _fc_module(name):
    # Module chi ton tai trong Python nhung cua FreeCAD (xem 1.5).
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise SystemExit(
            "Chay file nay bang FreeCADCmd.exe hoac FreeCAD GUI, khong "
            "phai python thuong. Thieu: " + str(exc))


try:
    FreeCAD = _fc_module("FreeCAD")
    Mesh = _fc_module("Mesh")
    ObjectsFem = _fc_module("ObjectsFem")
    Part = _fc_module("Part")

    if not os.path.isfile(STL):
        raise RuntimeError("Khong thay STL: " + STL)
    with open(SPEC, "r", encoding="utf-8") as fh:
        scale = float(json.load(fh)["element_size_mm"])
    report["scale_mm_per_voxel"] = scale

    doc = FreeCAD.newDocument("brake_verdict")
    step("FreeCAD %s" % ".".join(str(v) for v in FreeCAD.Version()[:3]))

    Mesh.insert(STL, doc.Name)
    mesh_obj = [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")][0]
    step("import STL: %d mat tam giac" % mesh_obj.Mesh.CountFacets)

    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)
    solid = Part.makeSolid(shape)
    # SCALE ve mm that: STL GP o toa do voxel (1 voxel = element_size_mm)
    mtx = FreeCAD.Matrix()
    mtx.scale(scale, scale, scale)
    solid = solid.transformGeometry(mtx)
    bb = solid.BoundBox
    step("scale x%.1f -> bbox %.1f x %.1f x %.1f mm"
         % (scale, bb.XLength, bb.YLength, bb.ZLength))
    if abs(bb.XLength - 160.0) > 8.0:
        raise RuntimeError(
            "Scale guard: be dai %.1fmm lech qua 5%% so 160mm" % bb.XLength)

    part_obj = doc.addObject("Part::Feature", "BrakePedal")
    part_obj.Shape = solid

    cx, cy = PIVOT_XY_MM
    fixed_faces, load_faces = [], []
    for i, f in enumerate(solid.Faces):
        c = f.CenterOfMass
        if ((c.x - cx) ** 2 + (c.y - cy) ** 2) ** 0.5 <= HOLE_R_MM:
            fixed_faces.append("Face%d" % (i + 1))
        elif c.y < bb.YMin + 1.5 and c.x >= PAD_X_MIN_MM:
            load_faces.append("Face%d" % (i + 1))
    step("chon mat: ngam lo truc=%d, pad tai=%d"
         % (len(fixed_faces), len(load_faces)))
    if not fixed_faces or not load_faces:
        raise RuntimeError("Khong tim du mat ngam/tai - kiem tra hinh hoc")

    analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
    analysis.addObject(solver)

    mat = ObjectsFem.makeMaterialSolid(doc, "Al6061T6")
    m = dict(mat.Material)
    m.update({"Name": "Aluminium-6061-T6", "YoungsModulus": "68900 MPa",
              "PoissonRatio": "0.33", "Density": "2700 kg/m^3"})
    mat.Material = m
    analysis.addObject(mat)
    step("vat lieu: nhom 6061-T6 (E 68900 MPa, yield %.0f MPa)" % YIELD_MPA)

    fixed = ObjectsFem.makeConstraintFixed(doc, "NgamLoTruc")
    fixed.References = [(part_obj, tuple(fixed_faces))]
    analysis.addObject(fixed)

    dir_line = doc.addObject("Part::Feature", "HuongDapY")
    dir_line.Shape = Part.makeLine(
        FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
    force = ObjectsFem.makeConstraintForce(doc, "Luc1200N")
    force.References = [(part_obj, tuple(load_faces))]
    force.Force = "1200 N"
    force.Direction = (dir_line, ["Edge1"])
    force.Reversed = False  # +y = huong dap (y-down cua luoi GP)
    analysis.addObject(force)
    step("tai: 1200N huong +y len pad")

    fem_mesh = ObjectsFem.makeMeshGmsh(doc, "GmshMesh")
    fem_mesh.Shape = part_obj
    fem_mesh.CharacteristicLengthMax = 4.0  # mm (vat the 160mm)
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
    if hasattr(fea, "run_all_tasks"):
        fea.run_all_tasks()
    else:
        fea.write_inp_file()
        fea.ccx_run()
        fea.load_results()
    step("CalculiX chay xong")

    results = [o for o in doc.Objects
               if o.isDerivedFrom("Fem::FemResultObject")]
    if not results:
        raise RuntimeError("Khong co ket qua - CalculiX loi?")
    res = results[0]
    vm = list(res.vonMises)
    if not vm or max(vm) <= 0:
        raise RuntimeError("Von Mises rong/0")
    vm_max = max(vm)
    imax = vm.index(vm_max)
    pos = fem_mesh.FemMesh.Nodes[res.NodeNumbers[imax]]
    n_over = sum(1 for v in vm if v >= YIELD_MPA)
    verdict_pass = vm_max < YIELD_MPA and n_over == 0
    report.update({
        "n_nodes": fem_mesh.FemMesh.NodeCount,
        "von_mises_max_MPa": round(vm_max, 3),
        "von_mises_mean_MPa": round(sum(vm) / len(vm), 3),
        "vi_tri_max_mm": {"x": round(pos.x, 1), "y": round(pos.y, 1),
                          "z": round(pos.z, 1)},
        "so_node_vuot_yield": n_over,
        "safety_factor": round(YIELD_MPA / vm_max, 3),
        "verdict": "AN TOAN (vm_max < 276 MPa)" if verdict_pass
        else "KHONG DAT (vm_max >= 276 MPa)",
    })
    step("VON MISES MAX = %.2f MPa | yield 276 | safety factor %.2f | %s"
         % (vm_max, YIELD_MPA / vm_max,
            "PASS" if verdict_pass else "FAIL"))

    doc.saveAs(FCSTD)
    step("luu " + FCSTD)

    if FreeCAD.GuiUp:
        Gui = _fc_module("FreeCADGui")
        res.ViewObject.Visibility = True
        try:
            res.ViewObject.DisplayMode = "Surface"
        except Exception as exc:  # khac nhau giua ban FreeCAD
            step("DisplayMode mac dinh (%s)" % exc)
        Gui.SendMsgToActiveView("ViewFit")
        Gui.activeDocument().activeView().saveImage(PNG, 1600, 900)
        step("screenshot -> " + PNG)

    report["status"] = ("PASS-MAY (cho NGUOI ky DoD-2.3)" if verdict_pass
                        else "FAIL-VATLY (S2-R3: xem lai volume/mesh/tai)")
except Exception:
    report["error"] = traceback.format_exc()
    print(report["error"], flush=True)
finally:
    finish()
