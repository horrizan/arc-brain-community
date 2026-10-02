function Get-DotEnvValue {
  param([string]$Path,[string]$Name)
  if (!(Test-Path $Path)) { return $null }
  $line = Get-Content $Path | Where-Object { $_ -match ('^' + [regex]::Escape($Name) + '=') } | Select-Object -First 1
  if (!$line) { return $null }
  return $line.Substring($Name.Length + 1)
}

function Set-DotEnvValue {
  param([string]$Path,[string]$Name,[string]$Value)
  $lines = @()
  if (Test-Path $Path) { $lines = @(Get-Content $Path) }
  $prefix = "$Name="
  $found = $false
  $new = foreach ($line in $lines) {
    if ($line.StartsWith($prefix)) { $found = $true; "$prefix$Value" } else { $line }
  }
  if (!$found) { $new += "$prefix$Value" }
  Set-Content -Path $Path -Value $new -Encoding utf8
}

function New-ArcSecret {
  param([int]$Bytes = 48)
  $b = New-Object byte[] $Bytes
  [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
  return ([Convert]::ToBase64String($b)).Replace('+','A').Replace('/','B').TrimEnd('=')
}

function Convert-SecureToPlain {
  param([Security.SecureString]$Secure)
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Test-CommandExists {
  param([string]$Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-ArcCompose {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  $root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
  & docker compose --env-file (Join-Path $root '.env') -f (Join-Path $root 'docker\docker-compose.yml') @Args
  if ($LASTEXITCODE -ne 0) { throw "docker compose failed with exit code $LASTEXITCODE" }
}

function Test-LocalPortAvailable {
  param([int]$Port)
  $listener = $null
  try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    $listener.Start()
    return $true
  } catch { return $false }
  finally { if ($listener) { try { $listener.Stop() } catch {} } }
}

function Find-AvailableLocalPort {
  param([int[]]$Candidates)
  foreach ($port in $Candidates) { if (Test-LocalPortAvailable $port) { return $port } }
  throw "None of these localhost ports are available: $($Candidates -join ', ')"
}
