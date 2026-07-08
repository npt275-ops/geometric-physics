@echo off
REM ============================================================
REM  GP - DO HIEU NANG DoD-1.2 / DoD-1.3 tren laptop that
REM  Chay ~15-60 phut. Ngat giua chung (Ctrl+C) khong sao -
REM  chay lai file nay se TIEP TUC tu checkpoint.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

python --version >nul 2>&1
if errorlevel 1 (
  echo [LOI] Chua cai Python. Tai: https://www.python.org/downloads/
  echo       Khi cai nho tick "Add python.exe to PATH"
  pause & exit /b 1
)

echo Cai dependencies (lan dau hoi vai phut)...
python -m pip install -r requirements.txt --quiet

echo.
echo Bat dau do 64x32x32 (~65k phan tu). De laptop cam sac, dung sleep.
echo.
python scripts\benchmark_laptop.py
echo.
if errorlevel 1 (
  echo KET QUA: co DoD FAIL - gui bench\report_64x32x32.json cho agent.
) else (
  echo KET QUA: DoD-1.2 + DoD-1.3 PASS - commit thu muc bench\ lam bang chung.
)
pause
