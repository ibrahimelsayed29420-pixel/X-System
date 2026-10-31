$ErrorActionPreference='Stop'
$xBefore=Get-Content -LiteralPath 'D:\X-System\environment-before.json' -Raw | ConvertFrom-Json
foreach($xKey in @('HF_HOME','OLLAMA_MODELS','PIP_CACHE_DIR','npm_config_cache','UV_CACHE_DIR')){
 [Environment]::SetEnvironmentVariable($xKey,$xBefore.$xKey,'User')
}
Write-Output 'Previous user storage settings restored. Reopen apps to use them.'
