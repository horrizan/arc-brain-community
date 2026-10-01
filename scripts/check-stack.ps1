$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "== Docker =="
docker version --format '{{.Server.Version}}'
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n== Ollama =="
try {
  $tags = Invoke-RestMethod http://127.0.0.1:11434/api/tags
  $names = @($tags.models | ForEach-Object { $_.name })
  $names | ForEach-Object { Write-Host "  $_" }
} catch {
  Write-Error "Ollama API not reachable: $($_.Exception.Message)"
}

Write-Host "`n== n8n =="
try {
  $r = Invoke-WebRequest http://127.0.0.1:5678/healthz -UseBasicParsing
  Write-Host "n8n health: $($r.StatusCode) $($r.Content)"
} catch {
  Write-Warning "n8n /healthz not reachable at localhost:5678: $($_.Exception.Message)"
}

Write-Host "`n== Expected model roles =="
Write-Host "fast      : llama"
Write-Host "main      : qwen3.*14b | qwen3"
Write-Host "reasoner  : deepseek.*r1 | deepseek"

Write-Host "`n== Next =="
Write-Host "Run: .\.venv\Scripts\python.exe .\scripts\sync_agents.py"
Write-Host "Then import workflows from .\workflows in n8n."
