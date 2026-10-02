$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$statePath="$Root\runtime\install-state.json"
if(!(Test-Path $statePath)){throw 'Missing install state. Run finish-setup.ps1 first.'}
$state=Get-Content $statePath -Raw | ConvertFrom-Json
& "$Root\.venv\Scripts\python.exe" "$Root\scripts\render_workflows.py" --postgres-credential-id $state.postgres_credential_id --postgres-credential-name $state.postgres_credential_name
& docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" exec -T n8n n8n import:workflow --separate --input=/imports
if($LASTEXITCODE -ne 0){throw 'Workflow update failed.'}
Write-Host 'Workflows imported. Re-publish any workflow that n8n deactivated during import.' -ForegroundColor Yellow
