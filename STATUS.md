# Project Status

**Release:** v0.1.0-alpha  
**State:** public installation candidate

## Verified in packaging

- all n8n workflow JSON files parse;
- Python helpers compile;
- workflow node references are structurally checked;
- public source workflows contain no embedded n8n credentials;
- outbound email workflow starts inactive and database send flag defaults to false;
- public configuration contains generic example projects rather than owner business configuration.

## Still needs real-world proof

- first clean Windows installation by the maintainer;
- clean installation by someone who did not build Arc Brain;
- Docker Desktop differences across Windows machines;
- n8n credential/bootstrap behavior against the pinned release;
- long-running Sentinel/Telegram reliability;
- multi-machine/home-server deployment documentation.

A bug discovered during first installs is a normal alpha result. Please report reproducible failures rather than silently working around them.
