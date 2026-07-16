@echo off
REM ============================================================
REM  GP - PUSH LEN GITHUB (dong DoD-0.7)
REM  Double-click file nay. Lan dau se hien cua so dang nhap
REM  GitHub (Git Credential Manager) - dang nhap 1 lan la xong.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

echo ============================================
echo    GP - PUSH LEN GITHUB  (dong DoD-0.7)
echo ============================================

git --version >nul 2>&1
if errorlevel 1 goto nogit

git remote get-url origin >nul 2>&1
if not errorlevel 1 goto dopush

echo.
echo Chua co remote 'origin'. Lam 2 buoc:
echo.
echo   B1. Mo trang:  https://github.com/new
echo       - Ten goi y: geometric-physics
echo       - Private hay Public deu duoc (Actions chay ca hai)
echo       - KHONG tick "Add a README" (repo phai TRONG)
echo.
echo   B2. Copy URL repo vua tao, dan vao duoi day roi Enter
echo       (vi du: https://github.com/tenban/geometric-physics.git)
echo.
set /p REPO_URL="URL repo: "
if "%REPO_URL%"=="" goto emptyurl
git remote add origin %REPO_URL%
if errorlevel 1 goto badurl

:dopush
echo.
echo Dang push nhanh main len GitHub ...
git push -u origin main
if errorlevel 1 goto pushfail

for /f "delims=" %%u in ('git remote get-url origin') do set URL=%%u
set URL=%URL:.git=%
echo.
echo ============================================
echo    PUSH XONG!
echo    Trinh duyet se mo tab Actions.
echo    CHO 4 O MATRIX XANH (Win+Ubuntu x Py3.11/3.12)
echo    roi quay lai bao agent:  "CI xanh 4/4"
echo ============================================
start "" %URL%/actions
pause
exit /b 0

:nogit
echo [LOI] May chua cai Git for Windows.
echo Tai tai: https://git-scm.com/download/win  (cai xong chay lai file nay)
pause
exit /b 1

:emptyurl
echo [LOI] Chua nhap URL. Chay lai file va dan URL repo.
pause
exit /b 1

:badurl
echo [LOI] URL khong hop le hoac remote da ton tai loi. Kiem tra lai URL.
pause
exit /b 1

:pushfail
echo [LOI] Push that bai. Nguyen nhan thuong gap:
echo   - Chua dang nhap: cua so Git Credential Manager bi dong -^> chay lai
echo   - Repo tao co san README -^> tao repo TRONG moi, hoac chay:
echo       git pull origin main --rebase   roi chay lai file nay
pause
exit /b 1
