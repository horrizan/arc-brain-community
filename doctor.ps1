$ErrorActionPreference='Continue'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
. "$Root\scripts\pslib.ps1"
$fail=0
function Check($name,[scriptblock]$test) {
  try { & $test; Write-Host "[OK]   $name" -ForegroundColor Green }
  catch { Write-Host "[FAIL] $name — $($_.Exception.Message)" -ForegroundColor Red; $script:fail++ }
}
$envPath="$Root\.env"
$n8nPort=Get-DotEnvValue $envPath 'N8N_PORT'; if(!$n8nPort){$n8nPort='5678'}
$controlPort=Get-DotEnvValue $envPath 'ARC_CONTROL_ROOM_PORT'; if(!$controlPort){$controlPort='8787'}
Check 'Docker engine' { docker info | Out-Null; if($LASTEXITCODE -ne 0){throw 'docker info failed'} }
Check 'Arc containers' {
  $services=@(docker compose --env-file $envPath -f "$Root\docker\docker-compose.yml" ps --services --filter status=running)
  foreach($n in @('postgres','redis','n8n')){if($services -notcontains $n){throw "$n service is not running"}}
}
Check 'Ollama API' { $r=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5; if(@($r.models).Count -lt 1){throw 'no model installed'} }
Check 'n8n health' { $r=Invoke-WebRequest "http://127.0.0.1:$n8nPort/healthz" -UseBasicParsing -TimeoutSec 5; if($r.StatusCode -ne 200){throw "HTTP $($r.StatusCode)"} }
Check 'Control Room' { $r=Invoke-RestMethod "http://127.0.0.1:$controlPort/health" -TimeoutSec 5; if(!$r.ok){throw ($r.error)} }
Check 'Project config' { Get-Content "$Root\config\projects.json" -Raw | ConvertFrom-Json | Out-Null }
Check 'Rendered workflows' { if(@(Get-ChildItem "$Root\runtime\workflows\*.json" -ErrorAction SilentlyContinue).Count -lt 7){throw 'run finish-setup.ps1'} }
Check 'Arc database' {
  $db=Get-DotEnvValue $envPath 'POSTGRES_DB'; $u=Get-DotEnvValue $envPath 'POSTGRES_USER'
  docker compose --env-file $envPath -f "$Root\docker\docker-compose.yml" exec -T postgres psql -U $u -d $db -Atc 'select count(*) from arc.agents;' | Out-Null
  if($LASTEXITCODE -ne 0){throw 'database query failed'}
}
if($fail -eq 0){Write-Host "`nAll core checks passed." -ForegroundColor Green; exit 0}
Write-Host "`n$fail check(s) failed. See docs/TROUBLESHOOTING.md." -ForegroundColor Yellow
exit 1
