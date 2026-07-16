# AGENT.md — Hợp đồng giao tiếp GP cho agent

> Bạn là một agent (Claude Code / worker X2 / bất kỳ). Tài liệu này là
> TẤT CẢ những gì bạn cần để dùng engine GP: đề bài ngôn ngữ tự nhiên
> → spec.json → chạy → đọc kết quả → tự đánh giá. Không cần đọc source.

## 1. Ba lệnh — exit code là hợp đồng

```
python -m geophys validate <spec.json>   # kiểm trước khi đốt máy
python -m geophys run <spec.json> --outdir <dir>   # chạy trọn pipeline
python -m geophys report <dir>           # đọc kết quả run đã xong
```

| exit | nghĩa |
|---|---|
| 0 | thành công / PASS |
| 1 | pipeline chạy xong nhưng FAIL (chưa hội tụ / STL hỏng) |
| 2 | spec rác / tham số sai / thiếu file |

`validate` luôn in JSON ra stdout — kể cả khi spec rác:
`{"trang_thai", "loi": [{"ma", "vi_tri", "ly_do", "goi_y"}], "tom_tat"}`.
Mã lỗi: GP-E-FILE/JSON/SCHEMA/GEOMETRY/PHYSICS. **Vòng sửa spec:**
đọc `loi[].goi_y` → sửa đúng trường `vi_tri` → validate lại, đến khi
HOP_LE mới `run`. Schema đầy đủ: `docs/spec_schema.json`.

## 2. Quy ước không được đoán mò

- Lưới voxel `nelx × nely × nelz` phần tử. Node index 0..nel*.
  Trong render, trục y tăng HƯỚNG XUỐNG (y=0 là mặt trên — xem bài bàn
  đạp Stage 2). Vật lý chỉ phụ thuộc VỊ TRÍ lực/ngàm và tính nhất quán
  dấu; fy=-100 tại đầu tự do + ngàm mặt x0 = công-xôn kinh điển.
- Có `element_size_mm` + `material_name` ⇒ hệ đơn vị THẬT mm-N-MPa.
  Kích thước vật lý = nel* × element_size_mm.
- Vật liệu (materials.json): `nhom_6061_t6` (E 68900 MPa, yield 276) ·
  `ti_6al_4v` (E 113800, yield 880) · `thep_s235` (E 210000, yield 235).
- v1 = `"loads": [...]` (1 case) · v2 = `"load_cases":
  [{"weight": w, "loads": [...]}, ...]` (c = Σ wᵢcᵢ). XOR — không khai cả hai.
- `preserve`/`void`: box/sphere/cylinder theo chỉ số ELEMENT; preserve
  không được giao void. Lỗ bu-lông = void cylinder + vành preserve quanh.
- `supports`: node (`x,y,z` hoặc `node` hoặc `face`) + `dof`
  (all/x/y/z). Thiếu ngàm = GP-E-PHYSICS.
- `simp`: p=3.0; rmin 1.3–2.5 (lưới thô dùng nhỏ, ≥64 voxel/cạnh nên ≥2.5).
- volfrac ∈ (0,1): "giảm X% khối lượng" ⇒ volfrac = 1 − X%.

## 3. Output của `run` (trong --outdir)

`report.json` (status/converged/compliance/volume_fraction/stl/digest)
· `<stem>.stl` (đơn vị VOXEL — nhân element_size_mm khi dùng CAD) ·
`<stem>_iso.png` · `<stem>_viewer.html` · `checkpoint.npz` (resume:
`--resume-from`) · `optimize_log.json` · `report.md`.

## 4. TIÊU CHÍ TỰ ĐÁNH GIÁ (ghi trước — cấm thêm bớt khi chấm)

Một bài được coi là THÀNH CÔNG khi và chỉ khi:
1. `report.status == "PASS"` và `converged == true`
2. `|volume_fraction − volfrac| ≤ 0.01 × volfrac`
3. `stl.watertight == true` và `stl.n_components == 1`
4. Exit code chuỗi lệnh: validate 0 → run 0 → report 0

Ghi kết quả chấm vào `danh_gia.json`: {de_bai, spec_tom_tat, cac_lenh,
tieu_chi: {1..4: true/false}, ket_luan}.

## 5. Giới hạn thật (đừng hứa hộ engine)

Voxel — không phải CAD cong; chi tiết < element_size sẽ mất. Lưới lớn
(64³) cần phút-tới-chục-phút + RAM ~GB. Compliance là độ cứng tương
đối — kiểm bền tuyệt đối (MPa) cần FEM độc lập (xem Stage 2: FreeCAD).
