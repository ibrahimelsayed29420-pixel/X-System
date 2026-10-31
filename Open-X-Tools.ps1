$ErrorActionPreference = 'Stop'
. 'D:\X-System\Start-X-Workspace.ps1'
$env:Path = 'D:\X-System\runtime\bin;' + $env:Path
git --version
node --version
python --version
Set-Location -LiteralPath 'D:\X-System'
