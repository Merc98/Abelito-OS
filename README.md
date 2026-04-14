# Abelito-OS (ABEL OS+ bootstrap)

Bootstrap funcional de **ABEL OS+ v3.3** con arquitectura multi-agente soberana orientada a ejecución no bloqueante, OSINT con guardrails y memoria durable de reconstrucción.

## Qué ya funciona

- API del CEO (`ceo-api`) para recibir mensajes y lanzar flujos OSINT.
- Publicación de tareas al bus NATS (`abel.tasks.*`).
- Worker asíncrono para consumir tareas y resultados.
- Orquestador OSINT inicial (`osint-orchestrator`) con fan-out paralelo.
- Sandbox runtime (`sandbox-runtime`) para observación de resultados y auditoría continua.
- Memory Core (SQLite) que persiste eventos/fallos por workflow y permite reconstrucción.

## Endpoints

- `GET /health`
- `GET /dashboard`
- `GET /v1/lanes`
- `POST /v1/message`
- `POST /v1/osint/start`
- `GET /v1/memory/{workflow_id}`

## Guardrails de seguridad/legal

- Solo señales de **fuentes públicas** en esta fase bootstrap.
- `AUTO` se bloquea para `phone`, `plate`, `image`.
- Requiere `purpose` + `consent_or_legal_basis`.
- Flujo orientado a `RECOMMEND_ONLY` y `HITL`.

## Sandbox + memoria operativa

- Base de memoria: `./data/abel_memory.db`.
- Cada workflow guarda:
  - eventos (`QUEUED`, `RECEIVED`, `COMPLETED`),
  - fallos (stage, error, fingerprint).
- Se puede reconstruir estado y revisar dónde falló antes vía `/v1/memory/{workflow_id}`.

## Inicio rápido

```bash
make up
make selfcheck
make verify-all
```

## Capas de validación (multi-entorno)

- **Capa 1 (rápida):** `make selfcheck` para chequeo básico de memoria.
- **Capa 2 (unitaria):** `make test` para validar guardrails/pipeline/API sin dependencias externas.
- **Capa 3 (simulación):** `make simulate` para simular publicación de tareas, ejecución OSINT y reintentos de NATS.
- **Todo junto:** `make verify-all`.

## Uso desde teléfono (inmediato)

1. Levanta el stack en tu servidor/local con `make up`.
2. Expón el puerto `8080` con un túnel seguro.
3. Desde el teléfono envía POST a `/v1/osint/start`.
4. Consulta la memoria en `/v1/memory/{workflow_id}`.

## Dashboard minimalista + Android

- Dashboard web: abre `http://localhost:8080/dashboard`.
- APK Android (WebView minimal):
  1. Ejecuta `make apk`.
  2. Si no existe SDK, el script bootstrappea `cmdline-tools` + `platforms;android-34` + `build-tools;34.0.0` en `./.android-sdk`.
  3. APK esperada: `mobile/android-dashboard/app/build/outputs/apk/debug/app-debug.apk`.
