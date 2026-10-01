@echo off
cd /d "%~dp0"
echo Arc Brain Community Edition installer
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo.
  echo Setup stopped with an error. Read docs\TROUBLESHOOTING.md or run CHECK-ARC-BRAIN.cmd.
  pause
)
