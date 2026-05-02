from __future__ import annotations
import shutil
import subprocess
import tempfile
from pathlib import Path

class SandboxBackend:
    def run_tests_in_copy(self, repo_path: str) -> dict:
        src = Path(repo_path)
        if not src.exists():
            return {"status":"error", "detail":"repo not found"}
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td) / src.name
            shutil.copytree(src, td_path)
            proc = subprocess.run(["python", "-m", "pytest", "-q"], cwd=td_path, capture_output=True, text=True, check=False)
            return {"status":"ok", "returncode":proc.returncode, "stdout":proc.stdout[-4000:], "stderr":proc.stderr[-2000:]}
