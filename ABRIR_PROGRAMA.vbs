Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectPath = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fso.BuildPath(projectPath, "run_api_silencioso.ps1")
powershellPath = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"

quote = Chr(34)
cmd = quote & powershellPath & quote & " -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & quote & scriptPath & quote

shell.Run cmd, 0, False
