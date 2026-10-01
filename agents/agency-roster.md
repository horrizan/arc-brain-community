# ARC Active Agency Roster

This is the **active orchestration roster**, not the full agent library stored in MemPalace.

| Key | Role | Default model role | Called when |
|---|---|---:|---|
| scout | intake triage | fast | every new item |
| researcher | bounded evidence gathering | reasoner | a specific unknown blocks a decision |
| critic | challenge assumptions / stop waste | reasoner | ideas and plans before build |
| architect | implementation contract | main | idea survives critique |
| builder | approved implementation | main | BUILD approved |
| qa | independent verification | reasoner | Builder returns work |
| operator | routine operations | fast | recurring/pre-authorized tasks |
| outreach | external communication drafting | main | outreach/reply/follow-up work |
| librarian | durable-memory curation | fast | after meaningful decision/lesson |
| security-reviewer | trust/safety review | reasoner | code/apps/integrations before execution |
| agent-curator | audit downloaded/community agents | reasoner | reviewing the MemPalace/agent library |

## Handoff rules

- Scout does not build.
- Critic can end the loop with PARK/KILL.
- Architect creates the build contract but does not execute it.
- Builder cannot approve its own work.
- QA defects go back to Builder, maximum 3 repair cycles before human escalation.
- Security Reviewer is mandatory before running downloaded code/apps.
- Outreach remains draft-only until an approval/policy explicitly authorizes sending.
- Librarian writes only durable knowledge, never secrets.
- Agent Curator never activates downloaded prompts automatically; it recommends merge/activate/library/reject.
