from __future__ import annotations
import subprocess

def search_darkweb(query: str) -> dict:
    proc = subprocess.run(["robin-smesh", "search", query], capture_output=True, text=True, check=False)
    return {"returncode": proc.returncode, "stdout": proc.stdout[:4000], "stderr": proc.stderr[:2000]}
