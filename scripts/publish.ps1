param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$jsonPath = "data/issues/becon-weekly-$Date.json"
$count = 0
if (Test-Path $jsonPath) {
    $count = (Get-Content $jsonPath -Raw | ConvertFrom-Json).papers.Count
}

git add data/issues issues index.html
git commit -m "chore: weekly issue $Date ($count papers)"
git push
Write-Output "[publish] pushed weekly issue $Date"
