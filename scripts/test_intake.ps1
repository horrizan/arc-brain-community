$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envPath = Join-Path $Root '.env'
if (!(Test-Path $envPath)) { throw 'Missing .env. Run install.ps1.' }
$intake = (Get-Content $envPath | Where-Object { $_ -match '^ARC_INTAKE_URL=' } | Select-Object -First 1).Substring('ARC_INTAKE_URL='.Length)
$body = @{
  source='manual-test'
  source_ref='quickstart'
  item_type='idea'
  title='Arc Brain smoke test'
  text='Create the smallest useful automation that turns this idea into a proposal.'
  project_hint='primary_project'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri $intake -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 20
