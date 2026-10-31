$ErrorActionPreference = 'Stop'
$xWorkspace = 'D:\X-System'
$xFolders = @('data\inbox','data\originals','data\catalog','knowledge','rules','media\working','media\exports','models\ollama','models\huggingface','cache\pip','cache\npm','cache\uv','runtime','apps','logs')
foreach ($xFolder in $xFolders) { New-Item -ItemType Directory -Path (Join-Path $xWorkspace $xFolder) -Force | Out-Null }
$env:HF_HOME = Join-Path $xWorkspace 'models\huggingface'
$env:OLLAMA_MODELS = Join-Path $xWorkspace 'models\ollama'
$env:PIP_CACHE_DIR = Join-Path $xWorkspace 'cache\pip'
$env:npm_config_cache = Join-Path $xWorkspace 'cache\npm'
$env:UV_CACHE_DIR = Join-Path $xWorkspace 'cache\uv'
Write-Output 'X workspace paths prepared for this PowerShell session. No services or downloads started.'
