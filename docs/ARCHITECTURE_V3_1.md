# ABEL OS+ — Arquitectura Multi‑Agente Soberana v3.3 (Bootstrap)

Este documento aterriza la especificación operativa para ejecución no bloqueante, evolución OSINT y memoria de reconstrucción.

## Decisiones aplicadas en este repo

1. **CEO como control plane**
   - `ceo-api` recibe intención y publica tareas al bus.
2. **Ejecución desacoplada**
   - `worker` consume tareas y resultados.
3. **OSINT Orchestrator**
   - fan-out paralelo (`dorks`, `breach-surface`, `username-surface`) con agregación parcial.
4. **Sandbox runtime**
   - observador dedicado de resultados para auditoría continua.
5. **Memory Core durable**
   - almacena eventos/fallos por workflow en SQLite y soporta reconstrucción post-falla.

## Guardrails OSINT (hard requirements)

- Solo datos públicos.
- `purpose` y `consent_or_legal_basis` obligatorios.
- `AUTO` bloqueado para tipos sensibles (`phone`, `plate`, `image`).
- Rechazo de política: `REJECTED_POLICY` + escalamiento HITL.

## Reconstrucción y auto-recuperación básica

- El pipeline captura fallos por módulo con `fingerprint`.
- El Memory Core consulta fallos previos y añade señal de recuperación.
- Endpoint `/v1/memory/{workflow_id}` reconstruye timeline de eventos y fallos.

## Modo teléfono

1. Ejecutar stack con Docker.
2. Exponer `ceo-api` por túnel seguro.
3. Consumir `/v1/osint/start`.
4. Ver reconstrucción en `/v1/memory/{workflow_id}`.
