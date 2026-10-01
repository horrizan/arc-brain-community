from __future__ import annotations

import base64
import json
import os
import socket
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from arc_config import telegram_prefixes

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TG = f"https://api.telegram.org/bot{TOKEN}"
ARC_URL = os.getenv("REMOTE_ARC_TELEGRAM_URL") or os.getenv("ARC_TELEGRAM_URL", "http://127.0.0.1:5678/webhook/arc/telegram")
ALLOWED = {int(x.strip()) for x in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",") if x.strip()}
POLL_TIMEOUT = int(os.getenv("TELEGRAM_POLL_TIMEOUT", "45"))
MAX_BINARY = int(os.getenv("ARC_MAX_INLINE_BINARY_MB", "8")) * 1024 * 1024
WOL_MAC = os.getenv("ARC_WOL_MAC", "").strip()
WOL_BROADCAST = os.getenv("ARC_WOL_BROADCAST", "255.255.255.255")
WAKE_WAIT = int(os.getenv("ARC_WAKE_WAIT_SECONDS", "75"))


def wol(mac: str):
    mac = mac.replace(":", "").replace("-", "")
    if len(mac) != 12:
        raise ValueError("ARC_WOL_MAC must be 12 hex digits")
    packet = bytes.fromhex("FF" * 6 + mac * 16)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(packet, (WOL_BROADCAST, 9))
    s.close()


def post_arc(payload):
    try:
        r = requests.post(ARC_URL, json=payload, timeout=20)
        r.raise_for_status()
        return r
    except Exception as first:
        if not WOL_MAC:
            raise
        print(f"Arc unavailable ({first}); sending WoL")
        wol(WOL_MAC)
        deadline = time.time() + WAKE_WAIT
        last = first
        while time.time() < deadline:
            time.sleep(5)
            try:
                r = requests.post(ARC_URL, json=payload, timeout=20)
                r.raise_for_status()
                return r
            except Exception as e:
                last = e
        raise last


def tg(method, **data):
    r = requests.post(f"{TG}/{method}", data=data, timeout=60)
    r.raise_for_status()
    return r.json()["result"]


def get_file_b64(file_id: str):
    info = tg("getFile", file_id=file_id)
    url = f"https://api.telegram.org/file/bot{TOKEN}/{info['file_path']}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    if len(r.content) > MAX_BINARY:
        return None, len(r.content), info["file_path"]
    return base64.b64encode(r.content).decode("ascii"), len(r.content), info["file_path"]


def allowed_user(user_id):
    return not ALLOWED or user_id in ALLOWED


def project_hint_from_text(text: str):
    t=(text or "").strip()
    low=t.lower()
    prefixes=telegram_prefixes()
    for prefix,project in prefixes:
        if low.startswith(prefix):
            return project, t[len(prefix):].strip()
    return None, t


def normalize(update):
    if "callback_query" in update:
        q = update["callback_query"]
        u = q.get("from", {})
        return {
            "event_type": "callback",
            "update_id": update.get("update_id"),
            "user_id": u.get("id"),
            "username": u.get("username"),
            "chat_id": q.get("message", {}).get("chat", {}).get("id"),
            "callback_query_id": q.get("id"),
            "callback_data": q.get("data", ""),
            "message_id": q.get("message", {}).get("message_id"),
            "source": "telegram",
        }
    m = update.get("message") or update.get("edited_message")
    if not m:
        return None
    u = m.get("from", {})
    original_text = m.get("text") or m.get("caption") or ""
    project_hint, cleaned_text = project_hint_from_text(original_text)
    payload = {
        "event_type": "message",
        "update_id": update.get("update_id"),
        "user_id": u.get("id"),
        "username": u.get("username"),
        "chat_id": m.get("chat", {}).get("id"),
        "message_id": m.get("message_id"),
        "text": cleaned_text,
        "project_hint": project_hint,
        "source": "telegram",
    }
    file_id = None
    file_kind = None
    if m.get("photo"):
        file_id = m["photo"][-1]["file_id"]
        file_kind = "photo"
    elif m.get("document"):
        file_id = m["document"]["file_id"]
        file_kind = "document"
        payload["filename"] = m["document"].get("file_name")
        payload["mime_type"] = m["document"].get("mime_type")
    if file_id:
        try:
            b64, size, remote = get_file_b64(file_id)
            payload.update({"attachment_kind": file_kind, "attachment_size": size, "telegram_file_path": remote})
            if b64:
                payload["binary_base64"] = b64
            else:
                payload["attachment_omitted"] = True
        except Exception as e:
            payload["attachment_error"] = str(e)
    return payload



