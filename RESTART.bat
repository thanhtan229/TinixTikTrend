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
echo   TikTok Shop Affiliate Trend Hunter - RESTART SERVICES [%TARGET%]
echo ====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_services.ps1" -Target "%TARGET%" -RestartOld -TimeoutSec 60

set "SERVICE_EXIT=%ERRORLEVEL%"
if %SERVICE_EXIT% EQU 0 (
    echo.
    echo [RESTART THANH CONG] Ung dung da san sang cho ban kiem thu!
) else (
    echo.
    echo [RESTART THAT BAI] Mot hoac ca hai dich vu gap su co khi khoi dong.
)

ping 127.0.0.1 -n 3 >nul

exit /b %SERVICE_EXIT%
