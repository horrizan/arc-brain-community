$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (!(Test-Path .\.venv\Scripts\python.exe)) { throw 'Run the install steps first; .venv is missing.' }
& .\.venv\Scripts\python.exe .\scripts\control_room.py
