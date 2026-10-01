param([string]$ApiKey)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
. "$Root\scripts\pslib.ps1"
if (!(Test-Path "$Root\.env")) { throw 'Missing .env. Run install.ps1 first.' }

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  $secure = Read-Host 'Paste your n8n API key' -AsSecureString
  $ApiKey = Convert-SecureToPlain $secure
}
$base = (Get-DotEnvValue "$Root\.env" 'ARC_N8N_BASE_URL')
if (!$base) { $base='http://127.0.0.1:5678' }
$headers = @{ 'X-N8N-API-KEY' = $ApiKey }

Write-Host 'Checking n8n API...' -ForegroundColor Cyan
Invoke-RestMethod -Headers $headers -Uri "$base/api/v1/credentials/schema/postgres" -Method Get | Out-Null

$credName = 'Arc Brain Postgres'
$list = Invoke-RestMethod -Headers $headers -Uri "$base/api/v1/credentials?limit=250" -Method Get
$existing = @($list.data) | Where-Object { $_.name -eq $credName -and $_.type -eq 'postgres' } | Select-Object -First 1
if ($existing) {
  $credId = $existing.id
  Write-Host "Using existing n8n credential: $credName ($credId)"
} else {
  $body = @{
    name=$credName
    type='postgres'
    data=@{
      host='postgres'
      database=(Get-DotEnvValue "$Root\.env" 'POSTGRES_DB')
      user=(Get-DotEnvValue "$Root\.env" 'POSTGRES_USER')
      password=(Get-DotEnvValue "$Root\.env" 'POSTGRES_PASSWORD')
      port=5432
      ssl='disable'
      allowUnauthorizedCerts=$false
      maxConnections=20
    }
  } | ConvertTo-Json -Depth 10
  $created = Invoke-RestMethod -Headers $headers -Uri "$base/api/v1/credentials" -Method Post -ContentType 'application/json' -Body $body
  $credId = $created.id
  Write-Host "Created n8n Postgres credential: $credId" -ForegroundColor Green
}

& "$Root\.venv\Scripts\python.exe" "$Root\scripts\render_workflows.py" --postgres-credential-id $credId --postgres-credential-name $credName

Write-Host 'Importing/updating workflows...' -ForegroundColor Cyan
& docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" exec -T n8n n8n import:workflow --separate --input=/imports
if ($LASTEXITCODE -ne 0) { throw 'Workflow import failed.' }

# Publish the safe inbound/core workflows. Healthcheck remains manual; outbound sender remains disabled.
$activateNames = @(
  'ARC-01 Core Intake Loop',
  'ARC-02 Telegram Intake',
  'ARC-03 Research URLs',
  'ARC-04 Outreach Draft',
  'ARC-06 Code-App Review'
)
$wfList = Invoke-RestMethod -Headers $headers -Uri "$base/api/v1/workflows?limit=250" -Method Get
foreach ($name in $activateNames) {
  $wf = @($wfList.data) | Where-Object { $_.name -eq $name } | Select-Object -First 1
  if ($wf) {
    try {
      Invoke-RestMethod -Headers $headers -Uri "$base/api/v1/workflows/$($wf.id)/activate" -Method Post -ContentType 'application/json' -Body '{}' | Out-Null
      Write-Host "Published $name"
    } catch { Write-Warning "Could not publish $name automatically: $($_.Exception.Message)" }
  } else { Write-Warning "Workflow not found after import: $name" }
}

$state = @{
  installed_at=(Get-Date).ToString('o')
  postgres_credential_id=$credId
  postgres_credential_name=$credName
  n8n_base_url=$base
} | ConvertTo-Json -Depth 6
$state | Set-Content "$Root\runtime\install-state.json" -Encoding utf8

Write-Host 'Running n8n security audit...' -ForegroundColor Cyan
& docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" exec -T n8n n8n audit 2>&1 | Tee-Object -FilePath "$Root\runtime\n8n-audit.txt" | Out-Host

& "$Root\start.ps1" -NoBrowser
Write-Host "`nArc Brain is installed." -ForegroundColor Green
Write-Host 'Run .\doctor.ps1 for a health report.'
Write-Host 'Run .\scripts\test_intake.ps1 for the first end-to-end proposal test.'
$controlPort=Get-DotEnvValue "$Root\.env" 'ARC_CONTROL_ROOM_PORT'; if (!$controlPort) {$controlPort='8787'}
$bridgeToken=Get-DotEnvValue "$Root\.env" 'ARC_CONTROL_ROOM_TOKEN'
Start-Process "http://127.0.0.1:$controlPort/?token=$bridgeToken"
