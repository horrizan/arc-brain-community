param([switch]$StopDocker)
$ErrorActionPreference='Continue'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$pidsPath="$Root\runtime\pids.json"
if (Test-Path $pidsPath) {
  $p=Get-Content $pidsPath -Raw | ConvertFrom-Json
  foreach ($id in @($p.control_room,$p.sentinel,$p.telegram)) { if ($id) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue } }
  Remove-Item $pidsPath -Force -ErrorAction SilentlyContinue
}
if ($StopDocker -and (Test-Path "$Root\.env")) {
  & docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" stop
}
Write-Host 'Arc Brain host helpers stopped.'
