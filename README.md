# Abelito OS - Sistema Operativo Autónomo Evolutivo v4.0

**Abelito OS** es un sistema operativo autónomo y auto-evolutivo que gira en torno al chat como interfaz principal. Capaz de ejecutarse en cualquier dispositivo (teléfono, servidor, desktop) y evolucionar automáticamente mediante autoanálisis, inyección de código, detección automática de IAs locales, navegación web avanzada y extracción inteligente de información.

## 🌟 Características Principales

### 🔍 Autoanálisis y Mejora Continua
- Escaneo automático del código base en busca de problemas de seguridad, rendimiento y mantenibilidad
- Detección de credenciales hardcodeadas, patrones anti-singletón, cláusulas except bare
- Aplicación automática de correcciones cuando es posible
- Generación de planes de mejora priorizados

### 🤖 Conector Automático de IA
- **Detección automática** de instalaciones locales: Ollama, LM Studio, vLLM, TGI, Hugging Face
- **Auto-conexión** tras selección del usuario
- **Auto-inicio** de servicios detenidos (Ollama)
- Soporte para múltiples modelos simultáneos
- API unificada para chat con cualquier proveedor

### 🌐 WebView Chat Multi-Plataforma
- Interfaz embebida para login en ChatGPT, Claude, Gemini, Poe
- Gestión de sesiones persistente con cookies
- Interfaz de chat en tiempo real vía WebSocket
- Historial de conversaciones almacenado localmente
- Accesible desde cualquier navegador móvil

### 🧭 Navegación y Extracción Avanzada
- Motor de navegación basado en Playwright
- Extracción de información con reglas configurables (CSS selectors, regex)
- Soporte para scroll infinito, capturas de pantalla, llenado de formularios
- Sesiones persistentes con cookies
- Módulos especializados para OSINT (email, username, domain)

### 💉 Inyección y Análisis de Binarios
- Análisis estático de binarios (PEF, ELF, Mach-O)
- Detección de arquitectura y secciones
- Extracción de imports, exports y strings
- Detección de amenazas potenciales
- Inyección dinámica con Frida
- Parcheo de binarios

### 🔄 Auto-Evolución
- Modificación del sistema basada en instrucciones en lenguaje natural
- Creación automática de archivos y módulos
- Gestión de dependencias
- Sistema de backup y rollback automático
- Historial de evoluciones aplicadas

### 📱 Ejecución Universal
- Contenedores Docker para todos los servicios
- API RESTful accesible desde cualquier dispositivo
- Interfaz responsive optimizada para móviles
- Túneles seguros para exposición pública

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    ABELITO OS v4.0                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Auto        │  │ AI           │  │ WebView         │   │
│  │ Analyzer    │  │ Connector    │  │ Chat Manager    │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                │                   │             │
│  ┌──────▼────────────────▼───────────────────▼────────┐   │
│  │           CEO API (FastAPI + NATS)                 │   │
│  └──────┬─────────────────────────────────────────────┘   │
│         │                                                  │
│  ┌──────▼─────────────────────────────────────────────┐   │
│  │  Navigation │ Binary Injector │ Self-Evolution    │   │
│  └──────┬─────────────────────────────────────────────┘   │
│         │                                                  │
│  ┌──────▼─────────────────────────────────────────────┐   │
│  │     Memory Core (SQLite) + Message Bus (NATS)      │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- Python 3.12+ (para desarrollo local)
- Opcional: Ollama, LM Studio u otra IA local
- Herramientas de análisis: `file`, `nm`, `strings`, `readelf` (para binarios)

### Instalación con Docker

```bash
# Clonar el repositorio
git clone <tu-repo-abelito-os>
cd abelito-os

# Levantar todos los servicios
make up

# Verificar estado
make logs

# Ejecutar auto-chequeo
make selfcheck
```

### Configuración de Variables de Entorno

Crear `.env` en la raíz:

