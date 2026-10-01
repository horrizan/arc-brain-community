from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from arc_config import projects

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def conninfo() -> str:
    return (
        f"host={os.getenv('PGHOST','127.0.0.1')} "
        f"port={os.getenv('PGPORT','5432')} "
        f"dbname={os.getenv('PGDATABASE','arcbrain')} "
        f"user={os.getenv('PGUSER','arcbrain')} "
        f"password={os.environ['PGPASSWORD']}"
    )


SQL = """
INSERT INTO arc.projects(project_key,display_name,priority_weight,lifecycle,objective,policy,metadata)
VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
ON CONFLICT(project_key) DO UPDATE SET
 display_name=excluded.display_name,
 priority_weight=excluded.priority_weight,
 lifecycle=excluded.lifecycle,
 objective=excluded.objective,
 policy=excluded.policy,
 metadata=excluded.metadata,
 updated_at=now()
"""


def main() -> None:
    ps = projects()
    configured_keys = [str(p["project_key"]) for p in ps]
    with psycopg.connect(conninfo()) as con:
        with con.cursor() as cur:
            # Preserve history instead of deleting projects removed from config.
            # Config-managed rows that disappear are archived so overlays can safely replace the example profile.
            cur.execute(
                "UPDATE arc.projects SET lifecycle='archived', updated_at=now() WHERE metadata->>'managed_by'='config' AND NOT (project_key = ANY(%s))",
                (configured_keys,),
            )
            for p in ps:
                metadata = dict(p.get("metadata", {}))
                metadata["managed_by"] = "config"
                cur.execute(SQL, (
                    p["project_key"], p["display_name"], int(p.get("priority_weight", 0)),
                    p.get("lifecycle", "active"), p.get("objective", ""), p.get("policy", ""),
                    json.dumps(metadata),
                ))
        con.commit()
    print(f"Synced {len(ps)} project(s) from config/projects.json")


if __name__ == "__main__":
    main()
