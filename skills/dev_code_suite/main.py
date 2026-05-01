from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Any

class DevCodeSuite:
    def list_python_files(self, path: str = ".") -> dict[str, Any]:
        files = [str(p) for p in Path(path).rglob("*.py")][:500]
        return {"count": len(files), "files": files}

    def run_pytest_subset(self, target: str = "tests") -> dict[str, Any]:
        proc = subprocess.run(["python", "-m", "pytest", "-q", target], capture_output=True, text=True, check=False)
        return {"returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-1500:]}

    def execute_action(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "list_python_files":
            return self.list_python_files(params.get("path", "."))
        if action == "run_pytest_subset":
            return self.run_pytest_subset(params.get("target", "tests"))
        raise ValueError(f"unsupported action: {action}")

def setup() -> DevCodeSuite:
    return DevCodeSuite()
