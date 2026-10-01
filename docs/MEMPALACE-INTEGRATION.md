# MemPalace Integration Boundary — v1.0

MemPalace remains the durable knowledge layer; Postgres remains operational state.

## v1 read path

The Windows Control Room exposes:

```text
GET /api/memory/search?q=<query>
```

Internally it executes the confirmed command shape:

```powershell
mempalace search "<query>"
```

ARC-01 treats this as **best effort**. If MemPalace is unavailable, the item still progresses and the failure is visible rather than silently fabricating memory.

## What belongs in Postgres

- queue/item state;
- proposals;
- agent runs;
- approvals;
- outreach state;
- research-task state;
- active runtime copies of canonical agent prompts.

## What belongs in MemPalace

- durable project decisions;
- reusable research;
- lessons learned;
- user/brand identity guidance;
- canonical project context;
- relationships in the knowledge graph;
- downloaded/reference agent library.

## Why v1 does not automate memory writes yet

The Arc context establishes the MCP server and `mempalace search`, but does not preserve the exact current write/ingest CLI/Python signature. Guessing the write call creates a real risk of silently writing knowledge to the wrong Wing/Hall/Room or corrupting metadata.

The remaining integration question is therefore narrow:

```powershell
mempalace --help
mempalace search --help
# and the current write/ingest command help
```

Once that signature is known, the Librarian can be wired to a single stable adapter without changing the n8n workflows or agent prompts.
