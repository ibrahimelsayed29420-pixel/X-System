$ErrorActionPreference='Stop'
& 'D:\X-System\runtime\x-personal-venv\Scripts\python.exe' "$PSScriptRoot\setup_speech_model.py"
if($LASTEXITCODE -ne 0){throw 'Speech model preparation failed'}
