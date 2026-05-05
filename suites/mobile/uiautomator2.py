"""UIAutomator2 controller — wrapper seguro con fallback para entornos sin device."""
from __future__ import annotations

import base64
import importlib
from typing import Any


class UIAutomator2Controller:
    """Controla un dispositivo Android via uiautomator2.
    Si el paquete no esta instalado, todos los metodos devuelven dict de error
    en lugar de lanzar ImportError, permitiendo que el sistema siga funcionando.
    """

    def __init__(self, serial: str | None = None):
        self._serial = serial
        self._d: Any = None
        self._error: str | None = None
        try:
            u2 = importlib.import_module("uiautomator2")
            self._d = u2.connect(serial)
        except ModuleNotFoundError:
            self._error = "uiautomator2 not installed — run: pip install uiautomator2"
        except Exception as exc:
            self._error = str(exc)

    def _check(self) -> dict[str, str] | None:
        if self._error:
            return {"error": self._error}
        return None

    def dump_hierarchy(self) -> str | dict:
        err = self._check()
        if err:
            return err  # type: ignore[return-value]
        return self._d.dump_hierarchy()

    def tap(self, x: int, y: int) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        self._d.click(x, y)
        return {"status": "ok", "x": x, "y": y}

    def screenshot_b64(self) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        png: bytes = self._d.screenshot(format="raw")
        return {"format": "png", "data_b64": base64.b64encode(png).decode()}

    def find_and_tap(self, text: str | None = None, resource_id: str | None = None) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        try:
            if text:
                el = self._d(text=text)
            elif resource_id:
                el = self._d(resourceId=resource_id)
            else:
                return {"error": "provide text or resource_id"}
            el.click()
            return {"status": "ok", "target": text or resource_id}
        except Exception as exc:
            return {"error": str(exc)}

    def swipe(self, fx: int, fy: int, tx: int, ty: int, duration: float = 0.3) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        self._d.swipe(fx, fy, tx, ty, duration=duration)
        return {"status": "ok", "from": [fx, fy], "to": [tx, ty]}
