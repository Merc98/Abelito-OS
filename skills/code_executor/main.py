"""Code Executor Skill — Runs Python code snippets."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from typing import Any, Dict

class CodeExecutorSkill:
    """Skill to execute Python code snippets."""

    def run_python(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """Run python code and return stdout/stderr."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "timeout": timeout}
        except Exception as e:
            return {"error": str(e)}
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)

def setup():
    return CodeExecutorSkill()
