"""Self-Patch System — Allows ABEL to modify and fix its own source code."""
from __future__ import annotations

import difflib
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("abel.patcher")

class CodePatcher:
    """Engine for applying diff-based patches to the codebase."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parents[1]

    def secure_update(self, branch: str = "main", remote: str = "origin") -> Dict[str, Any]:
        """
        Pulls latest code from repository ONLY if the commits are cryptographically signed 
        and verified by the local Git keyring. Requires `commit.gpgsign = true` in the repo.
        """
        try:
            logger.info("Attempting secure self-update...")
            # Fetch latest
            subprocess.run(["git", "fetch", remote], cwd=self.root_dir, check=True, capture_output=True)
            
            # Verify the signature of the head we are about to pull.
            # If the commit is not signed or the key isn't trusted, this throws an error.
            verify_cmd = ["git", "verify-commit", f"{remote}/{branch}"]
            result_verify = subprocess.run(verify_cmd, cwd=self.root_dir, capture_output=True, text=True)
            
            if result_verify.returncode != 0:
                logger.error("[SECURITY_HINT] Update rejected: Target commit has no valid cryptographic signature.")
                return {"error": "Signature verification failed", "detail": result_verify.stderr}

            # Fast-forward to the verified signed commit
            merge_cmd = ["git", "merge", "--ff-only", f"{remote}/{branch}"]
            result_merge = subprocess.run(merge_cmd, cwd=self.root_dir, capture_output=True, text=True)

            if result_merge.returncode == 0:
                logger.info(f"System securely updated to latest verified commit on {branch}.")
                return {"status": "success", "stdout": result_merge.stdout}
            else:
                return {"error": "Fast-forward merge failed", "detail": result_merge.stderr}

        except subprocess.CalledProcessError as e:
            return {"error": "Secure update command execution failed", "detail": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def apply_patch(self, file_path: str, diff_text: str) -> Dict[str, Any]:
        """Apply a unified diff to a file."""
        abs_path = (self.root_dir / file_path).resolve()
        if not abs_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                original_lines = f.readlines()

            # Apply patch (simple implementation for now)
            # In a real scenario, we'd use 'patch' utility or a specialized library
            # Here we'll implement a basic line-by-line replacement if the diff is small
            # or use 'git apply' if it's a git repo.
            
            # For robustness, we'll try 'patch' utility if available on Windows (via git-bash)
            # otherwise we'll do a manual merge.
            
            temp_diff = Path(tempfile.gettempdir()) / f"patch_{uuid.uuid4()}.diff"
            with open(temp_diff, "w", encoding="utf-8") as f:
                f.write(diff_text)
            
            cmd = ["git", "apply", "--whitespace=fix", str(temp_diff)]
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            
            os.remove(temp_diff)
            
            if result.returncode == 0:
                logger.info(f"Successfully patched {file_path}")
                return {"status": "success", "file": file_path}
            else:
                return {"error": "Patch application failed", "detail": result.stderr}

        except Exception as e:
            logger.error(f"Error patching {file_path}: {e}")
            return {"error": str(e)}

    def run_validation(self) -> Dict[str, Any]:
        """Run the test suite to ensure the patch didn't break anything."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests", "-v"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"error": f"Validation failed: {e}"}

import tempfile
import uuid

def setup():
    return CodePatcher()
