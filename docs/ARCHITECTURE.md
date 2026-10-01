# Arc Brain Community Architecture

## Principle

Arc Brain separates **orchestration, runtime state, durable knowledge and artifacts** so an LLM is never the only place a decision exists.

```text
Input surfaces
Telegram / watched folders / webhooks
              ↓
            n8n
       orchestration only
              ↓
     Postgres runtime state
              ↓
       local Ollama roles
              ↓
 proposal / research / review
              ↓
        human approval gate
```

Optional durable memory adapters such as MemPalace sit beside Postgres. Git/disk remain artifact truth for code and files.

## Components

### Ollama

Runs one or more local models. Community Edition can use a single model for all roles. Model roles (`fast`, `main`, `reasoner`) are logical routing names rather than hard dependencies on specific model families.

### n8n

Owns workflow sequencing, webhooks and scheduled operations. It should not become unrestricted host-shell access or the permanent knowledge base.

### Postgres

Stores items, runs, approvals, projects, research tasks, outreach drafts and operational settings.

### Sentinel

A Windows-native file watcher. It hashes incoming files, classifies their folder/project hint, and posts normalized events to n8n. It does not execute dropped code.

### Control Room / bridge

A local FastAPI process provides a basic UI and bridges host-local capabilities such as optional memory search and bounded public-page retrieval.

### Telegram gateway

Optional long-polling client so a home install can receive Telegram commands without exposing an inbound Telegram webhook to the Internet.

## Agent lifecycle

```text
Scout → Critic → Architect → human decision
          ↘ Researcher when evidence is needed

BUILD approval → Builder → QA → human/ship gate   (execution runner is roadmap work)
```

Downloaded/community agent Markdown is library material until Agent Curator and a human approve a change to the active roster.

## Project priorities

Projects are configured in `config/projects.json` and synchronized into `arc.projects`. The engine is intentionally unaware of the maintainer's private business/project names.

## Trust boundaries

- public Internet → research fetcher: public HTTP(S) only; private/loopback destinations blocked;
- downloaded files/code → security review before any future execution runner;
- LLM → external actions: explicit human gates by default;
- Git repository → no secrets/private project data;
- n8n → host bridge: token-authenticated local calls.
