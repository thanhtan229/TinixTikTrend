@echo off
setlocal
chcp 65001 >nul
cls

set "TARGET=All"
if /i "%~1"=="frontend" set "TARGET=Frontend"
if /i "%~1"=="front" set "TARGET=Frontend"
if /i "%~1"=="ui" set "TARGET=Frontend"
if /i "%~1"=="backend" set "TARGET=Backend"
if /i "%~1"=="back" set "TARGET=Backend"
if /i "%~1"=="api" set "TARGET=Backend"

echo ====================================================================
echo   TikTok Shop Affiliate Trend Hunter - Dang dung dich vu [%TARGET%]...
echo ====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_services.ps1" -Target "%TARGET%"

echo.
set "SERVICE_EXIT=%ERRORLEVEL%"
if not %SERVICE_EXIT% EQU 0 (
    echo [FAILED] Khong dung duoc dich vu. Xem logs/services.log
    exit /b %SERVICE_EXIT%
)
echo [DONE] Phien lam viec [%TARGET%] da duoc dung thanh cong!
ping 127.0.0.1 -n 2 >nul

exit /b %SERVICE_EXIT%