def render_proposal(response_json):
    try:
        outer = response_json or {}
        result = outer.get("result", outer)
        if isinstance(result, dict) and "result" in result and isinstance(result["result"], dict):
            result = result["result"]
        item_id = result.get("item_id") or result.get("id")
        proposal = result.get("proposal") or {}
        arch = proposal.get("architect") or {}
        critic = proposal.get("critic") or {}
        scout = proposal.get("scout") or {}
        title = arch.get("proposal_title") or scout.get("summary") or "Arc proposal"
        verdict = critic.get("verdict", "")
        validation = critic.get("cheapest_validation", "")
        complexity = arch.get("estimated_complexity", "")
        action = arch.get("recommended_action", "")
        mvp = arch.get("mvp") or []
        done = arch.get("definition_of_done") or []
        lines = [f"ARC: {title}"]
        if verdict: lines.append(f"Critic: {verdict}")
        if action: lines.append(f"Architect: {action}")
        if complexity: lines.append(f"Complexity: {complexity}")
        if validation: lines.append(f"Validation: {validation}")
        if mvp:
            lines.append("MVP: " + "; ".join(str(x) for x in mvp[:4]))
        if done:
            lines.append("Done when: " + "; ".join(str(x) for x in done[:3]))
        if item_id: lines.append(f"Item: {item_id}")
        return "\n".join(lines)[:3900], item_id
    except Exception as e:
        return f"Arc completed the intake, but proposal rendering failed: {e}", None


def send_proposal(chat_id, response_json):
    text, item_id = render_proposal(response_json)
    kwargs = {"chat_id": chat_id, "text": text}
    if item_id:
        keyboard = {"inline_keyboard": [
            [{"text":"BUILD","callback_data":f"arc:{item_id}:build"}, {"text":"RESEARCH","callback_data":f"arc:{item_id}:research"}],
            [{"text":"MODIFY","callback_data":f"arc:{item_id}:modify"}, {"text":"PARK","callback_data":f"arc:{item_id}:park"}, {"text":"KILL","callback_data":f"arc:{item_id}:kill"}]
        ]}
        kwargs["reply_markup"] = json.dumps(keyboard)
    tg("sendMessage", **kwargs)


def main():
    me = tg("getMe")
    print(f"Telegram gateway running as @{me.get('username')} -> {ARC_URL}")
    offset = None
    while True:
        try:
            params = {"timeout": POLL_TIMEOUT, "allowed_updates": json.dumps(["message", "edited_message", "callback_query"])}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(f"{TG}/getUpdates", params=params, timeout=POLL_TIMEOUT + 10)
            r.raise_for_status()
            for update in r.json().get("result", []):
                offset = update["update_id"] + 1
                p = normalize(update)
                if not p:
                    continue
                if not allowed_user(p.get("user_id")):
                    print(f"Rejected Telegram user {p.get('user_id')}")
                    continue
                try:
                    response = post_arc(p)
                    if p.get("event_type") == "callback" and p.get("callback_query_id"):
                        tg("answerCallbackQuery", callback_query_id=p["callback_query_id"], text="Arc received it.")
                    elif p.get("event_type") == "message" and p.get("chat_id"):
                        try:
                            send_proposal(p["chat_id"], response.json())
                        except Exception as render_error:
                            tg("sendMessage", chat_id=p["chat_id"], text=f"Arc processed the item but could not render the proposal: {render_error}")
                except Exception as e:
                    print(f"Failed posting update {update.get('update_id')}: {e}")
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(f"Telegram loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
