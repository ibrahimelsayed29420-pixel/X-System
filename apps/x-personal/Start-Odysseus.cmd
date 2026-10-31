@echo off
cd /d D:\X-System\runtime\odysseus
set PYTHONUTF8=1
set ODYSSEUS_DATA_DIR=D:\X-System\data\odysseus
set ODYSSEUS_WORKSPACE_DEFAULT=D:\X-System\apps\x-personal
set AUTH_ENABLED=true
set LOCALHOST_BYPASS=false
set LLM_HOST=127.0.0.1
set OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
"D:\X-System\runtime\odysseus-venv\Scripts\python.exe" setup.py
if errorlevel 1 goto failed
start "" http://127.0.0.1:7011
"D:\X-System\runtime\odysseus-venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 7011
:failed
pause
