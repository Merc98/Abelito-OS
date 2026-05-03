from __future__ import annotations
import subprocess
from pathlib import Path

def clone_repo(url: str, dest_root: str = 'data/repos') -> dict:
    Path(dest_root).mkdir(parents=True, exist_ok=True)
    name = url.rstrip('/').split('/')[-1].replace('.git','')
    dest = Path(dest_root) / name
    if dest.exists():
        return {"status": "exists", "path": str(dest)}
    proc = subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], capture_output=True, text=True, check=False)
    return {"status": "ok" if proc.returncode==0 else "error", "path": str(dest), "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
