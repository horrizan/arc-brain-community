$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$py = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $py)) { throw 'Missing .venv. Follow docs\INSTALL-WINDOWS.md first.' }
Start-Process powershell -ArgumentList '-NoExit','-Command',"& '$py' '$Root\scripts\control_room.py'" -WorkingDirectory $Root
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList '-NoExit','-Command',"& '$py' '$Root\scripts\arc_sentinel.py'" -WorkingDirectory $Root
if ((Get-Content .\.env -Raw) -match 'TELEGRAM_BOT_TOKEN=(?!CHANGE_ME)\S+') {
  Start-Process powershell -ArgumentList '-NoExit','-Command',"& '$py' '$Root\scripts\telegram_gateway.py'" -WorkingDirectory $Root
}
Write-Host 'Started Control Room + Sentinel, and Telegram when configured.'
