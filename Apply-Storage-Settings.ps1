$ErrorActionPreference='Stop'
$xSettings=@{
 HF_HOME='D:\X-System\models\huggingface'
 OLLAMA_MODELS='D:\X-System\models\ollama'
 PIP_CACHE_DIR='D:\X-System\cache\pip'
 npm_config_cache='D:\X-System\cache\npm'
 UV_CACHE_DIR='D:\X-System\cache\uv'
}
foreach($xEntry in $xSettings.GetEnumerator()){
 New-Item -ItemType Directory -Path $xEntry.Value -Force | Out-Null
 [Environment]::SetEnvironmentVariable($xEntry.Key,$xEntry.Value,'User')
 if([Environment]::GetEnvironmentVariable($xEntry.Key,'User') -ne $xEntry.Value){throw 'Setting verification failed'}
}
$xSettings | ConvertTo-Json | Set-Content -LiteralPath 'D:\X-System\environment-applied.json' -Encoding UTF8
Write-Output 'PASS five persistent user cache/model locations saved and read back. New processes use D. No services started.'
