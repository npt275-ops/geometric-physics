@echo off
REM ============================================================
REM  GP - SMOKE TEST FREECAD TU DONG (DoD-1.7)  [ban v3]
REM  v3: FreeCADCmd vo encoding voi duong dan co dau "Nha Kho"
REM      -> copy script sang %TEMP% (ASCII) roi chay tu do;
REM      vi tri repo truyen qua bien GP_ROOT.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set "GP_ROOT=%~dp0"
set FCCMD=

for /d %%d in ("C:\Program Files\FreeCAD*") do if exist "%%d\bin\FreeCADCmd.exe" set "FCCMD=%%d\bin\FreeCADCmd.exe"

if "%FCCMD%"=="" goto nofc

echo Dung: "%FCCMD%"
echo Copy script sang TEMP de ne duong dan co dau...
copy /y "%~dp0scripts\freecad_smoketest.py" "%TEMP%\gp_fc_test.py" >nul
if not exist "%TEMP%\gp_fc_test.py" goto nocopy

echo Dang chay smoke test headless ~2-5 phut...
if not exist bench mkdir bench
"%FCCMD%" "%TEMP%\gp_fc_test.py" > "%TEMP%\gp_fc_console.log" 2>&1
copy /y "%TEMP%\gp_fc_console.log" bench\freecad_console.log >nul
echo.
echo ===== 30 dong cuoi cua log =====
powershell -NoProfile -Command "Get-Content -LiteralPath $env:TEMP\gp_fc_console.log -Tail 30"
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
echo Neu FreeCAD cai noi khac: mo file nay bang Notepad, sua dong
echo   set FCCMD=
echo thanh duong dan day du toi FreeCADCmd.exe cua ban.
goto end

:nocopy
echo [LOI] Khong copy duoc script sang TEMP. Chay thu cong trong FreeCAD:
echo   Macro, Macros..., chon scripts\freecad_smoketest.py, Execute.
goto end

:noreport
echo [LOI] Khong sinh duoc report - gui file bench\freecad_console.log cho agent.
goto end

:end
echo.
pause
