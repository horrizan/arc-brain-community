from __future__ import annotations

import os
import subprocess
import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

APP = FastAPI(title="Arc Brain Control Room", version="1.0")
TOKEN = os.getenv("ARC_CONTROL_ROOM_TOKEN", "").strip()
CONTROL_HOST = os.getenv("ARC_CONTROL_ROOM_HOST", "127.0.0.1").strip()
REQUIRE_TOKEN = os.getenv("ARC_CONTROL_ROOM_REQUIRE_TOKEN", "true").lower() in {"1","true","yes","on"}
MEMPALACE = os.getenv("MEMPALACE_CLI", "mempalace")
MEMPALACE_TIMEOUT = int(os.getenv("MEMPALACE_SEARCH_TIMEOUT", "45"))
CODE_REVIEW_URL = os.getenv("ARC_CODE_REVIEW_URL", "http://127.0.0.1:5678/webhook/arc/code-review")


def conninfo() -> str:
    return (
        f"host={os.getenv('PGHOST','127.0.0.1')} "
        f"port={os.getenv('PGPORT','5432')} "
        f"dbname={os.getenv('PGDATABASE','arcbrain')} "
        f"user={os.getenv('PGUSER','arcbrain')} "
        f"password={os.environ['PGPASSWORD']}"
    )


def check_token(request: Request):
    # Community default is loopback-only and intentionally needs no token.
    # If an operator exposes the Control Room beyond loopback, REQUIRE_TOKEN should be enabled.
    if not REQUIRE_TOKEN:
        return
    if not TOKEN:
        raise HTTPException(status_code=503, detail="Control Room token protection is enabled but no token is configured")
    supplied = request.headers.get("x-arc-token") or request.query_params.get("token")
    if supplied != TOKEN:
        raise HTTPException(status_code=401, detail="Missing/invalid Arc token")


def rows(sql: str, params=()):
    with psycopg.connect(conninfo(), row_factory=dict_row) as con:
        with con.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


class Decision(BaseModel):
    decision: str
    notes: str | None = None
    actor: str = "control-room"


class OutreachApproval(BaseModel):
    actor: str = "control-room"


@APP.get("/health")
def health():
    try:
        rows("SELECT 1 AS ok")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@APP.get("/api/projects")
def projects(request: Request):
    check_token(request)
    return rows("SELECT project_key,display_name,priority_weight,lifecycle,objective,policy,metadata,updated_at FROM arc.projects WHERE lifecycle <> 'archived' ORDER BY priority_weight DESC")


@APP.get("/api/items")
def items(request: Request, status: str | None = None, limit: int = Query(100, ge=1, le=500)):
    check_token(request)
    if status:
        return rows("SELECT id,source,item_type,title,project_key,status,priority,proposal,metadata,created_at,updated_at FROM arc.items WHERE status=%s ORDER BY created_at DESC LIMIT %s", (status, limit))
    return rows("SELECT id,source,item_type,title,project_key,status,priority,proposal,metadata,created_at,updated_at FROM arc.items ORDER BY created_at DESC LIMIT %s", (limit,))


@APP.get("/api/runs")
def runs_api(request: Request, limit: int = Query(100, ge=1, le=500)):
    check_token(request)
    return rows("SELECT id,item_id,agent_key,model_role,model_name,stage,status,error,started_at,finished_at FROM arc.runs ORDER BY started_at DESC LIMIT %s", (limit,))


@APP.get("/api/approvals")
def approvals_api(request: Request, limit: int = Query(100, ge=1, le=500)):
    check_token(request)
    return rows("SELECT id,item_id,requested_action,status,requested_at,decided_at,decided_by,payload FROM arc.approvals ORDER BY requested_at DESC LIMIT %s", (limit,))


@APP.get("/api/outreach")
def outreach_api(request: Request, limit: int = Query(100, ge=1, le=500)):
    check_token(request)
    return rows("SELECT id,project_key,item_id,recipient_name,recipient_email,organization,channel,reason_to_contact,subject,draft_body,status,approval_required,approved_at,sent_at,created_at,updated_at FROM arc.outreach ORDER BY created_at DESC LIMIT %s", (limit,))


@APP.post("/api/items/{item_id}/decision")
def decide(item_id: str, body: Decision, request: Request):
    check_token(request)
    mapping = {
        "build": "approved_build",
        "research": "research_requested",
        "modify": "needs_modification",
        "park": "parked",
        "kill": "killed",
    }
    decision = body.decision.lower().strip()
    if decision not in mapping:
        raise HTTPException(400, f"decision must be one of {sorted(mapping)}")
    with psycopg.connect(conninfo(), row_factory=dict_row) as con:
        with con.cursor() as cur:
            cur.execute("UPDATE arc.items SET status=%s WHERE id=%s::uuid RETURNING id,title,status", (mapping[decision], item_id))
            item = cur.fetchone()
            if not item:
                raise HTTPException(404, "Arc item not found")
            cur.execute(
                """INSERT INTO arc.approvals(item_id,requested_action,status,decided_at,decided_by,payload)
                   VALUES (%s::uuid,%s,'decided',now(),%s,jsonb_build_object('notes',%s))""",
                (item_id, decision, body.actor, body.notes),
            )
            cur.execute(
                "INSERT INTO arc.events(item_id,event_type,actor,payload) VALUES (%s::uuid,'decision',%s,jsonb_build_object('decision',%s,'notes',%s))",
                (item_id, body.actor, decision, body.notes),
            )
        con.commit()
    return {"ok": True, "item": item}


