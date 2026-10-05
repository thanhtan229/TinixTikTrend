@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\restore.ps1"
    exit /b %ERRORLEVEL%
)
if "%~1"=="--help" goto usage
if "%~1"=="-h" goto usage

if "%~1"=="--recover" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\restore.ps1" -Recover
    exit /b %ERRORLEVEL%
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\restore.ps1" -CandidatePath "%~1"
exit /b %ERRORLEVEL%

:usage
echo =========================================================================
echo  HUONG DAN SU DUNG CONG CU PHUC HOI CO SO DU LIEU (RESTORE.bat)
echo =========================================================================
echo.
echo  1. Phuc hoi tu tap tin sao luu:
echo     RESTORE.bat ^<duong-dan-tap-tin-backup^>
echo.
echo     Vi du:
echo     RESTORE.bat backend\.local\backups\tinix-affiliate-v1-20261005T120000.000000Z.sqlite3
echo.
echo  2. Khoi phuc sau su co gian doan (Crash Recovery):
echo     RESTORE.bat --recover
echo.
echo  3. Liet ke cac ban sao luu quan ly:
echo     RESTORE.bat
echo.
echo =========================================================================
exit /b 1
