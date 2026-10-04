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

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\health_check.ps1" -Target "%TARGET%"

echo.
pause
