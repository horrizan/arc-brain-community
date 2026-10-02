from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

required = [
    "README.md", ".env.example", "config/projects.example.json", "docker/docker-compose.yml",
    "install.ps1", "finish-setup.ps1", "doctor.ps1", "agents/agency-roster.md",
    "INSTALL-ARC-BRAIN.cmd", "CHECK-ARC-BRAIN.cmd", "docs/FIRST-5-MINUTES.md",
    "docs/RELEASE-CHECKLIST.md",
]
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f"missing required file: {rel}")

# Internal planning/process files must never be part of a distributable source tree.
forbidden_paths = {
    "docs/BUILD-IN-PUBLIC.md",
    "docs/PUBLIC-LAUNCH-PLAN.md",
}
for rel in sorted(forbidden_paths):
    if (ROOT / rel).exists():
        errors.append(f"internal-only file present in release tree: {rel}")

for p in ROOT.rglob("*.json"):
    if "runtime" in p.parts:
        continue
    try:
        json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        errors.append(f"invalid JSON {p.relative_to(ROOT)}: {exc}")

for p in (ROOT / "scripts").glob("*.py"):
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as exc:
        errors.append(f"Python compile failed {p.name}: {exc}")

# Windows PowerShell 5.1 can misread UTF-8-without-BOM smart punctuation.
# Keep executable PowerShell/CMD sources ASCII-only so parsing is deterministic.
for pattern in ("*.ps1", "*.cmd"):
    for p in ROOT.rglob(pattern):
        try:
            text = p.read_text(encoding="utf-8-sig")
        except Exception as exc:
            errors.append(f"cannot decode script {p.relative_to(ROOT)}: {exc}")
            continue
        bad = sorted({ch for ch in text if ord(ch) > 127})
        if bad:
            shown = " ".join(f"U+{ord(ch):04X}" for ch in bad[:8])
            errors.append(f"non-ASCII punctuation/text in executable script {p.relative_to(ROOT)}: {shown}")

workflow_count = 0
for p in (ROOT / "workflows").glob("*.json"):
    workflow_count += 1
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    if not d.get("id"):
        errors.append(f"workflow missing stable id: {p.name}")
    for node in d.get("nodes", []):
        if node.get("type") == "n8n-nodes-base.postgres" and node.get("credentials"):
            errors.append(f"source workflow embeds a credential reference: {p.name}/{node.get('name')}")
    if d.get("name") == "ARC-05 Outreach Sender" and d.get("active"):
        errors.append("outbound sender must not ship active")
if workflow_count < 7:
    errors.append(f"expected at least 7 workflows, found {workflow_count}")

secret_patterns = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
for p in ROOT.rglob("*"):
    if not p.is_file() or any(x in p.parts for x in (".git", ".venv", "runtime")):
        continue
    if p.name == "LICENSE":
        continue
    try:
        text = p.read_text(encoding="utf-8-sig")
    except Exception:
        continue
    for pat in secret_patterns:
        if pat.search(text):
            errors.append(f"possible embedded secret in {p.relative_to(ROOT)}")
            break

if errors:
    print("VALIDATION FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"Validation passed: {workflow_count} workflows, Python compiled, required files present, PowerShell/CMD sources are ASCII-safe, and internal planning files are absent.")
