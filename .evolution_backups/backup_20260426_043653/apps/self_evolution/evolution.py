"""Self-Evolution: System self-modification and evolution engine."""
from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


@dataclass
class EvolutionPlan:
    """Plan for system evolution."""
    goal: str
    required_changes: list[str] = field(default_factory=list)
    new_files: list[dict[str, Any]] = field(default_factory=list)
    modified_files: list[dict[str, Any]] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    dependencies_to_add: list[str] = field(default_factory=list)
    estimated_impact: str = ""
    rollback_plan: str = ""


@dataclass
class EvolutionResult:
    """Result of evolution execution."""
    success: bool
    changes_applied: int
    errors: list[str] = field(default_factory=list)
    backup_path: str | None = None
    timestamp: str = ""


class SelfEvolutionEngine:
    """Engine for self-modification and evolution of Abelito OS."""

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = Path(base_path)
        self.backup_dir = self.base_path / ".evolution_backups"
        self.evolution_history: list[EvolutionResult] = []

    def create_backup(self, description: str = "") -> str:
        """Create a backup of the current state."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Copy critical directories
        for dir_name in ["apps", "core", "shared"]:
            src = self.base_path / dir_name
            if src.exists():
                dst = backup_path / dir_name
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", ".git"
                ))

        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "description": description,
            "files_count": sum(1 for _ in backup_path.rglob("*") if _.is_file())
        }

        with open(backup_path / "metadata.json", "w") as f:
            import json
            json.dump(metadata, f, indent=2)

        logger.info(f"Backup created: {backup_path}")
        return str(backup_path)

    def rollback(self, backup_path: str) -> bool:
        """Rollback to a previous state."""
        backup = Path(backup_path)
        if not backup.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            # Restore directories
            for dir_name in ["apps", "core", "shared"]:
                src = backup / dir_name
                dst = self.base_path / dir_name
                if src.exists():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

            logger.info(f"Rolled back to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def evolve_from_chat(self, instruction: str) -> EvolutionResult:
        """Evolve system based on chat instruction."""
        logger.info(f"Evolving from instruction: {instruction[:100]}...")

        # Create backup first
        backup_path = self.create_backup(f"Before evolution: {instruction[:50]}")

        result = EvolutionResult(
            success=False,
            changes_applied=0,
            backup_path=backup_path,
            timestamp=datetime.now().isoformat()
        )

        try:
            # Parse instruction and determine action
            plan = await self._parse_instruction(instruction)

            # Execute plan
            changes = 0

            # Add new files
            for file_info in plan.new_files:
                if self._create_file(file_info):
                    changes += 1

            # Modify existing files
            for mod_info in plan.modified_files:
                if self._modify_file(mod_info):
                    changes += 1

            # Delete files
            for file_path in plan.deleted_files:
                if self._delete_file(file_path):
                    changes += 1

            # Add dependencies
            if plan.dependencies_to_add:
                if self._add_dependencies(plan.dependencies_to_add):
                    changes += 1

            result.changes_applied = changes
            result.success = changes > 0

            if result.success:
                logger.info(f"Evolution complete: {changes} changes applied")
            else:
                logger.warning("No changes applied during evolution")

        except Exception as e:
            error_msg = f"Evolution failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            # Auto-rollback on failure
            if backup_path:
                logger.info("Auto-rolling back due to failure")
                self.rollback(backup_path)

        self.evolution_history.append(result)
        return result

    async def _parse_instruction(self, instruction: str) -> EvolutionPlan:
        """Parse natural language instruction into evolution plan."""
        # In production, this would use AI to parse the instruction
        # For now, simple pattern matching

        plan = EvolutionPlan(goal=instruction)

        instruction_lower = instruction.lower()

        # Detect file creation
        if "crear" in instruction_lower or "crea" in instruction_lower or "add" in instruction_lower:
            if "archivo" in instruction_lower or "file" in instruction_lower:
                # Extract filename and content
                plan.new_files.append({
                    "path": "apps/new_feature/main.py",
                    "content": "# New feature auto-generated\nprint('Hello from new feature')\n"
                })

        # Detect module addition
        if "modulo" in instruction_lower or "module" in instruction_lower:
            plan.new_files.append({
                "path": "apps/auto_module/__init__.py",
                "content": ""
            })
            plan.new_files.append({
                "path": "apps/auto_module/processor.py",
                "content": "# Auto-generated module\nasync def process(data):\n    return data\n"
            })

        # Detect dependency addition
        if "instalar" in instruction_lower or "install" in instruction_lower or "dependency" in instruction_lower:
            if "numpy" in instruction_lower:
                plan.dependencies_to_add.append("numpy")
            if "pandas" in instruction_lower:
                plan.dependencies_to_add.append("pandas")

        # Detect feature enhancement
        if "mejorar" in instruction_lower or "improve" in instruction_lower or "enhance" in instruction_lower:
            plan.estimated_impact = "Medium"
            plan.required_changes.append("Enhance existing functionality")

        plan.rollback_plan = f"Restore from backup created before: {instruction[:50]}"

        return plan

    def _create_file(self, file_info: dict[str, Any]) -> bool:
        """Create a new file."""
        try:
            path = self.base_path / file_info["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(file_info.get("content", ""))
            logger.info(f"Created file: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return False

    def _modify_file(self, mod_info: dict[str, Any]) -> bool:
        """Modify an existing file."""
        try:
            path = self.base_path / mod_info["path"]
            if not path.exists():
                logger.warning(f"File to modify not found: {path}")
                return False

            content = path.read_text()

            # Apply modifications
            if "search" in mod_info and "replace" in mod_info:
                content = content.replace(mod_info["search"], mod_info["replace"])

            if "append" in mod_info:
                content += mod_info["append"]

            path.write_text(content)
            logger.info(f"Modified file: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to modify file: {e}")
            return False

    def _delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            path = self.base_path / file_path
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def _add_dependencies(self, dependencies: list[str]) -> bool:
        """Add dependencies to requirements.txt."""
        try:
            req_file = self.base_path / "requirements.txt"
            if not req_file.exists():
                req_file.write_text("")

            content = req_file.read_text()
            lines = content.strip().split("\n") if content.strip() else []

            added = 0
            for dep in dependencies:
                # Check if already exists
                if not any(dep.lower() in line.lower() for line in lines):
                    lines.append(dep)
                    added += 1

            if added > 0:
                req_file.write_text("\n".join(lines) + "\n")
                logger.info(f"Added {added} dependencies")
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to add dependencies: {e}")
            return False

    def get_evolution_history(self) -> list[dict[str, Any]]:
        """Get history of all evolutions."""
        return [
            {
                "timestamp": r.timestamp,
                "success": r.success,
                "changes": r.changes_applied,
                "errors": r.errors,
                "backup": r.backup_path
            }
            for r in self.evolution_history
        ]


async def main():
    """Demo self-evolution."""
    print("\n=== ABELITO OS SELF-EVOLUTION ENGINE ===\n")

    engine = SelfEvolutionEngine()

    # Example instructions
    instructions = [
        "Crear un nuevo módulo para procesamiento de datos",
        "Agregar numpy como dependencia",
        "Mejorar el sistema de logging",
    ]

    for instruction in instructions:
        print(f"\nInstruction: {instruction}")
        result = await engine.evolve_from_chat(instruction)
        print(f"Success: {result.success}")
        print(f"Changes applied: {result.changes_applied}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.backup_path:
            print(f"Backup: {result.backup_path}")

    # Show history
    print("\nEvolution History:")
    for entry in engine.get_evolution_history():
        print(f"  • {entry['timestamp']}: {entry['changes']} changes, success={entry['success']}")


if __name__ == "__main__":
    asyncio.run(main())
