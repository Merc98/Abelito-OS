from __future__ import annotations
import sys

class WDAController:
    def __init__(self):
        if sys.platform != "darwin":
            raise RuntimeError("WDAController solo disponible en macOS")
        import wda  # type: ignore
        self.client = wda.Client()
