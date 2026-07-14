@echo off
REM ============================================================
REM  GP - BAI CHUAN BAN DAP PHANH (tang 2.3, DoD-2.1/2.2/2.4)
REM  Chay 2 luot toi uu (multi 3-case + single doi chung).
REM  Uoc ~30-60 phut. Ngat (Ctrl+C) roi chay lai = TIEP TUC.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

python --version >nul 2>&1
if errorlevel 1 goto nopy

echo Cai dependencies neu thieu...
python -m pip install -r requirements.txt --quiet

echo.
echo Bat dau bai ban dap phanh. De laptop cam sac, dung sleep.
echo.
python scripts\run_brake_pedal.py
echo.
if errorlevel 1 goto fail
echo KET QUA: 3/3 DoD PASS - commit bench\ + media\ lam bang chung,
echo bao agent: "brake pedal OK" kem ty_so_DoD21_c3.
goto end

:nopy
echo [LOI] Chua cai Python / chua co trong PATH.
goto end

:fail
echo KET QUA: co DoD FAIL - gui bench\report_brake_pedal.json cho agent.
goto end

:end
echo.
pause
