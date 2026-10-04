@echo off
setlocal
chcp 65001 >nul
cls

echo ====================================================================
echo   TikTok Shop Affiliate Trend Hunter - Khoi chay He thong Cuc bo
echo ====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_services.ps1" -RestartOld -OpenBrowser -TimeoutSec 60

set "SERVICE_EXIT=%ERRORLEVEL%"
if %SERVICE_EXIT% EQU 0 (
    echo.
    echo [KHOI CHAY THANH CONG] He thong da san sang!
) else (
    echo.
    echo [KHOI CHAY THAT BAI] Mot hoac ca hai dich vu gap su co khi khoi dong.
)

ping 127.0.0.1 -n 3 >nul

exit /b %SERVICE_EXIT%
