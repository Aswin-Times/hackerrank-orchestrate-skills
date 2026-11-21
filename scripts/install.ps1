# Install the hr-orchestrate skills for Claude Code.
#   .\scripts\install.ps1                  -> $HOME\.claude\skills (all projects)
#   .\scripts\install.ps1 -Project C:\repo -> C:\repo\.claude\skills (one challenge repo)
param([string]$Project = "")
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $PSScriptRoot
if ($Project -ne "") { $dest = Join-Path $Project ".claude\skills" } else { $dest = Join-Path $HOME ".claude\skills" }
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Get-ChildItem -Directory (Join-Path $here "skills") -Filter "hr-orchestrate*" | ForEach-Object {
    $target = Join-Path $dest $_.Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Copy-Item -Recurse $_.FullName $target
    Write-Output "installed $($_.Name) -> $target"
}
Write-Output "Done. Start a Claude Code session in the challenge repo and say: use hr-orchestrate"
