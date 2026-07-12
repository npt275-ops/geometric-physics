# -*- coding: utf-8 -*-
"""Smoke test DoD-1.7 TỰ ĐỘNG — chạy bằng FreeCADCmd (headless) hoặc trong GUI.

Pipeline: STL → Shape → Solid → FEM (thép generic, ngàm mặt x0, lực -Y
100N ở đầu tự do) → Gmsh → CalculiX → đọc Von Mises → bằng chứng vào bench/:
  - freecad_report.json  (máy đọc được: max stress, vị trí, verdict)
  - cantilever_smoketest.FCStd  (mở GUI xem màu Von Mises)
  - freecad_vonmises.png  (chỉ khi chạy trong GUI)

Cách chạy: double-click RUN_FREECAD_TEST.bat  (hoặc trong FreeCAD:
Macro ▸ Macros… ▸ trỏ tới file này ▸ Execute).
Chú ý: script chỉ THU bằng chứng — phán "đạt/không" cuối cùng là mắt NGƯỜI.
"""

import json
import os
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "media", "cantilever3d_60x20x4.stl")
BENCH = os.path.join(ROOT, "bench")
REPORT = os.path.join(BENCH, "freecad_report.json")
FCSTD = os.path.join(BENCH, "cantilever_smoketest.FCStd")
PNG = os.path.join(BENCH, "freecad_vonmises.png")

report = {"status": "FAIL", "steps": []}


def step(msg):
    report["steps"].append(msg)
    print("[smoketest] " + msg)


def finish():
    os.makedirs(BENCH, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("[smoketest] report -> " + REPORT)


# Các module dưới đây CHỈ tồn tại trong Python nhúng của FreeCAD —
# nạp qua importlib kèm guard, để trạm gác repo không nhầm là ghost-import
# và để ai chạy nhầm bằng python thường nhận thông báo rõ ràng.
import importlib


def _fc_module(name):
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise SystemExit(
            "File này phải chạy bằng FreeCADCmd.exe hoặc trong FreeCAD GUI "
            "(Macro > Macros...), không phải python thường. Thiếu: "
            + str(exc))


try:
    FreeCAD = _fc_module("FreeCAD")
    Mesh = _fc_module("Mesh")
    ObjectsFem = _fc_module("ObjectsFem")
    Part = _fc_module("Part")

    doc = FreeCAD.newDocument("smoketest")
    step("FreeCAD %s — tạo document" % ".".join(
        str(v) for v in FreeCAD.Version()[:3]))

    Mesh.insert(STL, doc.Name)
    mesh_obj = [o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")][0]
    step("import STL: %d mặt tam giác" % mesh_obj.Mesh.CountFacets)

    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)
    solid = Part.makeSolid(shape)
    part_obj = doc.addObject("Part::Feature", "GP_Solid")
    part_obj.Shape = solid
    step("Shape→Solid OK: volume=%.1f, %d faces"
         % (solid.Volume, len(solid.Faces)))

    bb = solid.BoundBox
    fixed_faces = ["Face%d" % (i + 1) for i, f in enumerate(solid.Faces)
                   if f.BoundBox.XMax < bb.XMin + 0.8]
    load_faces = ["Face%d" % (i + 1) for i, f in enumerate(solid.Faces)
                  if f.BoundBox.XMin > bb.XMax - 2.5]
    step("chọn mặt: ngàm=%d (x≈%.1f), tải=%d (x≈%.1f)"
         % (len(fixed_faces), bb.XMin, len(load_faces), bb.XMax))
    if not fixed_faces or not load_faces:
        raise RuntimeError("Không tìm được mặt ngàm/tải — kiểm tra STL")

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

    # Hướng lực -Y: mượn cạnh của một đoạn thẳng làm tham chiếu hướng
    dir_line = doc.addObject("Part::Feature", "HuongY")
    dir_line.Shape = Part.makeLine(
        FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
    force = ObjectsFem.makeConstraintForce(doc, "Luc100N")
    force.References = [(part_obj, tuple(load_faces))]
    force.Force = "100 N"
    force.Direction = (dir_line, ["Edge1"])
    force.Reversed = True  # -Y (y lưới hướng xuống là +y vật lý đảo)
    analysis.addObject(force)
    step("ràng buộc: ngàm + lực 100N hướng -Y")

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
    step("CalculiX chạy xong")

    results = [o for o in doc.Objects
               if o.isDerivedFrom("Fem::FemResultObject")]
    if not results:
        raise RuntimeError("Không có object kết quả — CalculiX lỗi?")
    res = results[0]
    vm = list(res.vonMises)
    if not vm or max(vm) <= 0:
        raise RuntimeError("Von Mises rỗng/0 — kết quả không hợp lệ")
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
    step("Von Mises max %.2f MPa tại x=%.1f (%s ngàm)" % (
        max(vm), pos.x, "GẦN" if near_fixed else "XA"))

    doc.saveAs(FCSTD)
    step("lưu " + FCSTD)

    if FreeCAD.GuiUp:
        Gui = _fc_module("FreeCADGui")
        res.ViewObject.Visibility = True
        try:
            res.ViewObject.DisplayMode = "Surface"
        except Exception as exc:  # tên DisplayMode khác nhau giữa bản FreeCAD
            step("không đặt được DisplayMode (%s) — dùng mặc định" % exc)
        Gui.SendMsgToActiveView("ViewFit")
        Gui.activeDocument().activeView().saveImage(PNG, 1600, 900)
        step("screenshot GUI -> " + PNG)
    else:
        step("headless — mở file FCStd trong GUI để xem màu + screenshot")

    report["status"] = "PASS-MAY (chờ mắt người xác nhận + screenshot GUI)"
except Exception:
    report["error"] = traceback.format_exc()
    print(report["error"])
finally:
    finish()
