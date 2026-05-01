# ABEL OS+ 3.1

## Estado
Bootstrap técnico inicial del runtime multi-agente soberano.

## Objetivo
Convertir ABEL OS en una arquitectura operativa continua con:
- control central vía CEO Agent;
- memoria única compartida;
- lanes de ejecución aislados;
- agregación por suficiencia;
- quórum configurable;
- persistencia fuera del camino crítico;
- ministerio móvil con decisión determinística y degradación segura.

## Componentes base
- **CEO Agent**: parsea intención, clasifica, planifica y responde.
- **Workflow Orchestrator**: coordina workflows con quorum, deadlines y cancelación temprana.
- **Lane Policy Layer**: define `REALTIME`, `SHORT`, `HEAVY`, `DURABLE`, `BACKGROUND`.
- **Shared Schemas**: contratos homogéneos para tareas, resultados parciales, decisiones y workflows.
- **Mobile Automation Ministry**:
  - Device Session Manager
  - Offer Screen Detector
  - UI Tree Parser
  - OCR ROI Parser
  - Vision Grounding Parser
  - Decision Engine
  - Action Executor
  - Drift Monitor

## Semántica de cierre
Un workflow puede cerrar como:
- `SUCCESS_FULL`
- `SUCCESS_QUORUM`
- `SUCCESS_PARTIAL_SUFFICIENT`
- `DEGRADED_BUT_USABLE`
- `HITL_REQUIRED`
- `FAILED_UNRECOVERABLE`

## Modos móviles
- `RECOMMEND_ONLY`
- `SEMI_AUTO`
- `AUTO_DETERMINISTIC`
- `AUTO_INTERNAL_LAB`

## Prioridad de lanes
1. realtime
2. device actions
3. short compute
4. durable workflows
5. heavy compute
6. background

## Primer alcance implementado en este bootstrap
1. Modelado de contratos del sistema.
2. Políticas por lane listas para ser consumidas por orquestación.
3. Orquestador in-memory con quorum y cierre temprano.
4. CEO Agent con planificación inicial por intención.
5. Motor de decisión móvil determinístico con degradación a recomendación.
6. API FastAPI para salud, planificación y evaluación móvil.
7. `docker-compose.yml` base para core, Redis, NATS, Qdrant y MinIO.

## Siguiente fase recomendada
- integrar NATS JetStream real;
- persistir workflows durables en Temporal;
- mover locks a Redis;
- añadir Graph Manager y Policy Engine;
- incorporar Appium / UiAutomator2 / WDA como adapters del ministerio móvil;
- agregar observabilidad completa con OTel, Prometheus, Grafana, Loki y Tempo.
