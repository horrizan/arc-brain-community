$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$script:fail = 0

function Check {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][scriptblock]$Test
  )
  try {
    & $Test
    Write-Host "[OK]   $Name" -ForegroundColor Green
  }
  catch {
    Write-Host "[FAIL] $Name - $($_.Exception.Message)" -ForegroundColor Red
    $script:fail++
  }
}

Check 'PowerShell version' {
  if ($PSVersionTable.PSVersion -lt [version]'5.1') {
    throw "PowerShell 5.1 or newer is required; found $($PSVersionTable.PSVersion)"
  }
}

$pslib = Join-Path $Root 'scripts\pslib.ps1'
Check 'PowerShell helper library' {
  if (!(Test-Path -LiteralPath $pslib)) { throw "Missing $pslib" }
}
if (!(Test-Path -LiteralPath $pslib)) {
  Write-Host "`n$script:fail check(s) failed. The helper library is required for remaining checks." -ForegroundColor Yellow
  exit 1
}
. $pslib

$envPath = Join-Path $Root '.env'
Check '.env configuration' {
  if (!(Test-Path -LiteralPath $envPath)) { throw 'Missing .env. Run install.ps1 first.' }
}

$n8nPort = Get-DotEnvValue $envPath 'N8N_PORT'
if (!$n8nPort) { $n8nPort = '5678' }
$controlPort = Get-DotEnvValue $envPath 'ARC_CONTROL_ROOM_PORT'
if (!$controlPort) { $controlPort = '8787' }

Check 'Docker engine' {
  & docker info *> $null
  if ($LASTEXITCODE -ne 0) { throw 'docker info failed; start Docker Desktop' }
}

Check 'Arc containers' {
  $services = @(& docker compose --env-file $envPath -f "$Root\docker\docker-compose.yml" ps --services --filter status=running)
  if ($LASTEXITCODE -ne 0) { throw 'docker compose ps failed' }
  foreach ($name in @('postgres','redis','n8n')) {
    if ($services -notcontains $name) { throw "$name service is not running" }
  }
}

Check 'Ollama API' {
  $response = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
  if (@($response.models).Count -lt 1) { throw 'no Ollama model is installed' }
}

Check 'n8n health' {
  $response = Invoke-WebRequest "http://127.0.0.1:$n8nPort/healthz" -UseBasicParsing -TimeoutSec 5
  if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode)" }
}

Check 'Control Room' {
  $response = Invoke-RestMethod "http://127.0.0.1:$controlPort/health" -TimeoutSec 5
  if (!$response.ok) { throw ([string]$response.error) }
}

Check 'Project config' {
  $projectPath = Join-Path $Root 'config\projects.json'
  if (!(Test-Path -LiteralPath $projectPath)) { throw 'config\projects.json is missing' }
  Get-Content -LiteralPath $projectPath -Raw | ConvertFrom-Json | Out-Null
}

Check 'Python environment' {
  $venvPython = Join-Path $Root '.venv\Scripts\python.exe'
  if (!(Test-Path -LiteralPath $venvPython)) { throw '.venv is missing; run install.ps1' }
  & $venvPython --version | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'virtual-environment Python failed to run' }
}

Check 'Rendered workflows' {
  $workflowDir = Join-Path $Root 'runtime\workflows'
  if (@(Get-ChildItem -Path (Join-Path $workflowDir '*.json') -ErrorAction SilentlyContinue).Count -lt 7) {
    throw 'fewer than 7 rendered workflows found; run finish-setup.ps1'
  }
}

Check 'Arc database' {
  $db = Get-DotEnvValue $envPath 'POSTGRES_DB'
  if (!$db) { $db = 'arcbrain' }
  $user = Get-DotEnvValue $envPath 'POSTGRES_USER'
  if (!$user) { $user = 'arcbrain' }
  & docker compose --env-file $envPath -f "$Root\docker\docker-compose.yml" exec -T postgres psql -U $user -d $db -Atc 'select count(*) from arc.agents;' | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'database query failed' }
}

if ($script:fail -eq 0) {
  Write-Host "`nAll core checks passed." -ForegroundColor Green
  exit 0
}
Write-Host "`n$script:fail check(s) failed. See docs\TROUBLESHOOTING.md." -ForegroundColor Yellow
exit 1
