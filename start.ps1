param([switch]$NoBrowser)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
. "$Root\scripts\pslib.ps1"
& docker compose --env-file "$Root\.env" -f "$Root\docker\docker-compose.yml" up -d
$py="$Root\.venv\Scripts\python.exe"
if (!(Test-Path $py)) { throw 'Missing Python venv. Run install.ps1.' }

# Stop stale tracked processes first.
$pidsPath="$Root\runtime\pids.json"
if (Test-Path $pidsPath) {
  try {
    $old=Get-Content $pidsPath -Raw | ConvertFrom-Json
    foreach ($id in @($old.control_room,$old.sentinel,$old.telegram)) { if ($id) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue } }
  } catch {}
}
$control=Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList @("$Root\scripts\control_room.py") -WorkingDirectory $Root
$sentinel=Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList @("$Root\scripts\arc_sentinel.py") -WorkingDirectory $Root
$telegram=$null
$token=Get-DotEnvValue "$Root\.env" 'TELEGRAM_BOT_TOKEN'
if ($token -and $token -ne 'CHANGE_ME') {
  $telegram=Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList @("$Root\scripts\telegram_gateway.py") -WorkingDirectory $Root
}
@{control_room=$control.Id;sentinel=$sentinel.Id;telegram=if($telegram){$telegram.Id}else{$null}} | ConvertTo-Json | Set-Content $pidsPath -Encoding utf8
Write-Host 'Arc Brain local services started.' -ForegroundColor Green
$controlPort=Get-DotEnvValue "$Root\.env" 'ARC_CONTROL_ROOM_PORT'; if (!$controlPort) {$controlPort='8787'}
$bridgeToken=Get-DotEnvValue "$Root\.env" 'ARC_CONTROL_ROOM_TOKEN'
if (!$NoBrowser) { Start-Process "http://127.0.0.1:$controlPort/?token=$bridgeToken" }
