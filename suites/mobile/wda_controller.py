"""WDA Controller — iOS WebDriverAgent wrapper, solo macOS."""
from __future__ import annotations

import importlib
import sys
from typing import Any


class WDAController:
    """Controla un dispositivo iOS via Facebook WebDriverAgent.
    Solo disponible en macOS. En otros entornos devuelve errores descriptivos.
    """

    def __init__(self, url: str = "http://localhost:8100"):
        self._url = url
        self._client: Any = None
        self._error: str | None = None

        if sys.platform != "darwin":
            self._error = "WDAController solo disponible en macOS"
            return

        try:
            wda = importlib.import_module("wda")
            self._client = wda.Client(url)
        except ModuleNotFoundError:
            self._error = "facebook-wda not installed — run: pip install facebook-wda"
        except Exception as exc:
            self._error = str(exc)

    def _check(self) -> dict[str, str] | None:
        if self._error:
            return {"error": self._error}
        return None

    def status(self) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        return self._client.status()

    def tap(self, x: int, y: int) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        self._client.session().tap(x, y)
        return {"status": "ok", "x": x, "y": y}

    def find_and_tap(self, label: str | None = None, xpath: str | None = None) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        sess = self._client.session()
        try:
            if label:
                el = sess(label=label)
            elif xpath:
                el = sess.xpath(xpath)
            else:
                return {"error": "provide label or xpath"}
            el.tap()
            return {"status": "ok", "target": label or xpath}
        except Exception as exc:
            return {"error": str(exc)}

    def source(self) -> dict[str, Any]:
        err = self._check()
        if err:
            return err
        return {"source": self._client.source()}
