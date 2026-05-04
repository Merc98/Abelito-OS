from __future__ import annotations

from pathlib import Path


SKILLS = {
    "setup": """# agent_setup\nEnsure baseline app scaffold exists.\n- Verify app/, tests/, docker-compose.yml\n- Create minimal placeholders if missing\n""",
    "deploy": """# agent_deploy\nPackage and verify deployment target.\nVerification gate:\n- /auth/login -> 200\n- /health -> 200\n- logs include 'Server running'\n- logs include provider identity\n""",
    "customize": """# agent_customize\nImplement feature by editing routes/controllers/models and then run deploy verification gate.\n""",
}


class AgentSkeleton:
    def __init__(self, root: str = ".") -> None:
        self.root = Path(root)
        self.skill_dir = self.root / ".agent" / "skills"
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_skill_files()

    def _ensure_skill_files(self) -> None:
        for name, content in SKILLS.items():
            p = self.skill_dir / f"{name}.md"
            if not p.exists():
                p.write_text(content, encoding="utf-8")

    def agent_setup(self) -> dict[str, str]:
        created = []
        for rel in ["app", "tests", "logs", "backups"]:
            p = self.root / rel
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                created.append(rel)
        compose = self.root / "docker-compose.yml"
        if not compose.exists():
            compose.write_text("version: '3.9'\nservices: {}\n", encoding="utf-8")
            created.append("docker-compose.yml")
        return {"status": "ok", "created": ", ".join(created) if created else "none"}

    def agent_deploy(self) -> dict[str, str]:
        # Placeholder local deploy gate; real deploy integrations can extend this.
        checks = {
            "/auth/login": "200",
            "/health": "200",
            "server_log": "Server running",
            "provider_log": "provider identity",
        }
        return {"status": "ready", "verification": str(checks)}

    def agent_customize(self, feature_desc: str) -> dict[str, str]:
        note = self.root / ".agent" / "last_customization.md"
        note.write_text(f"Feature requested: {feature_desc}\n", encoding="utf-8")
        gate = self.agent_deploy()
        return {"status": "captured", "feature": feature_desc, "deploy_gate": gate["status"]}
