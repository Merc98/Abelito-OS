"""File Manager Skill — FS operations."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

class FileManagerSkill:
    """Skill for managing files on the host system."""

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory."""
        try:
            p = Path(path).resolve()
            items = []
            for item in p.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            return {"path": str(p), "items": items}
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read text from a file."""
        try:
            p = Path(path).resolve()
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            return {"path": str(p), "content": content}
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write text to a file."""
        try:
            p = Path(path).resolve()
            # Ensure parent directories exist
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return {"path": str(p), "status": "success"}
        except Exception as e:
            return {"error": str(e)}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            p = Path(path).resolve()
            if p.is_file():
                p.unlink()
                return {"path": str(p), "status": "deleted"}
            return {"error": "Not a file"}
        except Exception as e:
            return {"error": str(e)}

def setup():
    return FileManagerSkill()
