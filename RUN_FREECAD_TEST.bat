@echo off
REM ============================================================
REM  GP - SMOKE TEST FREECAD TU DONG (DoD-1.7)  [ban v2]
REM  v2: sua loi ngoac don trong khoi if lam cua so tu tat;
REM      output FreeCAD ghi vao bench\freecad_console.log
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set FCCMD=

for /d %%d in ("C:\Program Files\FreeCAD*") do if exist "%%d\bin\FreeCADCmd.exe" set "FCCMD=%%d\bin\FreeCADCmd.exe"

if "%FCCMD%"=="" goto nofc

echo Dung: "%FCCMD%"
echo Dang chay smoke test headless ~2-5 phut...
echo Log day du: bench\freecad_console.log
if not exist bench mkdir bench
"%FCCMD%" "%~dp0scripts\freecad_smoketest.py" > bench\freecad_console.log 2>&1
echo.
echo ===== 30 dong cuoi cua log =====
powershell -NoProfile -Command "Get-Content bench\freecad_console.log -Tail 30"
echo.
if not exist bench\freecad_report.json goto noreport

echo ===== bench\freecad_report.json =====
type bench\freecad_report.json
echo.
echo BUOC CUOI CUA BAN - mat nguoi ky DoD-1.7:
echo   1. Double-click bench\cantilever_smoketest.FCStd
echo   2. Click CCX_Results trong cay, xem mau Von Mises
echo   3. Kiem: vung do/cam GAN NGAM x=0, dau tu do xanh duong
echo   4. Chup man hinh, luu thanh bench\freecad_vonmises.png
echo   5. Bao agent: "DoD-1.7 OK" kem so von_mises_max
goto end

:nofc
echo [LOI] Khong tim thay FreeCADCmd.exe trong "C:\Program Files\FreeCAD*"
echo Neu FreeCAD cai noi khac: mo file nay