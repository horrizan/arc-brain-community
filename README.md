# Arc Brain Community Edition

> **Public alpha — v0.1.0**  
> Local-first idea → research → proposal → approval automation using **n8n + Ollama + Postgres**, with optional Telegram and MemPalace.

Arc Brain is for people who have ideas, files, code, screenshots, research and outreach tasks scattered everywhere and want one local system to triage them into useful next actions.

You do **not** need to understand agents, Postgres, Docker networking or n8n internals to try the guided Windows install.

## What it does

```text
Telegram / watched folders / webhook
                  ↓
               Scout
                  ↓
               Critic
                  ↓
              Architect
                  ↓
          actionable proposal
                  ↓
     BUILD / RESEARCH / MODIFY
          / PARK / KILL
```

The loop is intentionally bounded. Arc Brain does not let agents endlessly research and rewrite their own plans.

Included roles:

- Scout — intake and routing
- Researcher — bounded evidence gathering
- Critic — challenges weak assumptions and unnecessary work
- Architect — creates an implementation contract
- Builder — implementation role (execution sandbox is intentionally not enabled in this alpha)
- QA — independent verification
- Operator — routine/pre-authorized work
- Outreach — personalized draft-only communication by default
- Librarian — durable-memory curation
- Security Reviewer — reviews code/apps before execution
- Agent Curator — audits downloaded/community agent prompts before activation

## Easiest install — Windows 11

### 1. Prerequisites

You need:

- Docker Desktop
- Python 3.11+
- Ollama
- at least one Ollama chat model

If you have no model, the installer can offer to pull `qwen3.5:9b`. A single model can power all roles; multiple-model routing is optional.

### 2. Run the installer

For the easiest path, double-click:

```text
INSTALL-ARC-BRAIN.cmd
```

Or run it from PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

The installer will:

1. check Docker, Python and Ollama;
2. let you select an installed model;
3. ask for your primary and secondary project names;
4. generate local secrets;
5. create the Python environment and watched folders;
6. start Postgres, Redis and n8n;
7. create the Arc database schema;
8. load the agent roster and project policies;
9. open n8n for its one-time owner setup.

On a brand-new n8n install, create the owner account and then create an API key under **Settings → n8n API**. Return to PowerShell and paste the key when prompted. The installer then creates the local Postgres credential, renders/imports the workflows, publishes the safe inbound workflows, runs an n8n security audit, and starts Arc's local helpers.

The API key is used for setup and is **not written into the repository**.

### 3. Verify it

```powershell
.\doctor.ps1
.\scripts\test_intake.ps1
```

Open:

- Arc Control Room: `http://127.0.0.1:8787` by default
- n8n: `http://127.0.0.1:5678` by default

If either port is already occupied, the installer selects another localhost port and opens/prints the actual address.

## What is intentionally OFF

Arc starts conservatively:

- outbound email automation is disabled;
- downloaded code is not executed;
- Builder has no unrestricted host-shell access;
- Docker database/n8n ports bind to localhost; the small Windows bridge listens for Docker-host traffic and requires a generated token on every non-health API call;
- Telegram is optional;
- MemPalace is optional;
- cloud LLMs are optional.

This is an automation system, not a permission bypass.

## Personal configuration stays private

Your project names and priorities live in:

```text
config/projects.json
```

Your secrets live in:

```text
.env
```

Both should be treated as local configuration. The public template is `config/projects.example.json` and `.env.example`.

For a serious personal setup, keep business/prospect/customer memory outside the public repository. See [docs/PUBLIC-PRIVATE-SPLIT.md](docs/PUBLIC-PRIVATE-SPLIT.md).

## Main folders

```text
agents/       active agent Markdown prompts
config/       project configuration templates
 db/          Arc operational database schema
 docker/      local Postgres/Redis/n8n stack
 docs/        newcomer docs and architecture
 examples/    safe examples
 scripts/     Sentinel, Telegram, Control Room, setup helpers
 workflows/   source n8n workflows (no credentials)
 runtime/     generated local files; ignored by Git
```

## Status

This package has static validation and packaging checks, but **v0.1.0 is still an alpha until it has been installed end-to-end on multiple machines**. That is intentional: the public build log should say what is proven, not pretend the first release is production-ready.

See [docs/FIRST-5-MINUTES.md](docs/FIRST-5-MINUTES.md), [STATUS.md](STATUS.md), [ROADMAP.md](ROADMAP.md), and [docs/RELEASE-CHECKLIST.md](docs/RELEASE-CHECKLIST.md).

## Security model

Human approval is the default for publishing, deploying, new external outreach, spending, destructive data changes and execution of untrusted code. See [SECURITY.md](SECURITY.md).

## License

Arc Brain Community Edition is released under the Apache License 2.0. See [LICENSE](LICENSE).
