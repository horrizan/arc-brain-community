from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import sqlite3
import time
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from arc_config import alias_map

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

INBOX = Path(os.getenv("ARC_INBOX", r"D:\ArcBrain\Inbox"))
WEBHOOK = os.getenv("ARC_INTAKE_URL", "http://127.0.0.1:5678/webhook/arc/intake")
STATE_DB = Path(os.getenv("ARC_SENTINEL_STATE", r"D:\ArcBrain\arc-sentinel.sqlite3"))
MAX_TEXT = int(os.getenv("ARC_MAX_INLINE_TEXT_BYTES", "524288"))
MAX_BINARY = int(os.getenv("ARC_MAX_INLINE_BINARY_MB", "8")) * 1024 * 1024

TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".sql", ".ps1", ".bat",
    ".sh", ".java", ".cs", ".cpp", ".c", ".h", ".go", ".rs", ".php", ".rb"
}
INLINE_BINARY_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def db():
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STATE_DB)
    con.execute("CREATE TABLE IF NOT EXISTS seen(sha256 TEXT PRIMARY KEY, path TEXT, sent_at REAL)")
    return con


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wait_stable(path: Path, rounds=3, delay=0.8):
    last = -1
    stable = 0
    for _ in range(20):
        if not path.exists() or not path.is_file():
            return False
        size = path.stat().st_size
        if size == last:
            stable += 1
            if stable >= rounds:
                return True
        else:
            stable = 0
            last = size
        time.sleep(delay)
    return True


PROJECT_FOLDERS = alias_map()


def route_for(path: Path):
    try:
        rel = path.relative_to(INBOX)
        parts = list(rel.parts[:-1])
    except Exception:
        return "unknown", None
    if not parts:
        return "unknown", None
    first = parts[0].strip().lower()
    project = PROJECT_FOLDERS.get(first)
    if project:
        category = parts[1].strip().lower() if len(parts) > 1 else "unknown"
        return category, project
    return first, None


def zip_manifest(path: Path):
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()[:500]
            return {"entries": names, "truncated": len(z.namelist()) > 500}
    except Exception as e:
        return {"error": str(e)}


def build_payload(path: Path):
    digest = sha256(path)
    size = path.stat().st_size
    ext = path.suffix.lower()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = {
        "event_type": "file_created",
        "source": "sentinel",
        "source_ref": str(path),
        "category": route_for(path)[0],
        "project_hint": route_for(path)[1],
        "filename": path.name,
        "extension": ext,
        "mime_type": mime,
        "size_bytes": size,
        "sha256": digest,
        "created_at_epoch": time.time(),
    }
    if ext in TEXT_EXTS and size <= MAX_TEXT:
        try:
            payload["text"] = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            payload["read_error"] = str(e)
    elif ext == ".zip":
        payload["zip_manifest"] = zip_manifest(path)
    elif ext in INLINE_BINARY_EXTS and size <= MAX_BINARY:
        payload["binary_base64"] = base64.b64encode(path.read_bytes()).decode("ascii")
    return payload


def send(path: Path):
    if not wait_stable(path):
        return
    digest = sha256(path)
    with db() as con:
        if con.execute("SELECT 1 FROM seen WHERE sha256=?", (digest,)).fetchone():
            return
    payload = build_payload(path)
    r = requests.post(WEBHOOK, json=payload, timeout=120)
    r.raise_for_status()
    with db() as con:
        con.execute("INSERT OR REPLACE INTO seen(sha256,path,sent_at) VALUES(?,?,?)", (digest, str(path), time.time()))
        con.commit()
    print(f"[sent] {path} -> {r.status_code}")


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            try:
                send(Path(event.src_path))
            except Exception as e:
                print(f"[error] {event.src_path}: {e}")

    def on_moved(self, event):
        if not event.is_directory:
            try:
                send(Path(event.dest_path))
            except Exception as e:
                print(f"[error] {event.dest_path}: {e}")


if __name__ == "__main__":
    INBOX.mkdir(parents=True, exist_ok=True)
    print(f"Watching {INBOX}")
    print(f"Posting to {WEBHOOK}")
    observer = Observer()
    observer.schedule(Handler(), str(INBOX), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
