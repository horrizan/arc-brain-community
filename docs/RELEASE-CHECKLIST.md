# Release checklist

Before publishing a release:

- run `python scripts/validate_release.py`;
- run a clean install in a fresh Windows environment;
- run `CHECK-ARC-BRAIN.cmd` and `scripts/test_intake.ps1`;
- confirm `.env`, `config/projects.json`, `runtime/`, local inboxes and memories are absent from Git;
- confirm `ARC-05 Outreach Sender` is inactive and the send kill switch defaults false;
- scan screenshots for names, paths, emails, API keys, Telegram IDs and private project data;
- update `CHANGELOG.md` and `STATUS.md` with what was actually tested;
- generate a ZIP and SHA-256 checksum;
- attach both to the GitHub Release;
- publish a short build log containing problem, change, proof, failure and next milestone.
