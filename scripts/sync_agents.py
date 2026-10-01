from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
import psycopg

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_agent(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
    key = meta.get("agent_key", path.stem)
    display = meta.get("display_name", key.replace("-", " ").title())
    version = meta.get("version", "1.0.0")
    role = meta.get("model_role", "main")
    return key, display, version, role, text, meta


def main():
    conninfo = (
        f"host={os.getenv('PGHOST','127.0.0.1')} "
        f"port={os.getenv('PGPORT','5432')} "
        f"dbname={os.getenv('PGDATABASE','arcbrain')} "
        f"user={os.getenv('PGUSER','arcbrain')} "
        f"password={os.environ['PGPASSWORD']}"
    )
    agents_dir = ROOT / "agents"
    contract = (agents_dir / "00-agent-contract.md").read_text(encoding="utf-8")
    paths = [p for p in agents_dir.glob("*.md") if p.name not in {"agency-roster.md", "00-agent-contract.md"}]
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            count = 0
            for p in sorted(paths):
                key, display, version, role, prompt, meta = parse_agent(p)
                prompt = contract + "\n\n---\n\n" + prompt
                cur.execute(
                    """
                    INSERT INTO arc.agents(agent_key, display_name, version, model_role, prompt, enabled, metadata, updated_at)
                    VALUES (%s,%s,%s,%s,%s,true,%s::jsonb,now())
                    ON CONFLICT(agent_key) DO UPDATE SET
                      display_name=excluded.display_name,
                      version=excluded.version,
                      model_role=excluded.model_role,
                      prompt=excluded.prompt,
                      metadata=excluded.metadata,
                      enabled=true,
                      updated_at=now();
                    """,
                    (key, display, version, role, prompt, json.dumps(meta)),
                )
                count += 1
        conn.commit()
    print(f"Synced {count} ARC agents into arc.agents")


if __name__ == "__main__":
    main()