@APP.post("/api/items/{item_id}/code-review")
def trigger_code_review(item_id: str, request: Request):
    check_token(request)
    try:
        r = requests.post(CODE_REVIEW_URL, json={"item_id": item_id}, timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(502, f"Code review workflow failed: {e}")


@APP.post("/api/outreach/{outreach_id}/approve")
def approve_outreach(outreach_id: str, body: OutreachApproval, request: Request):
    check_token(request)
    with psycopg.connect(conninfo(), row_factory=dict_row) as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE arc.outreach SET status='approved',approved_at=now(),approved_by=%s WHERE id=%s::uuid AND status IN ('draft','needs_approval') RETURNING id,project_key,recipient_email,subject,status",
                (body.actor, outreach_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Draft not found or not approvable")
        con.commit()
    return {"ok": True, "outreach": row}




def _public_http_url(url: str) -> bool:
    try:
        u = urlparse(url)
        if u.scheme not in {"http", "https"} or not u.hostname:
            return False
        for info in socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
        return True
    except Exception:
        return False


@APP.get("/api/research/fetch")
def research_fetch(request: Request, url: str = Query(..., min_length=8, max_length=3000)):
    check_token(request)
    if not _public_http_url(url):
        raise HTTPException(400, "Only public http/https URLs are allowed")
    try:
        current = url
        r = None
        for _ in range(6):
            if not _public_http_url(current):
                raise ValueError("Redirect target is not a public HTTP(S) URL")
            r = requests.get(current, timeout=25, headers={"User-Agent":"ArcBrainResearch/1.0 (+local research assistant)"}, allow_redirects=False)
            if r.status_code in {301,302,303,307,308} and r.headers.get("location"):
                from urllib.parse import urljoin
                current = urljoin(current, r.headers["location"])
                continue
            break
        if r is None:
            raise RuntimeError("No response")
        if r.status_code in {301,302,303,307,308}:
            raise RuntimeError("Too many redirects")
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "text" not in ctype and "html" not in ctype and "json" not in ctype and "xml" not in ctype:
            return {"ok":False,"url":url,"status":r.status_code,"content_type":ctype,"text":"","error":"Unsupported content type"}
        text = r.text
        if "html" in ctype.lower() or "<html" in text[:1000].lower():
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script","style","noscript","svg"]):
                tag.decompose()
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            clean = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        else:
            title = ""
            clean = text
        return {"ok":True,"url":str(r.url),"status":r.status_code,"content_type":ctype,"title":title,"text":clean[:90000],"truncated":len(clean)>90000}
    except Exception as e:
        return {"ok":False,"url":url,"text":"","error":str(e)}


@APP.get("/api/memory/search")
def memory_search(request: Request, q: str = Query(..., min_length=2, max_length=2000)):
    check_token(request)
    try:
        cp = subprocess.run([MEMPALACE, "search", q], capture_output=True, text=True, timeout=MEMPALACE_TIMEOUT, check=False)
        return {"ok": cp.returncode == 0, "query": q, "stdout": cp.stdout[-50000:], "stderr": cp.stderr[-8000:], "returncode": cp.returncode}
    except FileNotFoundError:
        return {"ok": False, "query": q, "stdout": "", "stderr": f"MemPalace CLI not found: {MEMPALACE}", "returncode": 127}
    except Exception as e:
        return {"ok": False, "query": q, "stdout": "", "stderr": str(e), "returncode": -1}


HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arc Brain Control Room</title>
<style>
:root{font-family:system-ui,Segoe UI,Roboto,sans-serif;color-scheme:dark;background:#111;color:#eee}body{margin:0;background:#111}.wrap{max-width:1300px;margin:auto;padding:18px}h1{margin:0 0 4px}.muted{color:#aaa}.bar{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.bar button,.actions button{background:#222;border:1px solid #444;color:#eee;border-radius:8px;padding:8px 12px}.bar button:hover,.actions button:hover{background:#333}.card{border:1px solid #333;border-radius:12px;padding:12px;margin:10px 0;background:#171717}.tag{display:inline-block;padding:2px 7px;border:1px solid #444;border-radius:999px;margin-right:5px;font-size:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}.proposal{white-space:pre-wrap;font-size:13px;max-height:260px;overflow:auto;background:#0d0d0d;padding:8px;border-radius:8px}.hidden{display:none}input{background:#191919;color:#eee;border:1px solid #444;border-radius:7px;padding:7px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center}.status{font-weight:700}.priority{font-variant-numeric:tabular-nums}</style></head>
<body><div class="wrap"><div class="top"><div><h1>Arc Brain Control Room</h1><div class="muted">configurable project priorities · humans approve external/high-impact actions</div></div><button onclick="refresh()">Refresh</button></div>
<div class="bar"><button onclick="show('items')">Inbox / Ideas</button><button onclick="show('projects')">Projects</button><button onclick="show('outreach')">Outreach</button><button onclick="show('runs')">Runs</button><button onclick="show('memory')">Memory Search</button></div>
<section id="items"></section><section id="projects" class="hidden"></section><section id="outreach" class="hidden"></section><section id="runs" class="hidden"></section><section id="memory" class="hidden"><div class="card"><input id="mq" style="width:70%" placeholder="Search MemPalace"><button onclick="mem()">Search</button><pre id="mr" class="proposal"></pre></div></section>
</div><script>
const token=new URLSearchParams(location.search).get('token')||''; const H=token?{'x-arc-token':token}:{};
async function api(u,o={}){o.headers={...(o.headers||{}),...H,'content-type':'application/json'}; const r=await fetch(u,o); if(!r.ok)throw new Error(await r.text()); return r.json()}
function show(id){for(const s of document.querySelectorAll('section'))s.classList.add('hidden');document.getElementById(id).classList.remove('hidden')}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
async function decision(id,d){await api(`/api/items/${id}/decision`,{method:'POST',body:JSON.stringify({decision:d})});await loadItems()}
async function codeReview(id){await api(`/api/items/${id}/code-review`,{method:'POST',body:'{}'});await loadItems()}
async function approveOutreach(id){await api(`/api/outreach/${id}/approve`,{method:'POST',body:JSON.stringify({})});await loadOutreach()}
async function loadItems(){const a=await api('/api/items?limit=100');document.getElementById('items').innerHTML=a.map(x=>`<div class="card"><div><span class="tag">${esc(x.project_key||'unassigned')}</span><span class="tag">${esc(x.item_type)}</span><span class="status">${esc(x.status)}</span></div><h3>${esc(x.title)}</h3><div class="muted">${esc(x.id)} · ${esc(x.created_at)}</div>${x.proposal?`<details><summary>Proposal</summary><pre class="proposal">${esc(JSON.stringify(x.proposal,null,2))}</pre></details>`:''}<div class="actions"><button onclick="decision('${x.id}','build')">BUILD</button><button onclick="decision('${x.id}','research')">RESEARCH</button><button onclick="decision('${x.id}','modify')">MODIFY</button><button onclick="decision('${x.id}','park')">PARK</button><button onclick="decision('${x.id}','kill')">KILL</button>${['code','app'].includes(x.item_type)?`<button onclick="codeReview('${x.id}')">SECURITY REVIEW</button>`:''}</div></div>`).join('')}
async function loadProjects(){const a=await api('/api/projects');document.getElementById('projects').innerHTML=`<div class="grid">${a.map(x=>`<div class="card"><div class="priority">Priority ${x.priority_weight}</div><h3>${esc(x.display_name)}</h3><div>${esc(x.objective)}</div><details><summary>Policy</summary><p>${esc(x.policy)}</p></details></div>`).join('')}</div>`}
async function loadOutreach(){const a=await api('/api/outreach?limit=100');document.getElementById('outreach').innerHTML=a.map(x=>`<div class="card"><span class="tag">${esc(x.project_key)}</span><span class="status">${esc(x.status)}</span><h3>${esc(x.organization||x.recipient_name||x.recipient_email||'Outreach')}</h3><div><b>${esc(x.subject||'')}</b></div><pre class="proposal">${esc(x.draft_body||'')}</pre>${['draft','needs_approval'].includes(x.status)?`<button onclick="approveOutreach('${x.id}')">Approve draft</button>`:''}</div>`).join('')}
async function loadRuns(){const a=await api('/api/runs?limit=100');document.getElementById('runs').innerHTML=a.map(x=>`<div class="card"><span class="tag">${esc(x.agent_key)}</span><span class="tag">${esc(x.model_name||x.model_role)}</span><b>${esc(x.status)}</b><div class="muted">${esc(x.stage)} · ${esc(x.started_at)}</div>${x.error?`<pre>${esc(x.error)}</pre>`:''}</div>`).join('')}
async function mem(){const q=document.getElementById('mq').value;const r=await api('/api/memory/search?q='+encodeURIComponent(q));document.getElementById('mr').textContent=r.stdout||r.stderr||JSON.stringify(r,null,2)}
async function refresh(){await Promise.all([loadItems(),loadProjects(),loadOutreach(),loadRuns()])} refresh();
</script></body></html>'''


@APP.get("/", response_class=HTMLResponse)
def root():
    return HTML


if __name__ == "__main__":
    import uvicorn
    host = CONTROL_HOST
    port = int(os.getenv("ARC_CONTROL_ROOM_PORT", "8787"))
    uvicorn.run(APP, host=host, port=port)
