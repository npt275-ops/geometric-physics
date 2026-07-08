# HƯỚNG DẪN SMOKE TEST FREECAD — DoD-1.7 (FreeCAD 1.1.x)

> Mục đích: chứng minh vật thể GP "mọc" ra ĐỨNG ĐƯỢC trong phần mềm công
> nghiệp độc lập — mở được, mesh được, phân tích tĩnh chạy hết, ứng suất
> phân bố hợp lý. CHƯA phán "an toàn" (đó là Stage 2 với vật liệu thật).
> Thời gian: ~15–20 phút. File: `media/cantilever3d_60x20x4.stl`.

## Bước 1 — Nạp STL và đổi thành Solid
1. Mở FreeCAD → **File ▸ New**.
2. **File ▸ Import** → chọn `media/cantilever3d_60x20x4.stl`.
3. Chuyển workbench sang **Mesh Design** (menu thả xuống giữa toolbar).
4. Chọn mesh trong cây → menu **Meshes ▸ Create shape from mesh** → OK
   (dung sai mặc định).
5. Chọn shape vừa tạo → workbench **Part** → menu
   **Part ▸ Convert to solid**. Cây giờ có `...(Solid)`.
   ✅ *Đến đây không lỗi = STL hợp lệ với CAD công nghiệp.*

## Bước 2 — Dựng bài phân tích FEM
6. Chuyển workbench **FEM**.
7. Chọn Solid trong cây → nút **[A] Analysis container** (Model ▸ Analysis).
8. Nút **Material for solid** → chọn **Steel (generic)** → OK.
   (Định tính — vật liệu thật là chuyện Stage 2.)
9. Nút **Fixed boundary condition** → click chọn MẶT PHẲNG tại đầu x = 0
   (mặt bị ngàm — mặt phẳng lớn vuông góc trục dài) → OK.
10. Nút **Force boundary condition** → chọn mặt/cạnh ở ĐẦU TỰ DO
    (x = 60, phía cạnh dưới nơi thấy vật liệu tụ) → Force = **100 N**,
    Direction: chọn một mặt nằm ngang rồi tick **Reverse** nếu cần cho
    lực chỉ XUỐNG (−y) → OK.

## Bước 3 — Mesh và chạy
11. Chọn Solid → nút **Mesh ▸ FEM mesh from shape by Gmsh** →
    Max element size: **2.0** → Apply → đợi Gmsh chạy xong → OK.
12. Trong cây, double-click **CalculiX/Solver** (SolverCcx) →
    **Write .inp file** → **Run CalculiX**.
    ✅ *"CalculiX done without error!" = phân tích tĩnh CHẠY HẾT.*

## Bước 4 — Đọc kết quả + thu bằng chứng
13. Double-click **CCX_Results** trong cây → chọn **Von Mises stress**.
14. KIỂM TRA ĐỊNH TÍNH (đúng cả 2 = smoke test ĐẠT):
    - [ ] Vùng đỏ/cam (ứng suất cao) tập trung GẦN NGÀM (x = 0) và dọc
      các thanh chịu lực chính.
    - [ ] Đầu tự do và các vùng thoáng gần như xanh dương (ứng suất thấp).
15. Thu bằng chứng vào thư mục `bench/`:
    - Screenshot toàn màn hình kết quả Von Mises → `bench/freecad_vonmises.png`
    - **File ▸ Save** → `bench/cantilever_smoketest.FCStd`
16. Commit: mở terminal trong folder GP:
    `git add bench && git commit -m "evidence: DoD-1.7 FreeCAD smoke test"`
    (hoặc để agent commit hộ — chỉ cần báo "đã có bằng chứng trong bench/").

## Nếu kẹt
- Import STL không thấy gì → View ▸ Fit all (phím **0**).
- Gmsh lỗi → tăng Max element size lên 3.0.
- CalculiX lỗi thiếu ràng buộc → kiểm bước 9 đã chọn đúng MẶT (không phải cạnh).
- Vẫn kẹt → chụp màn hình lỗi gửi agent.
