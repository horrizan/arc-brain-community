# Public / Private Split

The easiest way to build Arc Brain in public without leaking the valuable layer is to publish **the engine, not your private operating data**.

## Public repository

Publish:

- installer and health checks;
- generic agents;
- workflow source JSON without credentials;
- database schema;
- generic project examples;
- architecture/security decisions;
- test fixtures containing fake data;
- release notes and known failures.

## Keep private

Never commit:

- `.env`;
- personal/business `config/projects.json`;
- prospect/customer/contact lists;
- outreach history;
- Telegram IDs/tokens;
- n8n credential exports;
- MemPalace vault/database;
- personal photos/documents;
- private code repositories;
- exact business strategy you do not want competitors to copy.

A good local pattern is:

```text
arc-brain-community/       # public Git repository
arc-brain-owner-config/    # optional private repository or offline folder
```

The private layer copies/overlays configuration into the public engine during local setup.
