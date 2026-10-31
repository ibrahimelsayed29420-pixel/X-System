$ErrorActionPreference = 'Stop'
$mindRoot = 'D:\X-System\apps\x-personal'
$mindPython = 'D:\X-System\runtime\x-personal-venv\Scripts\pythonw.exe'
$mindStartup = [Environment]::GetFolderPath('Startup')
$mindShell = New-Object -ComObject WScript.Shell
$mindLink = $mindShell.CreateShortcut((Join-Path $mindStartup 'X Mind Background.lnk'))
$mindLink.TargetPath = $mindPython
$mindLink.Arguments = '"D:\X-System\apps\x-personal\mind_service.py"'
$mindLink.WorkingDirectory = $mindRoot
$mindLink.Description = 'X local background mind; starts with this Windows user. No screen or microphone monitoring.'
$mindLink.Save()
$mindWscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
$companionLauncher = Join-Path $mindRoot 'Launch-X-Mind-Companion.vbs'
if (-not (Test-Path -LiteralPath $companionLauncher)) {
    throw "X companion launcher was not found: $companionLauncher"
}
$companionLink = $mindShell.CreateShortcut((Join-Path $mindStartup 'X Mind Companion.lnk'))
$companionLink.TargetPath = $mindWscript
$companionLink.Arguments = "`"$companionLauncher`""
$companionLink.WorkingDirectory = $mindRoot
$companionLink.Description = 'Small interactive X companion; reads only X runtime state.'
$companionLink.Save()
Start-Process -FilePath $mindPython -ArgumentList '"D:\X-System\apps\x-personal\mind_service.py"' -WorkingDirectory $mindRoot -WindowStyle Hidden
Start-Process -FilePath $mindWscript -ArgumentList "`"$companionLauncher`"" -WorkingDirectory $mindRoot
Write-Output 'X background runtime and interactive companion started; both launch for this Windows user at sign-in.'