```bash
# NATS Message Bus
NATS_URL=nats://nats:4222

# Memory Core
MEMORY_DB_PATH=/app/data/abel_memory.db

# AI Connector
OLLAMA_HOST=http://host.docker.internal:11434
LMSTUDIO_HOST=http://host.docker.internal:1234

# Security
SECRET_KEY=tu_clave_secreta_muy_segura
API_RATE_LIMIT=100

# Logging
LOG_LEVEL=INFO
STRUCTLOG_FORMAT=json
```

## 📖 Uso

### 1. Autoanálisis del Sistema

```bash
# Ejecutar análisis completo
python apps/auto_analyzer/analyzer.py

# Ver reporte
# El sistema generará un informe con:
# - Problemas críticos de seguridad
# - Sugerencias de mejora
# - Correcciones automáticas aplicadas
```

### 2. Conectar a IA Local

```bash
# Detectar IAs disponibles
python apps/ai_connector/connector.py

# El sistema mostrará:
# • Ollama (ollama) - Status: running - Models: llama2, mistral...
# • LM Studio (lmstudio) - Status: stopped
# 
# ✓ Conectado automáticamente a Ollama
```

### 3. Chat con WebView

```bash
# Iniciar servidor WebView
python apps/webview_chat/webview.py

# Acceder desde navegador:
# http://localhost:8081/chat/login/chatgpt
# http://localhost:8081/chat/login/claude
# http://localhost:8081/chat/{session_id}
```

### 4. Navegación y Extracción

```python
from core.navigation.engine import NavigationEngine, ExtractionRule

async def extract_info():
    nav = NavigationEngine(headless=True)
    await nav.start()
    
    # Navegar y extraer
    result = await nav.navigate("https://example.com")
    print(f"Título: {result.title}")
    print(f"Links: {len(result.links)}")
    
    # Extracción con reglas
    rules = [
        ExtractionRule(name="heading", selector="h1"),
        ExtractionRule(name="links", selector="a", multiple=True),
    ]
    data = await nav.extract_with_rules("https://example.com", rules)
    
    await nav.stop()
```

### 5. Análisis de Binarios

```python
from apps.binary_injector.injector import BinaryAnalyzer

async def analyze():
    analyzer = BinaryAnalyzer()
    result = await analyzer.analyze("/path/to/binary")
    
    print(f"Tipo: {result.file_type}")
    print(f"Arquitectura: {result.architecture}")
    print(f"Amenazas: {len(result.threats)}")
```

### 6. Auto-Evolución

```python
from apps.self_evolution.evolution import SelfEvolutionEngine

async def evolve():
    engine = SelfEvolutionEngine()
    
    # Evolucionar desde instrucción en lenguaje natural
    result = await engine.evolve_from_chat(
        "Crear un nuevo módulo para procesamiento de datos"
    )
    
    print(f"Cambios aplicados: {result.changes_applied}")
    print(f"Backup: {result.backup_path}")
```

### 7. Uso desde Teléfono

1. **Exponer el servicio:**
```bash
# Usar ngrok o cloudflared
ngrok http 8080
```

2. **Enviar petición OSINT:**
```bash
curl -X POST https://tu-tunnel.ngrok.io/v1/osint/start \
  -H "Content-Type: application/json" \
  -d '{
    "target": "usuario@example.com",
    "target_type": "email",
    "purpose": "security_audit",
    "consent_or_legal_basis": "legitimate_interest",
    "mode": "RECOMMEND_ONLY"
  }'
```

3. **Consultar resultados:**
```bash
curl https://tu-tunnel.ngrok.io/v1/memory/{workflow_id}
```

## 🔌 Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del sistema |
| `/v1/message` | POST | Enviar mensaje al CEO |
| `/v1/osint/start` | POST | Iniciar investigación OSINT |
| `/v1/memory/{id}` | GET | Reconstruir workflow |
| `/v1/lanes` | GET | Configuración de latencia |
| `/chat/login/{service}` | GET | Login WebView |
| `/chat/{session_id}` | GET | Interfaz de chat |
| `/ws/chat/{session_id}` | WS | Chat en tiempo real |

