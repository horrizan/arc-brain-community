# Project Portfolio Policy

Project priority is loaded from `config/projects.json` and the `arc.projects` table. Do not assume a fixed business order from this file.

Rules:

1. Protect higher-priority project delivery from lower-priority infrastructure work.
2. A small, high-leverage lower-priority action is acceptable when it does not displace critical work.
3. Project-specific policy supplied by the caller/database overrides generic assumptions.
4. New projects start as low priority until a human intentionally promotes them.
