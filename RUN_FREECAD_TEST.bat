@echo off
REM ============================================================
REM  GP - SMOKE TEST FREECAD TU DONG (DoD-1.7)
REM  Tu tim FreeCADCmd.exe, chay pipeline FEM headless ~2-5 phut.
REM  Bang chung ghi vao bench\: freecad_report.json + .FCStd
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set FCCMD=

for /d %%d in ("C:\Program Files\FreeCAD*") do (
  if exist "%%d\bin\FreeCADCmd.exe" set "FCCMD=%%d\bin\FreeCADCmd.exe"
)
if "%FCCMD%"=="" (
  echo [LOI] Khong tim thay FreeCADCmd.exe trong "C:\Program Files\FreeCAD*"
  echo Neu cai cho khac: mo file nay, sua dong set FCCMD= thanh duong dan day du.
  echo Hoac chay thu cong trong FreeCAD: Macro ^> Macros... ^> scripts\freecad_smoketest.py
  pause & exit /b 1
)

echo Dung: %FCCMD%
echo Dang chay smoke test headless (~2-5 phut, cho den khi xong)...
"%FCCMD%" "%~dp0scripts\freecad_smoketest.py"
echo.
if exist bench\freecad_report.json (
  echo ===== bench\freecad_report.json =====
  type bench\freecad_report.json
  echo.
  echo BUOC CUOI CUA BAN (mat nguoi ky DoD-1.7):
  echo   1. Double-click bench\cantilever_smoketest.FCStd
  echo   2. Click CCX_Results trong cay ^> xem mau Von Mises
  echo   3. Kiem: vung do/cam GAN NGAM x=0, dau tu do xanh
  echo   4. Chup man hinh -^> luu bench\freecad_vonmises.png
  echo   5. Bao agent: "DoD-1.7 OK" kem so von_mises_max
) else (
  echo [LOI] Khong co report - gui toan bo output tren cho agent.
)
pause
