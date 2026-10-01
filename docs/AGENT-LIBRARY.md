# Downloaded Agent Markdown Library

The downloaded `.md` agent stack is useful raw material, but it should not all become executable roles.

## Why

Large agent packs commonly contain overlapping personas, contradictory instructions, stale tool assumptions, broad permissions and role definitions that add latency without adding capability.

ARC therefore separates:

```text
MemPalace/reference agent library
             ↓
      Agent Curator review
             ↓
merge useful patterns into existing role
             OR
activate a genuinely distinct role
```

## Physical-folder audit

If the original Markdown files are available on disk, set:

```text
ARC_AGENT_LIBRARY_DIR=D:\ArcBrain\AgentLibrary
```

then run:

```powershell
python .\scripts\audit_agent_library.py
```

Results are written to:

```text
agent-reviews\
```

No active prompt is changed automatically.

## MemPalace-only files

If the downloaded prompts only exist inside MemPalace, use Control Room memory search to retrieve candidates. The same Curator output contract applies. A later write adapter can automate promotion once the MemPalace ingest interface is confirmed.
