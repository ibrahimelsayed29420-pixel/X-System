Option Explicit

Dim shell, filesystem, root, powershell, script
Set shell = CreateObject("WScript.Shell")
Set filesystem = CreateObject("Scripting.FileSystemObject")

root = filesystem.GetParentFolderName(WScript.ScriptFullName)
powershell = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
script = root & "\mind_companion.ps1"

shell.Run Chr(34) & powershell & Chr(34) & _
    " -NoProfile -ExecutionPolicy Bypass -STA -File " & Chr(34) & script & Chr(34), 0, False
