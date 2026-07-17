@echo off
REM ============================================================
REM  GP GAUNTLET - 10 bai khao tra hop den tren may that
REM  Ky vong dang ky truoc: specs/stage3-t6-gauntlet.md (dddfa66)
REM  Double-click la chay. Log: bench\gauntlet_console.log
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

echo ============================================
echo    GP GAUNTLET - 10 BAI KHAO TRA
echo ============================================
echo Chay ~3-10 phut tuy may. Log ghi vao bench\gauntlet_console.log
echo.

python --version >nul 2>&1
if errorlevel 1 goto nopython

python scripts\run_gauntlet.py > bench\gauntlet_console.log 2>&1
set KQ=%ERRORLEVEL%

type bench\gauntlet_console.log
echo.
if %KQ%==0 goto ok
echo [CHU Y] Co bai LECH ngoai du bao - xem bang tren va
echo bench\gauntlet\ket_qua_laptop.json. Gui log cho ky su truong.
goto het

:ok
echo ============================================
echo  GAUNTLET PASS - 9 DAT + bai08 dung du bao
echo  Bang chung: bench\gauntlet\ket_qua_laptop.json
echo ============================================
goto het

:nopython
echo [LOI] Khong thay python trong PATH.
goto het

:het
echo.
pause
