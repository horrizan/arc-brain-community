# Troubleshooting

Start with:

```powershell
.\doctor.ps1
```

## Docker is installed but not running

Start Docker Desktop, wait until the engine reports ready, then rerun the installer.

## Ollama is installed but Arc cannot see a model

Run:

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

If no model appears, install one and rerun setup.

## n8n can load but workflows fail on Postgres

Rerun:

```powershell
.\finish-setup.ps1
```

The script creates/reuses the `Arc Brain Postgres` credential and renders workflow copies with that credential ID before import.

## Control Room returns 401 inside an n8n workflow

The source workflows send `x-arc-token` from the n8n container environment. Confirm `ARC_CONTROL_ROOM_TOKEN` exists in `.env`, then recreate the n8n container:

```powershell
docker compose --env-file .env -f docker\docker-compose.yml up -d --force-recreate n8n
.\update-workflows.ps1
```

## MemPalace search says the CLI is missing

MemPalace is optional in Community Edition. Core intake still works; memory search simply has no external memory source. Set `MEMPALACE_CLI` later if you install a compatible adapter.

## Telegram does nothing

Telegram is optional. If enabled, check `TELEGRAM_BOT_TOKEN` and `ALLOWED_TELEGRAM_USER_IDS` in `.env`, then restart Arc host helpers with `stop.ps1` followed by `start.ps1`.

## Resetting

Do not delete Docker volumes casually: they contain n8n and Arc database state. Back up first. The alpha intentionally does not provide a one-click destructive reset.
