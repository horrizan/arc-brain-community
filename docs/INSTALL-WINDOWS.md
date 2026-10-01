# Windows 11 Installation — detailed

For most users, use [QUICKSTART-WINDOWS.md](QUICKSTART-WINDOWS.md) and run `install.ps1`.

This page explains what the installer is doing so failures are diagnosable.

## Prerequisites

- Windows 11
- Docker Desktop with Docker Compose
- Python 3.11+
- Ollama
- one local Ollama chat model

The alpha installer may offer to request missing prerequisites through `winget`, but Docker Desktop can require its own first-run setup. If prerequisites were just installed, start Docker Desktop and Ollama and rerun `install.ps1`.

## Files created

The repository itself contains source/configuration templates. Machine-local state is created in:

```text
.env
config/projects.json
runtime/
<your chosen Arc data directory>/Inbox/
<your chosen Arc data directory>/arc-sentinel.sqlite3
```

These are excluded from Git where appropriate.

## Docker stack

The reference stack contains:

- `postgres` (PostgreSQL)
- `redis`
- `n8n`

They run under the Compose project `arc-brain-community`; fixed container names are deliberately avoided so Arc can coexist with other Docker stacks.

Start manually if needed:

```powershell
docker compose --env-file .env -f .\docker\docker-compose.yml up -d
```

The Docker-published n8n/Postgres ports bind to `127.0.0.1`. The separate Windows host bridge listens on its configured port so Docker Desktop can reach it through `host.docker.internal`; its non-health API routes require a generated random token. Do not port-forward the bridge to the internet.

## Database

Apply/reapply the idempotent Arc migrations:

```powershell
.\scripts\apply_db.ps1
```

Then synchronize the active Markdown agents and configured projects:

```powershell
.\.venv\Scripts\python.exe .\scripts\sync_agents.py
.\.venv\Scripts\python.exe .\scripts\sync_projects.py
```

## n8n first-run bootstrap

A new self-hosted n8n instance requires an owner account. After creating it, create an API key under **Settings → n8n API**.

Run:

```powershell
.\finish-setup.ps1
```

The script uses that key to create/reuse the local Postgres credential. It then renders workflow JSON with the credential reference, imports the workflows through the n8n CLI, and publishes the safe inbound workflows. The outbound sender stays off.

The key is not saved into the repository or `.env` by the setup script.

## Model routing

The guided installer defaults to a single installed model for all three logical roles. If multiple models are installed, advanced setup can assign separate fast/main/reasoning models.

You can change the generated regexes in `.env` later:

```text
ARC_MODEL_FAST_PATTERN=
ARC_MODEL_MAIN_PATTERN=
ARC_MODEL_REASONER_PATTERN=
```

After changing model patterns, run `./update-workflows.ps1` so the generated workflow copies are refreshed and imported. Each resolver falls back to the first installed Ollama model if a preferred pattern is unavailable.

## Start / stop

```powershell
.\start.ps1
.\stop.ps1
```

Use `-StopDocker` if you also want `stop.ps1` to stop the Docker services.

## Telegram

Telegram is optional. Add a bot token and allowed user IDs to `.env`, then restart host helpers.

Project prefixes are read from `config/projects.json`; the default examples use `/p1`, `/p2`, and `/arc`.

## Memory

MemPalace is optional in Community Edition. If `mempalace` is available on PATH, the Control Room exposes search to the workflows. Otherwise the bridge returns a non-fatal "CLI not found" result and the core loop continues without external durable-memory retrieval.

## Outreach

Draft generation is available, but sending is disabled until you deliberately configure a mail credential and enable the separate database kill switch. Do not turn this on during first installation.

## Validation

```powershell
.\doctor.ps1
.\scripts\test_intake.ps1
python .\scripts\validate_release.py
```
