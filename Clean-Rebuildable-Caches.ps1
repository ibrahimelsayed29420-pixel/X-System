$ErrorActionPreference='Stop'
$xHome=[Environment]::GetFolderPath('UserProfile')
$xTargets=@('AppData\Local\pip\Cache','AppData\Local\npm-cache','.npm','AppData\Local\uv\cache','.cache\uv')
$xReport=@()
$xBefore=(Get-PSDrive -Name C).Free
foreach($xRelative in $xTargets){
 $xTarget=[IO.Path]::GetFullPath((Join-Path $xHome $xRelative))
 $xAllowed=[IO.Path]::GetFullPath((Join-Path 'C:\Users\nenoh' $xRelative))
 if($xTarget -ne $xAllowed -or -not $xTarget.StartsWith('C:\Users\nenoh\')){throw 'Cache path validation failed'}
 if(-not(Test-Path -LiteralPath $xTarget)){continue}
 $xItem=Get-Item -LiteralPath $xTarget -Force
 if($xItem.Attributes -band [IO.FileAttributes]::ReparsePoint){$xReport+=@{Path=$xTarget;Status='Skipped link'};continue}
 # Restrict removal to the exact named regenerable cache roots; never use drive-wide enumeration.
 $xErrors=@()
 Remove-Item -LiteralPath $xTarget -Recurse -Force -ErrorAction SilentlyContinue -ErrorVariable xErrors
 $xReport+=@{Path=$xTarget;Status=$(if(Test-Path -LiteralPath $xTarget){'Partial; locked files retained'}else{'Removed'});ErrorCount=$xErrors.Count}
}
$xAfter=(Get-PSDrive -Name C).Free
$xResult=@{Targets=$xReport;CFreeBeforeGiB=[math]::Round($xBefore/1GB,2);CFreeAfterGiB=[math]::Round($xAfter/1GB,2);ObservedFreeChangeGiB=[math]::Round(($xAfter-$xBefore)/1GB,2);Note='Only exact pip/npm/uv caches. Free-space change includes unrelated concurrent disk activity.'}
$xResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'D:\X-System\cleanup-result.json' -Encoding UTF8
$xResult | ConvertTo-Json -Depth 5
