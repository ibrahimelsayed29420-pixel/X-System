@echo off
setlocal
set "PYTHONUTF8=1"
set "PIP_CACHE_DIR=D:\X-System\cache\pip"
set "PYTHONDONTWRITEBYTECODE=1"
cd /d "%~dp0"
if not exist "D:\X-System\runtime\x-personal-venv\Scripts\python.exe" (
  echo X Python environment is missing. See README_AR.md.
  exit /b 1
)
if "%~1"=="" (
  "D:\X-System\runtime\x-personal-venv\Scripts\python.exe" -m x_personal doctor
) else (
  "D:\X-System\runtime\x-personal-venv\Scripts\python.exe" -m x_personal %*
)
