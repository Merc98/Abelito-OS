from __future__ import annotations
import subprocess
from typing import Any

class OsintSuite:
    def _require_net(self, params: dict[str, Any]) -> None:
        scope = params.get("permission_scope", "")
        if scope not in {"internet_limited", "internet_session"}:
            raise PermissionError("Se requiere permission_scope=internet_limited|internet_session")

    def dns_lookup(self, domain: str, permission_scope: str) -> dict[str, Any]:
        self._require_net({"permission_scope": permission_scope})
        proc = subprocess.run(["nslookup", domain], capture_output=True, text=True, check=False)
        return {"tool": "nslookup", "domain": domain, "returncode": proc.returncode, "output": proc.stdout[-4000:]}

    def whois_lookup(self, target: str, permission_scope: str) -> dict[str, Any]:
        self._require_net({"permission_scope": permission_scope})
        proc = subprocess.run(["whois", target], capture_output=True, text=True, check=False)
        return {"tool": "whois", "target": target, "returncode": proc.returncode, "output": proc.stdout[:4000]}

    def execute_action(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "dns_lookup":
            return self.dns_lookup(params["domain"], params.get("permission_scope", ""))
        if action == "whois_lookup":
            return self.whois_lookup(params["target"], params.get("permission_scope", ""))
        raise ValueError(f"unsupported action: {action}")

def setup() -> OsintSuite:
    return OsintSuite()
