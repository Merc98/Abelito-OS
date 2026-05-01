from __future__ import annotations
import subprocess

def run_via_tor(cmd: list[str]) -> dict:
    proc = subprocess.run(["torsocks", *cmd], capture_output=True, text=True, check=False)
    return {"returncode": proc.returncode, "stdout": proc.stdout[:4000], "stderr": proc.stderr[:2000]}
