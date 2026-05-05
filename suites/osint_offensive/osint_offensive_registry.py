"""Registro del suite OSINT ofensivo."""
from __future__ import annotations

SUITE_NAME = "osint_offensive"
ACTIONS = ["tor_client", "robin_smesh", "shodan_query"]

ACTION_DESCRIPTIONS: dict[str, str] = {
    "tor_client": "Ejecuta un comando de red enrutado por Tor (requiere torsocks instalado)",
    "robin_smesh": "Busca en dark-web con robin-smesh (requiere herramienta instalada)",
    "shodan_query": "Consulta la API de Shodan para un host o query (requiere SHODAN_API_KEY)",
}

REQUIRED_PERMISSIONS = {"darkweb_access", "internet_session"}


def describe() -> dict:
    return {
        "suite": SUITE_NAME,
        "actions": ACTIONS,
        "descriptions": ACTION_DESCRIPTIONS,
        "required_permissions": sorted(REQUIRED_PERMISSIONS),
    }
