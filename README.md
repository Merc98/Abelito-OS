# Abelito OS v5.0 - Segundo Cerebro Digital Autónomo

[![Version](https://img.shields.io/badge/version-5.0-blue)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Android%20%7C%20iOS%20%7C%20Linux%20%7C%20Mac%20%7C%20Windows-orange)](#)

## 🎯 ¿Qué es Abelito OS?

Abelito OS es tu **segundo cerebro digital autónomo**. No es una aplicación, es un entorno operativo inteligente que vive sobre cualquier hardware (móvil, servidor, desktop) y evoluciona contigo. 

**Diferencia clave:** Tú expresas intenciones en lenguaje natural ("Limpia mis contactos", "Busca inversores"), y el sistema descompone, ejecuta múltiples herramientas coordinadamente y te entrega el resultado final. Sin pasos intermedios manuales.

---

## ✨ Características Principales

### 🧠 Orquestación Inteligente
- **Entrada Natural:** Habla con el sistema como hablarías con una persona
- **Auto-Conciencia:** Sabe qué herramientas tiene, cuáles le faltan y cómo conseguirlas
- **Ejecución Paralela:** Coordina múltiples habilidades simultáneamente
- **Auto-Remediación:** Si falta una herramienta, la instala o sintetiza una alternativa
- **Validación Automática:** Verifica resultados y reintenta si falla

### 📱 Multi-Plataforma Nativo
- **Sin Docker:** Instalación directa en cualquier SO
- **Móvil Primero:** Funciona en Android (Termux) e iOS como app nativa
- **Sincronización:** Tus datos y flujos se sincronizan entre dispositivos
- **Modo Offline:** Opera sin conexión y sincroniza cuando recupera conectividad

### 🔧 Capacidades Implementadas

#### 1. **Bio-Digital Sync** (Gestión de Contactos)
```python
# Ejemplo: "Limpia mis contactos y une las redes sociales"
# El sistema:
# 1. Escanea agenda telefónica, emails y redes sociales
# 2. Detecta duplicados con fuzzy matching
# 3. Correlaciona identidades (mismo nombre, diferente email)
# 4. Escribe físicamente en la app nativa de contactos del SO
# 5. Enriquece con perfiles de LinkedIn, Twitter, GitHub
```

#### 2. **Análisis e Inyección de Binarios**
- Detección de tipo (PE, ELF, Mach-O)
- Extracción de imports, exports, strings
- Detección de amenazas
- Inyección de código con Frida
- Parcheo automático

#### 3. **OSINT Avanzado**
- Búsqueda con Dorking
- Scraping de redes sociales
- Análisis de Pastebin
- Extracción de información estructurada

#### 4. **Business Intelligence**
- Búsqueda de grants y fondos
- Análisis de oportunidades
- Reportes automáticos

#### 5. **Auto-Evolución**
- Modifica su propio código fuente
- Añade nuevas funciones bajo demanda
- Sistema de backup y rollback

#### 6. **Control HID Físico**
- Controla la UI del dispositivo como si fueras tú
- Integra con Appium para automatización móvil
- Llena formularios nativos automáticamente

---

## 🚀 Instalación Rápida

### Método Universal (Recomendado)

```bash
# Clonar repositorio
git clone <tu-repo>
cd abelito-os

# Ejecutar instalador automático
chmod +x install.sh
./install.sh
```

El instalador detecta tu SO (Linux, Mac, Android/Termux, Windows) y configura todo automáticamente.

### Instalación Manual por Plataforma

#### Android (Termux)
```bash
pkg update && pkg upgrade
pkg install python git curl wget
git clone <tu-repo>
cd abelito-os
pip install -r requirements.txt
```

#### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

---

## 📖 Uso

### Modo Comando (CLI)

```bash
# Activar entorno
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate   # Windows

# Ejecutar el orquestador principal
python core/orchestrator.py

# Ejecutar módulos específicos
python -m apps.osint_orchestrator.main
python -m apps.self_evolution.evolution
python -m apps.binary_injector.injector
```

### Modo Interactivo (Python)

```python
from core.orchestrator import Orchestrator
import asyncio

async def main():
    orch = Orchestrator()
    
    # Ejemplos de intenciones naturales
    await orch.process_intention("Limpia mis contactos, elimina duplicados y enlaza redes sociales")
    await orch.process_intention("Analiza este binario en busca de malware")
    await orch.process_intention("Busca grants para startups de IA en Europa")
    await orch.process_intention("Sincroniza mis chats de WhatsApp con mi CRM")

asyncio.run(main())
```

### Modo Móvil (PWA)

1. Inicia el servidor: `python apps/mobile_runtime/mobile_server.py`
2. Abre navegador en tu móvil: `http://tu-ip:8080`
3. Toca "Agregar a pantalla de inicio"
4. ¡Listo! Funciona como app nativa

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                 ENTRADA: Intención Natural              │
│         "Limpia contactos y une redes sociales"         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ORQUESTADOR PRINCIPAL (Core)               │
│  • Analiza intención                                   │
│  • Descompone en tareas                                │
│  • Verifica herramientas                               │
│  • Diseña flujo (DAG)                                  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Gestor   │  │  Gestor   │  │  Gestor   │
│ Brechas   │  │  Flujo    │  │ Memoria   │
│           │  │           │  │           │
│ • Instala │  │ • DAG     │  │ • Contexto│
│ • Sintet. │  │ • Paralelo│  │ • History │
│ • Backup  │  │ • Deps    │  │ • Learn   │
└───────────┘  └───────────┘  └───────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           EJECUTOR DE HABILIDADES (Skills)              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │Contact  │ │ OSINT   │ │ Binary  │ │ HID/Appium  │  │
│  │ Sync    │ │ Search  │ │ Analysis│ │ Automation  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  VALIDACIÓN & SALIDA                    │
│  • Verifica resultado vs intención                     │
│  • Reintenta con estrategia alternativa si falla       │
│  • Reporte conciso al usuario                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura del Proyecto

```
abelito-os/
├── core/                      # Núcleo del sistema
│   ├── orchestrator.py        # Cerebro central (orquestación)
│   ├── memory.py              # Memoria persistente
│   ├── navigation/            # Navegación web
│   └── sandbox.py             # Entorno seguro de ejecución
│
├── apps/                      # Aplicaciones especializadas
│   ├── ai_connector/          # Conexión a IAs (Ollama, LM Studio)
│   ├── auto_analyzer/         # Auto-análisis de código
│   ├── binary_injector/       # Análisis/inyección de binarios
│   ├── mobile_runtime/        # Servidor móvil y red
│   ├── osint_orchestrator/    # Motor OSINT
│   ├── self_evolution/        # Auto-evolución del código
│   ├── webview_chat/          # Chat embebido
│   └── business/              # Business intelligence
│
├── scripts/                   # Scripts utilitarios
│   ├── selfcheck.py           # Verificación del sistema
│   └── ...
│
├── data/                      # Datos persistentes
├── logs/                      # Logs del sistema
├── backups/                   # Backups automáticos
│
├── install.sh                 # Instalador universal
├── requirements.txt           # Dependencias Python
├── MANIFEST.md                # Manifiesto de capacidades
└── README.md                  # Este archivo
```

---

## 🔒 Seguridad

- **Encriptación:** AES-256 para datos sensibles
- **Sandbox:** Ejecución aislada de código no confiable
- **Permisos Granulares:** Solicita permiso solo para acciones irreversibles
- **Backup Automático:** Rollback ante fallos críticos
- **Modo Fantasma:** Opera sin notificaciones intrusivas

---

## 🧪 Testing

```bash
# Verificar estado del sistema
python scripts/selfcheck.py

# Ejecutar tests unitarios
pytest tests/

# Probar módulo específico
python -m pytest apps/binary_injector/test_injector.py -v
```

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea rama feature (`git checkout -b feature/nueva-funcion`)
3. Commit cambios (`git commit -m 'Añade nueva función'`)
4. Push (`git push origin feature/nueva-funcion`)
5. Abre Pull Request

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

---

## 🆘 Soporte

- **Documentación:** `/docs`
- **Issues:** GitHub Issues
- **Discusión:** GitHub Discussions

---

## 🎯 Roadmap

- [ ] Integración con MCP (Model Context Protocol) estándar
- [ ] Plugins marketplace dinámico
- [ ] Soporte para más plataformas móviles
- [ ] Mejora en análisis semántico con LLM local
- [ ] Sincronización P2P offline-first

---

**Abelito OS v5.0** - Tu segundo cerebro, siempre contigo, siempre evolucionando.
