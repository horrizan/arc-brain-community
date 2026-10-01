from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
LIB = Path(os.getenv("ARC_AGENT_LIBRARY_DIR", str(ROOT / "agent-library")))
OLLAMA = os.getenv("OLLAMA_HOST_URL", "http://127.0.0.1:11434").rstrip("/")
OUT = ROOT / "agent-reviews"


def discover_reasoner() -> str:
    explicit = os.getenv("ARC_MODEL_REASONER", "").strip()
    if explicit:
        return explicit
    pats = [x.strip() for x in os.getenv("ARC_MODEL_REASONER_PATTERN", "deepseek.*r1|deepseek").split("|") if x.strip()]
    names = [m.get("name", "") for m in requests.get(f"{OLLAMA}/api/tags", timeout=10).json().get("models", [])]
    for p in pats:
        rx = re.compile(p, re.I)
        for n in names:
            if rx.search(n):
                return n
    raise RuntimeError(f"No reasoner model matched {pats}; installed={names}")


def main():
    if not LIB.exists():
        raise SystemExit(f"Agent library folder not found: {LIB}")
    curator = (ROOT / "agents" / "00-agent-contract.md").read_text(encoding="utf-8") + "\n\n" + (ROOT / "agents" / "agent-curator.md").read_text(encoding="utf-8")
    roster = (ROOT / "agents" / "agency-roster.md").read_text(encoding="utf-8")
    model = discover_reasoner()
    OUT.mkdir(parents=True, exist_ok=True)
    files = [p for p in LIB.rglob("*.md") if p.is_file()]
    print(f"Auditing {len(files)} Markdown agents with {model}")
    summary = []
    for i, path in enumerate(files, 1):
        raw = path.read_text(encoding="utf-8", errors="replace")
        prompt = f"ACTIVE ROSTER:\n{roster}\n\nCANDIDATE FILE: {path.name}\n\n{raw[:60000]}"
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": curator},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            r = requests.post(f"{OLLAMA}/api/chat", json=payload, timeout=240)
            r.raise_for_status()
            content = r.json().get("message", {}).get("content", "{}")
            result = json.loads(content)
        except Exception as e:
            result = {"candidate_name": path.name, "disposition": "error", "reason": str(e)}
        result["source_path"] = str(path)
        (OUT / f"{path.stem}.review.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        summary.append(result)
        print(f"[{i}/{len(files)}] {path.name}: {result.get('disposition')}")
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reviews written to {OUT}")


if __name__ == "__main__":
    main()
