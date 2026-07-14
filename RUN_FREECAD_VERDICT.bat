@echo off
REM ============================================================
REM  GP - PHIEN TOA DoD-2.3: ban dap phanh vs 276 MPa
REM  Macro tu dong: scale mm that, nhom 6061, ngam lo truc,
REM  1200N len pad, CalculiX, verdict + safety factor.
REM  ~3-8 phut. Log: bench\brake_verdict_console.log
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set "GP_ROOT=%~dp0"
set FCCMD=

for /d %%d in ("C:\Program Files\FreeCAD*") do if exist "%%d\bin\FreeCADCmd.exe" set "FCCMD=%%d\bin\FreeCADCmd.exe"

if "%FCCMD%"=="" goto nofc

echo Dung: "%FCCMD%"
copy /y "%~dp0scripts\freecad_brake_verdict.py" "%TEMP%\gp_brake_verdict.py" >nul
if not exist "%TEMP%\gp_brake_verdict.py" goto nocopy

echo Dang xet xu... Gmsh + CalculiX tren vat the 160mm
if not exist bench mkdir bench
"%FCCMD%" "%TEMP%\gp_brake_verdict.py" > "%TEMP%\gp_brake_console.log" 2>&1
copy /y "%TEMP%\gp_brake_console.log" bench\brake_verdict_console.log >nul
echo.
echo ===== 25 dong cuoi log =====
powershell -NoProfile -Command "Get-Content -LiteralPath $env:TEMP\gp_brake_console.log -Tail 25"
echo.
if not exist bench\freecad_brake_verdict.json goto noreport

echo ===== bench\freecad_brake_verdict.json =====
type bench\freecad_brake_verdict.json
echo.
echo BUOC CUOI - mat NGUOI ky DoD-2.3:
echo   1. Double-click bench\brake_pedal_verdict.FCStd
echo   2. Double-click CCX_Results, Mode=Surface, Field=von Mises Stress, Apply
echo   3. Kiem: mau nong quanh lo truc / co chuyen tiep la hop ly;
echo      khong vung do bat thuong giua khong trung
echo   4. Chup man hinh, luu bench\brake_verdict_vonmises.png
echo   5. Neu verdict AN TOAN va mat ban dong y: bao agent "DoD-2.3 OK"
echo      kem von_mises_max va safety_factor
goto end

:nofc
echo [LOI] Khong thay FreeCADCmd.exe trong "C:\Program Files\FreeCAD*"
goto end

:nocopy
echo [LOI] Khong copy duoc script sang TEMP.
goto end

:noreport
echo [LOI] Khong co report - gui bench\brake_verdict_console.log cho agent.
goto end

:end
echo.
pause
