from __future__ import annotations
from dataclasses import dataclass


@dataclass
class KillSwitch:
    session_id: str
    active: bool = False
    triggered: bool = False

    def enable(self) -> None:
        self.active = True

    def disable(self) -> None:
        self.active = False

    def trigger(self) -> None:
        self.triggered = True
        self.active = False

    def is_active(self) -> bool:
        return self.active and not self.triggered

    def require_active_or_raise(self) -> None:
        if not self.is_active():
            raise RuntimeError("kill_switch_inactive")