## 🛠️ Desarrollo

### Estructura del Proyecto

```
/workspace
├── apps/
│   ├── auto_analyzer/      # Autoanálisis y mejora
│   ├── ai_connector/       # Detección y conexión IA
│   ├── webview_chat/       # Chat embebido
│   ├── binary_injector/    # Análisis e inyección de binarios
│   ├── self_evolution/     # Auto-evolución del sistema
│   ├── ceo_api/           # API principal
│   ├── osint_orchestrator/# Orquestación OSINT
│   ├── worker/            # Workers asíncronos
│   └── sandbox_runtime/   # Sandbox de ejecución
├── core/
│   ├── navigation/        # Motor de navegación
│   ├── info_extraction/   # Extracción de información
│   ├── memory.py          # Memoria durable
│   └── sandbox.py         # Sandbox de ejecución
├── shared/
│   └── schemas.py         # Esquemas Pydantic
├── scripts/
│   └── selfcheck.py       # Auto-verificación
└── docs/
    └── ARCHITECTURE_V3_1.md
```

### Agregar Nueva Funcionalidad

El sistema puede auto-modificarse. Ejemplo:

```python
# El auto-analyzer detecta la necesidad y sugiere:
def add_new_feature(feature_name: str):
    """Función auto-generada por Abelito OS."""
    # Implementación insertada automáticamente
    pass
```

## 🔒 Seguridad y Guardrails

- **Solo fuentes públicas** en modo bootstrap
- **AUTO desactivado** para datos sensibles (teléfono, placa, imagen)
- **Requiere propósito** y base legal para cada consulta
- **Modo RECOMMEND_ONLY** por defecto
- **Rate limiting** en todos los endpoints
- **Sanitización** de todas las entradas

## 📊 Monitorización

```bash
# Logs en tiempo real
make logs

# Métricas de Prometheus
curl http://localhost:8080/metrics

# Health checks
curl http://localhost:8080/health
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Coverage
pytest --cov=.

# Auto-check
make selfcheck
```

## 🔄 Actualización y Evolución

El sistema se auto-actualiza mediante:

1. **Autoanálisis periódico** del código base
2. **Detección de mejoras** en dependencias
3. **Aplicación automática** de fixes de seguridad
4. **Reconstrucción** tras fallos usando Memory Core

```bash
# Forzar auto-análisis
python apps/auto_analyzer/analyzer.py

# Ver historial de cambios
cat ./data/analysis_reports/*.json
```

## 📱 Integración con Dispositivos Móviles

### Android/iOS

1. Exponer API mediante túnel seguro
2. Usar WebView nativa para interfaz de chat
3. Llamar endpoints REST directamente
4. Suscribirse a WebSocket para actualizaciones

### Ejemplo React Native

```javascript
const chatWithAbelito = async (message) => {
  const response = await fetch('https://tu-url/v1/message', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: 'mobile-user', text: message})
  });
  return await response.json();
};
```

## 🎯 Casos de Uso

### 1. Investigación OSINT
```bash
curl -X POST /v1/osint/start -d '{
  "target": "nombre_usuario",
  "target_type": "username",
  "purpose": "background_check",
  "mode": "RECOMMEND_ONLY"
}'
```

### 2. Análisis de Binarios
```python
from apps.binary_injector import analyze_binary
report = analyze_binary("./malware.exe")
print(report["threats"])
```

### 3. Chat Multi-Modelo
```python
from apps.ai_connector import AIConnector
connector = AIConnector()
await connector.discover_and_connect()
response = await connector.chat("¿Qué puedes hacer?")
```

## 📝 Licencia

MIT License - Ver LICENSE para detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. El sistema puede auto-analizar tus PRs y sugerir mejoras.

---

**Abelito OS v4.0** - Un sistema que evoluciona contigo.
