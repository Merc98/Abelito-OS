"""Tor client wrapper — enruta comandos de red a traves de torsocks."""
from __future__ import annotations

import shutil
import socket
import subprocess


def _tor_reachable(host: str = "127.0.0.1", port: int = 9050) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def run_via_tor(cmd: list[str], timeout: int = 120) -> dict:
    """Envuelve cmd con torsocks. Pre-checks: torsocks en PATH + Tor daemon activo."""
    if not shutil.which("torsocks"):
        return {"error": "torsocks not found in PATH", "hint": "apt install torsocks / brew install torsocks"}
    if not _tor_reachable():
        return {"error": "Tor SOCKS proxy not reachable at 127.0.0.1:9050", "hint": "systemctl start tor / brew services start tor"}
    try:
        proc = subprocess.run(["torsocks", *cmd], capture_output=True, text=True, timeout=timeout, check=False)
        return {"returncode": proc.returncode, "stdout": proc.stdout[:4000], "stderr": proc.stderr[:2000]}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as exc:
        return {"error": str(exc)}
