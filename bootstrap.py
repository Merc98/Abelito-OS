#!/usr/bin/env python3
from __future__ import annotations
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

REQUIRED_BINS = ["python", "git"]
OPTIONAL_BINS = ["nats-server", "ollama", "adb", "appium"]


def check_port(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False


def main() -> int:
    print("[BOOT] Abelito OS bootstrap")
    missing = [b for b in REQUIRED_BINS if shutil.which(b) is None]
    if missing:
        print(f"[ERR] Missing required binaries: {', '.join(missing)}")
        return 1

    for d in ["data", "logs", "data/repos", "data/private"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    print("[OK] Core dependencies OK")
    for b in OPTIONAL_BINS:
        print(("[OK]" if shutil.which(b) else "[WARN]"), f"optional: {b}")

    nats_up = check_port("127.0.0.1", int(os.getenv("NATS_PORT", "4222")))
    print(("[OK]" if nats_up else "[WARN]"), "NATS port 4222 reachable" if nats_up else "NATS not reachable; async pipeline limited")

    run_target = os.getenv("ABEL_RUN", "app")
    if run_target == "none":
        print("[INFO] Bootstrap checks complete (no server launch)")
        return 0

    app_ref = "app.abel_os.main:app" if run_target == "app" else "abel_core.main:app"
    cmd = [sys.executable, "-m", "uvicorn", app_ref, "--host", "0.0.0.0", "--port", os.getenv("PORT", "8000")]
    print("[RUN] Launch:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
