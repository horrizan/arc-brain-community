from __future__ import annotations
import hashlib, shutil, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.0-alpha'
OUT=ROOT.parent / f'arc-brain-community-v{VERSION}.zip'
EXCLUDE_TOP={'.env','config/projects.json'}
EXCLUDE_PARTS={'.git','.venv','__pycache__','runtime','dist'}

def include(p: Path) -> bool:
    rel=p.relative_to(ROOT).as_posix()
    if rel in EXCLUDE_TOP: return False
    if any(part in EXCLUDE_PARTS for part in p.relative_to(ROOT).parts): return False
    if p.suffix in {'.pyc','.pyo'}: return False
    return True

with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and include(p):
            z.write(p, f'arc-brain-community-v{VERSION}/{p.relative_to(ROOT).as_posix()}')
h=hashlib.sha256(OUT.read_bytes()).hexdigest()
sha=OUT.with_suffix(OUT.suffix+'.sha256')
sha.write_text(f'{h}  {OUT.name}\n',encoding='utf-8')
print(OUT)
print(h)
