from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
from typing import Any

class SandboxRestructureSuite:
    def sandbox_python(self, code: str, timeout_sec: int = 5) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "snippet.py"
            p.write_text(code)
            proc = subprocess.run(["python", str(p)], capture_output=True, text=True, timeout=timeout_sec, check=False)
            return {"returncode": proc.returncode, "stdout": proc.stdout[:2000], "stderr": proc.stderr[:2000]}

    def format_file(self, path: str) -> dict[str, Any]:
        proc = subprocess.run(["python", "-m", "black", path], capture_output=True, text=True, check=False)
        return {"returncode": proc.returncode, "stdout": proc.stdout[:1500], "stderr": proc.stderr[:1500]}

    def execute_action(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "sandbox_python":
            return self.sandbox_python(params["code"], int(params.get("timeout_sec", 5)))
        if action == "format_file":
            return self.format_file(params["path"])
        raise ValueError(f"unsupported action: {action}")

def setup() -> SandboxRestructureSuite:
    return SandboxRestructureSuite()
