$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
. "$Root\scripts\pslib.ps1"
$envPath = "$Root\.env"
if (!(Test-Path $envPath)) { throw 'Missing .env. Run install.ps1 first.' }
$dbUser = Get-DotEnvValue $envPath 'POSTGRES_USER'; if (!$dbUser) {$dbUser='arcbrain'}
$dbName = Get-DotEnvValue $envPath 'POSTGRES_DB'; if (!$dbName) {$dbName='arcbrain'}
Get-ChildItem .\db\*.sql | Sort-Object Name | ForEach-Object {
  Write-Host "Applying $($_.Name)..."
  Get-Content $_.FullName -Raw | docker compose --env-file $envPath -f "$Root\docker\docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U $dbUser -d $dbName
  if ($LASTEXITCODE -ne 0) { throw "Database migration failed: $($_.Name)" }
}
Write-Host 'Database migrations applied.'
