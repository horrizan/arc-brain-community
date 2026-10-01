from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "workflows"
OUT = ROOT / "runtime" / "workflows"
load_dotenv(ROOT / ".env")


def js_pick(role: str, pattern: str, include_all: bool = True) -> str:
    pat = json.dumps(pattern or ".*")
    # The fallback to the first installed model is intentional: a one-model install must work.
    return (
        "const names=($json.models||[]).map(m=>m.name);"
        f" const rx=new RegExp({pat},'i');"
        " const chosen=names.find(n=>rx.test(n))||names[0]||null;"
        f" return [{{json:{{{role}:chosen,all:names}}}}];"
    )


def js_roles(fast: str, main: str, reasoner: str, health: bool = False) -> str:
    fp, mp, rp = map(json.dumps, (fast or ".*", main or ".*", reasoner or ".*"))
    prefix = "const names=($json.models||[]).map(m=>m.name); const pick=(p)=>{const r=new RegExp(p,'i');return names.find(n=>r.test(n))||names[0]||null;};"
    body = f"fast:pick({fp}),main:pick({mp}),reasoner:pick({rp})"
    if health:
        return prefix + f" return [{{json:{{ollama_ok:names.length>0,models:names,{body},warning:names.length?null:'No Ollama models returned'}}}}];"
    return prefix + f" return [{{json:{{{body},all:names}}}}];"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--postgres-credential-id", required=True)
    ap.add_argument("--postgres-credential-name", default="Arc Brain Postgres")
    args = ap.parse_args()

    fast = os.getenv("ARC_MODEL_FAST_PATTERN", ".*")
    main_pat = os.getenv("ARC_MODEL_MAIN_PATTERN", ".*")
    reasoner = os.getenv("ARC_MODEL_REASONER_PATTERN", ".*")
    control_port = os.getenv("ARC_CONTROL_ROOM_PORT", "8787")
    bridge_token = os.getenv("ARC_CONTROL_ROOM_TOKEN", "").strip()

    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.json"):
        stale.unlink()

    count = 0
    for src in SRC.glob("*.json"):
        data = json.loads(src.read_text(encoding="utf-8"))
        # Bridge URLs are localhost-on-host from the n8n container. The installer can move the host port if 8787 is occupied.
        raw = json.dumps(data, ensure_ascii=False).replace("host.docker.internal:8787", f"host.docker.internal:{control_port}")
        data = json.loads(raw)
        for node in data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.postgres":
                node["credentials"] = {
                    "postgres": {"id": args.postgres_credential_id, "name": args.postgres_credential_name}
                }
            name = node.get("name")
            params = node.setdefault("parameters", {})
            if name == "Resolve Model Roles":
                params["jsCode"] = js_roles(fast, main_pat, reasoner, health=True)
            elif name == "Resolve Models":
                params["jsCode"] = js_roles(fast, main_pat, reasoner)
            elif name == "Resolve Main Model":
                params["jsCode"] = js_pick("main", main_pat)
            elif name == "Resolve Reasoner":
                params["jsCode"] = js_pick("reasoner", reasoner)

            # n8n runs in Docker while the memory/research bridge runs on Windows.
            # Inject the random bridge token only into generated runtime workflows (runtime/ is gitignored).
            if node.get("type") == "n8n-nodes-base.httpRequest" and f"host.docker.internal:{control_port}" in str(params.get("url", "")):
                params["sendHeaders"] = True
                hp = params.setdefault("headerParameters", {}).setdefault("parameters", [])
                hp = [h for h in hp if h.get("name", "").lower() != "x-arc-token"]
                if bridge_token:
                    hp.append({"name": "x-arc-token", "value": bridge_token})
                params["headerParameters"]["parameters"] = hp
        (OUT / src.name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        count += 1
    print(f"Rendered {count} workflow(s) into {OUT}")


if __name__ == "__main__":
    main()
