from __future__ import annotations
import subprocess
from typing import Any

def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.stdout

def list_devices() -> list[dict[str, Any]]:
    devices = []
    try:
        out = _run(["adb", "devices"])
        for line in out.splitlines()[1:]:
            if line.strip() and "\t" in line:
                did, status = line.split("\t", 1)
                devices.append({"platform": "android", "id": did.strip(), "status": status.strip()})
    except FileNotFoundError:
        pass
    try:
        out = _run(["idevice_id", "-l"])
        for line in out.splitlines():
            if line.strip():
                devices.append({"platform": "ios", "id": line.strip(), "status": "connected"})
    except FileNotFoundError:
        pass
    return devices
