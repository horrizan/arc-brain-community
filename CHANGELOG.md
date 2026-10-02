# Changelog

## 0.1.0-alpha — 2026-09-30

Initial Community Edition packaging.

- generic project configuration instead of owner-specific business policies;
- guided Windows installer and resumable finish-setup step;
- one-model minimum setup;
- automatic n8n Postgres credential creation after the user supplies an n8n API key;
- stable workflow IDs for repeatable CLI imports;
- automatic safe-workflow publishing;
- `doctor.ps1` health checks;
- public/private configuration split;
- GitHub validation workflow and contributor docs;
- localhost-only Control Room default with optional token protection for deliberate non-loopback exposure;
- safe installer reruns preserve database/encryption secrets;
- automatic alternate localhost ports when common ports are already occupied;
- optional separate-model routing while retaining a one-model default;
- double-click installer/start/check/stop launchers for non-technical testers.
## 0.1.1-alpha - 2026-10-02
- Fixed Windows PowerShell 5.1 installer parsing on systems that interpret UTF-8-without-BOM as an ANSI code page.
- Hardened Python version detection and the doctor health report.
- Added release validation for PowerShell/CMD ASCII safety.
- Internal build-public and launch-planning documents are now forbidden from distributable source.

