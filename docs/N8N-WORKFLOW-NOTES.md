# n8n Workflow Notes

Source workflows live in `workflows/`. Generated install-time copies live in `runtime/workflows/` and contain the local n8n Postgres credential reference.

## Workflow set

- **ARC-00 Healthcheck** — manual Ollama/model-role check.
- **ARC-01 Core Intake Loop** — normalized item → Scout → Critic → Architect → stored proposal.
- **ARC-02 Telegram Intake** — Telegram gateway payloads and approval callbacks.
- **ARC-03 Research URLs** — bounded analysis of supplied public URLs.
- **ARC-04 Outreach Draft** — project-aware draft generation.
- **ARC-05 Outreach Sender** — scheduled sender; intentionally inactive by default and protected by a database kill switch.
- **ARC-06 Code-App Review** — Security Reviewer pass for code/app intake.

## Project routing

The Windows Telegram gateway maps prefixes from `config/projects.json`. The default public examples are:

```text
/p1 ...  -> primary_project
/p2 ...  -> secondary_project
/arc ... -> arc_brain
```

Sentinel similarly maps the first folder level using configured project display names/aliases.

## Credentials

Do not commit credentials into source workflow JSON. `finish-setup.ps1` creates/reuses an n8n Postgres credential and `scripts/render_workflows.py` adds only its n8n credential ID/name to generated copies under `runtime/`.

## Control Room authentication

n8n-to-bridge HTTP requests send the `x-arc-token` header from the `ARC_CONTROL_ROOM_TOKEN` environment variable passed into the n8n container.

## Repeatable imports

Source workflows use stable IDs so CLI re-imports target the same workflow records rather than intentionally creating a new set each time. n8n may deactivate imports depending on import mode/version; `finish-setup.ps1` republishes the safe core workflows through the public API.
