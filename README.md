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

- `GET /health`
- `GET /dashboard`
- `GET /v1/lanes`
- `POST /v1/message`
- `POST /v1/osint/start`
- `GET /v1/memory/{workflow_id}`

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
