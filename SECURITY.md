# Security Policy

Arc Brain touches files, automation workflows, language models and potentially external communication. Treat every integration as a trust boundary.

## Defaults

- n8n, Postgres and the Control Room bind to localhost in the reference install.
- outbound email is disabled by both workflow state and an Arc database kill switch.
- downloaded code/apps may be inspected but are not automatically executed.
- secrets belong in `.env` or external credential stores, never prompts, agent Markdown, workflow source JSON or Git commits.
- public-page research blocks loopback/private/link-local/reserved network targets.
- new external outreach remains human-approved unless a narrow rule is explicitly pre-authorized.

## Reporting a vulnerability

Do not open a public issue containing a live token, password, exploit payload against a real target, customer data or other sensitive material. Use a private maintainer contact/security advisory once the repository has one configured.

## Before exposing Arc beyond localhost

Add authentication, TLS and network restrictions appropriate to the deployment. The alpha reference stack is designed for local use, not direct Internet exposure.

## Docker-to-host bridge

The Community Edition runs a small Windows Python bridge for memory and bounded URL retrieval. n8n runs inside Docker and reaches that host service through `host.docker.internal`. The bridge therefore requires a generated random token for all non-health API routes. The token lives in `.env` and is injected only into generated `runtime/workflows/` copies; neither location belongs in Git.

Do not port-forward the bridge or expose it directly to the public internet. If Windows Firewall asks about Python, only allow the network profiles you actually need for Docker Desktop/local use.
