param(
  [switch]$SkipBrowserSetup,
  [switch]$InstallMissingPrerequisites
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
. "$Root\scripts\pslib.ps1"

Write-Host "`nArc Brain Community Edition — guided installer" -ForegroundColor Cyan
Write-Host "This installer keeps services on localhost and leaves outbound email disabled by default.`n"

if ($env:OS -ne 'Windows_NT') { throw 'This alpha installer currently supports Windows 11 only.' }

$missing = @()
foreach ($cmd in @('docker','python','ollama')) { if (!(Test-CommandExists $cmd)) { $missing += $cmd } }
if ($missing.Count -gt 0) {
  Write-Host "Missing prerequisites: $($missing -join ', ')" -ForegroundColor Yellow
  if ($InstallMissingPrerequisites -and (Test-CommandExists 'winget')) {
    if ($missing -contains 'python') { winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements }
    if ($missing -contains 'ollama') { winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements }
    if ($missing -contains 'docker') { winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements }
    Write-Host "Prerequisites were requested through winget. Start Docker Desktop, then re-run install.ps1." -ForegroundColor Yellow
    exit 2
  }
  Write-Host "Install Docker Desktop, Python 3.11+ and Ollama, then run this again." -ForegroundColor Yellow
  Write-Host "Tip: re-run with -InstallMissingPrerequisites to let winget request them where available."
  exit 2
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker is installed but not running. Start Docker Desktop and re-run install.ps1.' }

try {
  $pyVersion = & python -c "import sys; print('.'.join(map(str,sys.version_info[:3])))"
  if ([version]$pyVersion -lt [version]'3.11') { throw "Python $pyVersion is too old; use Python 3.11+." }
} catch { throw "Python check failed: $($_.Exception.Message)" }

$statePath = "$Root\runtime\install-state.json"
$envPath = "$Root\.env"
$existingInstall = (Test-Path $statePath) -and (Test-Path $envPath)
if ($existingInstall) {
  Write-Host 'Existing Arc Brain install detected. This run will repair/update it without changing project or model choices.' -ForegroundColor Cyan
}

try { $tags = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5 }
catch {
  Write-Host 'Ollama is installed but its API is not running. Starting ollama serve...' -ForegroundColor Yellow
  Start-Process -WindowStyle Hidden -FilePath 'ollama' -ArgumentList 'serve' | Out-Null
  Start-Sleep -Seconds 3
  try { $tags = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5 }
  catch { throw 'Ollama API is still unavailable at http://127.0.0.1:11434. Start Ollama and re-run install.ps1.' }
}

$models = @($tags.models | ForEach-Object { $_.name })
if ($models.Count -eq 0) {
  Write-Host 'No Ollama models are installed.' -ForegroundColor Yellow
  $ans = Read-Host 'Pull the recommended qwen3.5:9b model now? [Y/n]'
  if ($ans -notmatch '^[Nn]') {
    & ollama pull 'qwen3.5:9b'
    if ($LASTEXITCODE -ne 0) { throw 'Ollama model pull failed.' }
    $models = @('qwen3.5:9b')
  } else { throw 'Arc Brain needs at least one Ollama chat model.' }
}

if ($existingInstall) {
  $fastPattern = Get-DotEnvValue $envPath 'ARC_MODEL_FAST_PATTERN'; if (!$fastPattern) {$fastPattern='.*'}
  $mainPattern = Get-DotEnvValue $envPath 'ARC_MODEL_MAIN_PATTERN'; if (!$mainPattern) {$mainPattern='.*'}
  $reasonerPattern = Get-DotEnvValue $envPath 'ARC_MODEL_REASONER_PATTERN'; if (!$reasonerPattern) {$reasonerPattern='.*'}
} else {
  Write-Host "`nInstalled Ollama models:" -ForegroundColor Cyan
  for ($i=0;$i -lt $models.Count;$i++) { Write-Host " [$($i+1)] $($models[$i])" }
  $advanced = Read-Host "Use separate models for fast / main / reasoning roles? [y/N]"
  function Select-ArcModel([string]$Prompt,[int]$DefaultIndex=1) {
    $pick = Read-Host "$Prompt [$DefaultIndex]"
    if ([string]::IsNullOrWhiteSpace($pick)) { $pick = [string]$DefaultIndex }
    $idx = [int]$pick - 1
    if ($idx -lt 0 -or $idx -ge $models.Count) { throw 'Invalid model selection.' }
    return $models[$idx]
  }
  if ($advanced -match '^[Yy]') {
    $fastModel = Select-ArcModel 'FAST model number' 1
    $mainModel = Select-ArcModel 'MAIN model number' 1
    $reasonerModel = Select-ArcModel 'REASONING model number' 1
  } else {
    $oneModel = Select-ArcModel 'Model to use for all roles' 1
    $fastModel = $oneModel; $mainModel = $oneModel; $reasonerModel = $oneModel
  }
  $fastPattern = [regex]::Escape($fastModel)
  $mainPattern = [regex]::Escape($mainModel)
  $reasonerPattern = [regex]::Escape($reasonerModel)
}


if ($existingInstall) {
  $arcHome = Get-DotEnvValue $envPath 'ARC_HOME'
  if ([string]::IsNullOrWhiteSpace($arcHome)) { $arcHome = Join-Path $env:USERPROFILE 'ArcBrain' }
  $arcInbox = Get-DotEnvValue $envPath 'ARC_INBOX'
  if ([string]::IsNullOrWhiteSpace($arcInbox)) { $arcInbox = Join-Path $arcHome 'Inbox' }
  New-Item -ItemType Directory -Force $arcHome,$arcInbox,(Join-Path $Root 'runtime') | Out-Null
} else {
  $arcHomeDefault = Join-Path $env:USERPROFILE 'ArcBrain'
  $arcHome = Read-Host "Arc data folder [$arcHomeDefault]"
  if ([string]::IsNullOrWhiteSpace($arcHome)) { $arcHome = $arcHomeDefault }
  $arcHome = [IO.Path]::GetFullPath($arcHome)
  $arcInbox = Join-Path $arcHome 'Inbox'
  New-Item -ItemType Directory -Force $arcHome,$arcInbox,(Join-Path $Root 'runtime') | Out-Null

  if (!(Test-Path "$Root\config\projects.json")) { Copy-Item "$Root\config\projects.example.json" "$Root\config\projects.json" }
  $config = Get-Content "$Root\config\projects.json" -Raw | ConvertFrom-Json
  $primary = $config.projects | Where-Object { $_.project_key -eq 'primary_project' }
  $secondary = $config.projects | Where-Object { $_.project_key -eq 'secondary_project' }
  if ($primary -and $secondary) {
    $primaryName = Read-Host "Name your primary project [$($primary.display_name)]"
    if (![string]::IsNullOrWhiteSpace($primaryName)) { $primary.display_name = $primaryName; $primary.aliases += $primaryName; $primary.folder_name = (($primaryName -replace '[<>:"/\\|?*]','-').Trim().TrimEnd('.')) }
    $secondaryName = Read-Host "Name your secondary project [$($secondary.display_name)]"
    if (![string]::IsNullOrWhiteSpace($secondaryName)) { $secondary.display_name = $secondaryName; $secondary.aliases += $secondaryName; $secondary.folder_name = (($secondaryName -replace '[<>:"/\\|?*]','-').Trim().TrimEnd('.')) }
    $config | ConvertTo-Json -Depth 20 | Set-Content "$Root\config\projects.json" -Encoding utf8
  } else {
    Write-Host 'Preconfigured project profile detected; keeping its project names and priorities.' -ForegroundColor Cyan
  }
}


$isNewEnv = !(Test-Path $envPath)
if ($isNewEnv) { Copy-Item "$Root\.env.example" $envPath }

# Preserve cryptographic/database secrets on reruns. Re-running setup must never orphan the existing database.
$pgSecret = Get-DotEnvValue $envPath 'POSTGRES_PASSWORD'
if ([string]::IsNullOrWhiteSpace($pgSecret) -or $pgSecret -like 'GENERATED_*') { $pgSecret = New-ArcSecret 36 }
$n8nSecret = Get-DotEnvValue $envPath 'N8N_ENCRYPTION_KEY'
if ([string]::IsNullOrWhiteSpace($n8nSecret) -or $n8nSecret -like 'GENERATED_*') { $n8nSecret = New-ArcSecret 48 }
$bridgeSecret = Get-DotEnvValue $envPath 'ARC_CONTROL_ROOM_TOKEN'
if ([string]::IsNullOrWhiteSpace($bridgeSecret) -or $bridgeSecret -like 'GENERATED_*') { $bridgeSecret = New-ArcSecret 36 }

# Choose free host ports on first install. Internal Docker service ports remain unchanged.
if ($isNewEnv -and !(Test-Path $statePath)) {
  $n8nPort = Find-AvailableLocalPort @(5678,5679,5680,5681,5682,5683)
  $pgPort = Find-AvailableLocalPort @(5432,55432,55433,55434)
  $controlPort = Find-AvailableLocalPort @(8787,8788,8789,8790,8791)
} else {
  $n8nPort = [int](Get-DotEnvValue $envPath 'N8N_PORT'); if (!$n8nPort) { $n8nPort = 5678 }
  $pgPort = [int](Get-DotEnvValue $envPath 'PGPORT'); if (!$pgPort) { $pgPort = 5432 }
  $controlPort = [int](Get-DotEnvValue $envPath 'ARC_CONTROL_ROOM_PORT'); if (!$controlPort) { $controlPort = 8787 }
}

Set-DotEnvValue $envPath 'ARC_HOME' $arcHome
Set-DotEnvValue $envPath 'ARC_INBOX' $arcInbox
Set-DotEnvValue $envPath 'ARC_SENTINEL_STATE' (Join-Path $arcHome 'arc-sentinel.sqlite3')
Set-DotEnvValue $envPath 'POSTGRES_PASSWORD' $pgSecret
Set-DotEnvValue $envPath 'PGPASSWORD' $pgSecret
Set-DotEnvValue $envPath 'N8N_ENCRYPTION_KEY' $n8nSecret
Set-DotEnvValue $envPath 'N8N_PORT' ([string]$n8nPort)
Set-DotEnvValue $envPath 'PGPORT' ([string]$pgPort)
Set-DotEnvValue $envPath 'ARC_CONTROL_ROOM_PORT' ([string]$controlPort)
Set-DotEnvValue $envPath 'ARC_N8N_BASE_URL' "http://127.0.0.1:$n8nPort"
Set-DotEnvValue $envPath 'ARC_INTAKE_URL' "http://127.0.0.1:$n8nPort/webhook/arc/intake"
Set-DotEnvValue $envPath 'ARC_TELEGRAM_URL' "http://127.0.0.1:$n8nPort/webhook/arc/telegram"
Set-DotEnvValue $envPath 'ARC_CODE_REVIEW_URL' "http://127.0.0.1:$n8nPort/webhook/arc/code-review"
Set-DotEnvValue $envPath 'ARC_CONTROL_ROOM_HOST' '0.0.0.0'
Set-DotEnvValue $envPath 'ARC_CONTROL_ROOM_TOKEN' $bridgeSecret
Set-DotEnvValue $envPath 'ARC_CONTROL_ROOM_REQUIRE_TOKEN' 'true'
Set-DotEnvValue $envPath 'ARC_MODEL_FAST_PATTERN' $fastPattern
Set-DotEnvValue $envPath 'ARC_MODEL_MAIN_PATTERN' $mainPattern
Set-DotEnvValue $envPath 'ARC_MODEL_REASONER_PATTERN' $reasonerPattern

Write-Host "`nCreating Python environment..." -ForegroundColor Cyan
if (!(Test-Path "$Root\.venv\Scripts\python.exe")) { & python -m venv "$Root\.venv" }
& "$Root\.venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Host
& "$Root\.venv\Scripts\python.exe" -m pip install -r "$Root\scripts\requirements.txt" | Out-Host

& "$Root\scripts\create_inbox.ps1"

Write-Host "`nStarting n8n/Postgres/Redis..." -ForegroundColor Cyan
& docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" up -d
if ($LASTEXITCODE -ne 0) { throw 'Docker stack failed to start.' }

Write-Host 'Applying Arc database schema...'
& "$Root\scripts\apply_db.ps1"
& "$Root\.venv\Scripts\python.exe" "$Root\scripts\sync_agents.py"
& "$Root\.venv\Scripts\python.exe" "$Root\scripts\sync_projects.py"

if (Test-Path $statePath) {
  Write-Host "`nExisting Arc Brain setup detected. Preserving credentials and updating local workflows." -ForegroundColor Cyan
  $installState = Get-Content $statePath -Raw | ConvertFrom-Json
  if ($installState.postgres_credential_id) {
    & "$Root\.venv\Scripts\python.exe" "$Root\scripts\render_workflows.py" --postgres-credential-id $installState.postgres_credential_id --postgres-credential-name $installState.postgres_credential_name
    & docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" exec -T n8n n8n import:workflow --separate --input=/imports
    if ($LASTEXITCODE -ne 0) { throw 'Workflow update failed.' }
  }
  & "$Root\start.ps1" -NoBrowser
  Write-Host "Re-run complete. Existing secrets were preserved." -ForegroundColor Green
  & "$Root\doctor.ps1"
  exit 0
}

Write-Host "`nBase install complete." -ForegroundColor Green
Write-Host 'There is one unavoidable n8n browser step on a brand-new self-hosted instance: create the owner account and an API key.'
Write-Host 'In n8n: create/sign in to the owner account, then open Settings > n8n API > Create an API key.' -ForegroundColor Yellow
if (!$SkipBrowserSetup) {
  Start-Process "http://127.0.0.1:$n8nPort"
  Read-Host 'Press ENTER after you have copied the n8n API key'
  & "$Root\finish-setup.ps1"
} else {
  Write-Host 'When ready, run .\finish-setup.ps1' -ForegroundColor Yellow
}
