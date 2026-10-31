@echo off
setlocal
set "SCRIPT=%~dp0install_mind_runtime.ps1"
if not exist "%SCRIPT%" (
    echo X installer was not found: "%SCRIPT%"
    exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
exit /b %errorlevel%
