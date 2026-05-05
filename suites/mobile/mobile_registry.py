"""Registro del suite mobile."""
from __future__ import annotations

SUITE_NAME = "mobile"
ACTIONS = ["rideshare_accept_reject", "device_discovery", "tap", "dump_hierarchy", "screenshot"]

ACTION_DESCRIPTIONS: dict[str, str] = {
    "rideshare_accept_reject": "Acepta o rechaza un viaje en app de rideshare via UIAutomator2",
    "device_discovery": "Lista dispositivos Android conectados por ADB",
    "tap": "Toca coordenadas (x,y) en la pantalla del dispositivo",
    "dump_hierarchy": "Vuelca la jerarquia de vistas XML del dispositivo actual",
    "screenshot": "Captura pantalla del dispositivo y la retorna en base64",
}


def describe() -> dict:
    return {"suite": SUITE_NAME, "actions": ACTIONS, "descriptions": ACTION_DESCRIPTIONS}
