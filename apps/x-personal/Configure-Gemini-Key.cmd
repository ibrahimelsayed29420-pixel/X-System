@echo off
setlocal
set "PYTHON=%~dp0..\..\runtime\x-workflow-venv\Scripts\python.exe"
"%PYTHON%" "%~dp0configure_gemini_key.py"
if errorlevel 1 pause
