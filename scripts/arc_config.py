from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_FILE = ROOT / "config" / "projects.json"


def load_project_config() -> dict:
    if not PROJECTS_FILE.exists():
        raise FileNotFoundError(f"Missing {PROJECTS_FILE}. Run install.ps1 or copy config/projects.example.json.")
    data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError("config/projects.json must contain a non-empty 'projects' array")
    return data


def projects() -> list[dict]:
    return load_project_config()["projects"]


def alias_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in projects():
        key = str(p["project_key"])
        out[key.lower()] = key
        out[str(p.get("display_name", key)).strip().lower()] = key
        if p.get("folder_name"):
            out[str(p.get("folder_name")).strip().lower()] = key
        for alias in p.get("aliases", []):
            out[str(alias).strip().lower()] = key
    return out


def telegram_prefixes() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for p in projects():
        key = str(p["project_key"])
        for prefix in p.get("telegram_prefixes", []):
            if str(prefix).strip():
                out.append((str(prefix).lower(), key))
    return sorted(out, key=lambda pair: len(pair[0]), reverse=True)
