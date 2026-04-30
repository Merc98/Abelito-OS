"""Skills Loader — Dynamically discovers and loads installed skills."""
from __future__ import annotations

import importlib
import inspect
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger("abel.skills")

@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str
    author: str
    entry_point: str

class SkillRegistry:
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path(__file__).parent
        self._skills: Dict[str, Any] = {}
        self._metadata: Dict[str, SkillMetadata] = {}

    def discover(self) -> None:
        """Find all directories in the skills folder that contain a skill.json."""
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "skill.json").exists():
                self._load_meta(item)

    def _load_meta(self, skill_path: Path) -> None:
        try:
            with open(skill_path / "skill.json", "r") as f:
                data = json.load(f)
                meta = SkillMetadata(
                    name=data["name"],
                    description=data.get("description", ""),
                    version=data.get("version", "0.1.0"),
                    author=data.get("author", "Abel Core"),
                    entry_point=data["entry_point"]
                )
                self._metadata[meta.name] = meta
                logger.debug(f"Discovered skill: {meta.name} v{meta.version}")
        except Exception as e:
            logger.error(f"Failed to load metadata for {skill_path.name}: {e}")

    def load_skill(self, name: str) -> Any:
        """Dynamically load a skill by name."""
        if name not in self._metadata:
            raise KeyError(f"Skill '{name}' not found")
        
        if name in self._skills:
            return self._skills[name]

        meta = self._metadata[name]
        module_path = f"skills.{name}.{meta.entry_point.replace('.py', '')}"
        
        try:
            module = importlib.import_module(module_path)
            # We expect a function or class named the same as the skill or 'setup'
            skill_instance = getattr(module, "setup", None)
            if skill_instance and callable(skill_instance):
                instance = skill_instance()
                self._skills[name] = instance
                return instance
            
            self._skills[name] = module
            return module
        except Exception as e:
            logger.error(f"Error loading skill {name}: {e}")
            raise

    def list_available(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": m.name,
                "description": m.description,
                "version": m.version,
                "author": m.author,
                "loaded": m.name in self._skills
            }
            for m in self._metadata.values()
        ]

from dataclasses import dataclass

# Global registry
registry = SkillRegistry()
registry.discover()
