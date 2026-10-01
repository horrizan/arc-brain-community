# Arc Brain v1.0 Security Notes

## Trust boundaries

- **Watched folders:** untrusted input. Sentinel reads/hashes/posts; it never executes files.
- **Downloaded agent prompts:** untrusted reference material until Agent Curator review.
- **Downloaded code/apps:** data until Security Reviewer + human approval define a sandbox task.
- **n8n:** orchestration service; do not expose raw Arc webhooks to the public Internet.
- **Control Room:** local host service by default. If bound to LAN, restrict it with Windows Firewall and set `ARC_CONTROL_ROOM_TOKEN`.
- **MemPalace:** durable knowledge; never store tokens, passwords, private keys or raw credentials.
- **Outreach:** master send setting defaults false.

## File access

Do not give n8n broad Windows filesystem mounts simply for convenience. The host-side Sentinel provides a narrower, auditable intake boundary.

## URL research

The Control Room research fetcher accepts only HTTP(S), rejects private/loopback/link-local/reserved targets, and validates redirect destinations before following them. This reduces the chance that a research URL becomes an SSRF path to local infrastructure.

## Code execution

v1.0 deliberately does not expose arbitrary shell/PowerShell command execution from n8n. A future Builder runner should use allowlisted repositories, temporary Git worktrees/branches, explicit test commands, timeouts and captured diffs.

## Email

`ARC-05 Outreach Sender` will not send while `arc.settings.outreach_send_enabled` is false. Keep this as a master kill switch even after a mail credential exists.

## Secrets

- Keep `.env` out of Git.
- Do not paste secrets into agent prompts or MemPalace.
- Keep n8n's encryption key stable and backed up securely.
- Prefer OAuth for Gmail/Google Workspace rather than long-lived passwords.

## Audit

Run periodically:

```powershell
docker exec -it <your-n8n-container> n8n audit
```

Also inspect `arc.runs`, `arc.events`, `arc.approvals` and `arc.outreach` when debugging agent behavior.
