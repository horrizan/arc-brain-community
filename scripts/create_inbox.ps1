$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$configPath = Join-Path $Root 'config\projects.json'
if (!(Test-Path $configPath)) { throw "Missing $configPath. Run install.ps1 first." }

$envFile = Join-Path $Root '.env'
$arcInbox = Join-Path $env:USERPROFILE 'ArcBrain\Inbox'
if (Test-Path $envFile) {
  $line = Get-Content $envFile | Where-Object { $_ -match '^ARC_INBOX=' } | Select-Object -First 1
  if ($line) { $arcInbox = $line.Substring('ARC_INBOX='.Length) }
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$paths = @(
  (Join-Path $arcInbox 'Code'),
  (Join-Path $arcInbox 'Apps'),
  (Join-Path $arcInbox 'Ideas'),
  (Join-Path $arcInbox 'Screenshots'),
  (Join-Path $arcInbox 'Documents'),
  (Join-Path $arcInbox 'Research'),
  (Join-Path $arcInbox 'Unknown')
)
foreach ($p in $config.projects) {
  $projectFolder = $p.folder_name
  if ([string]::IsNullOrWhiteSpace($projectFolder)) { $projectFolder = $p.display_name }
  foreach ($folder in $p.folders) {
    $paths += Join-Path (Join-Path $arcInbox $projectFolder) $folder
  }
}
$paths | Sort-Object -Unique | ForEach-Object { New-Item -ItemType Directory -Force $_ | Out-Null }
Write-Host "Created/verified watched folders under $arcInbox"
