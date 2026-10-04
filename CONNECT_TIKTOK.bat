@echo off
setlocal
cd /d "%~dp0backend"
".venv\Scripts\python.exe" -m app.connect_tiktok
set "SESSION_EXIT=%ERRORLEVEL%"
if not "%SESSION_EXIT%"=="0" echo Khong tao duoc phien. Kiem tra ket noi va Playwright Chromium.
pause
exit /b %SESSION_EXIT%
