"""Robin-smesh dark-web search wrapper con fallback cuando la herramienta no esta."""
from __future__ import annotations

import shutil
import subprocess


def search_darkweb(query: str) -> dict:
    """Busca en dark-web usando robin-smesh CLI.
    Requiere: robin-smesh en PATH y tor corriendo en localhost:9050.
    Si no esta disponible, retorna dict de error.
    """
    if not shutil.which("robin-smesh"):
        return {
            "error": "robin-smesh not found in PATH",
            "hint": "Install robin-smesh or verify it is in PATH",
        }
    try:
        proc = subprocess.run(
            ["robin-smesh", "search", query],
            capture_output=True, text=True, timeout=60, check=False,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout[:4000], "stderr": proc.stderr[:2000]}
    except subprocess.TimeoutExpired:
        return {"error": "robin-smesh timed out after 60s"}
    except Exception as exc:
        return {"error": str(exc)}
