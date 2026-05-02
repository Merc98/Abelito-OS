from __future__ import annotations
from dataclasses import dataclass

REQUIRED_PERMISSIONS = {
    "mobile_control": {"mobile_device_control"},
    "osint_offensive": {"internet_session", "darkweb_access"},
}

@dataclass
class PermissionContext:
    granted: set[str]

    def require(self, op: str) -> None:
        missing = REQUIRED_PERMISSIONS.get(op, set()) - self.granted
        if missing:
            raise PermissionError(f"Missing permissions for {op}: {sorted(missing)}")
