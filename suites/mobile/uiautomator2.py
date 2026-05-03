from __future__ import annotations
import uiautomator2 as u2  # type: ignore

class UIAutomator2Controller:
    def __init__(self, serial: str | None = None):
        self.d = u2.connect(serial)

    def dump_hierarchy(self) -> str:
        return self.d.dump_hierarchy()

    def tap(self, x: int, y: int) -> None:
        self.d.click(x, y)
