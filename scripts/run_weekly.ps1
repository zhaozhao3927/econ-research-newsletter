param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$SkipPublish,
    [switch]$ForceSummarize
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

New-Item -ItemType Directory -Force cache | Out-Null
New-Item -ItemType Directory -Force logs | Out-Null
New-Item -ItemType Directory -Force data/issues | Out-Null
New-Item -ItemType Directory -Force issues | Out-Null

$Log = "logs/$Date.log"
function Log([string]$msg) {
    $line = "$(Get-Date -Format HH:mm:ss) $msg"
    $line | Tee-Object -FilePath $Log -Append
}

Log "Run started"
python src/fetch.py --config config.yaml --output cache/papers_raw.json
$summarizeArgs = @(
    "src/summarize.py",
    "--config", "config.yaml",
    "--input", "cache/papers_raw.json",
    "--output", "cache/papers_summarized.json"
)
if ($ForceSummarize) { $summarizeArgs += "--force" }
python @summarizeArgs
python src/build_issue.py --config config.yaml --input cache/papers_summarized.json --date $Date
python src/render.py --template templates/issue.html.j2 --input "data/issues/becon-weekly-$Date.json" --output "issues/becon-weekly-$Date.html"
python src/update_index.py --data-dir data/issues --template templates/index.html.j2 --output index.html

if (-not $SkipPublish) {
    & "$PSScriptRoot\publish.ps1" -Date $Date
} else {
    Log "SkipPublish is enabled"
}

Log "Run completed"
