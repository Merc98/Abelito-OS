# Abelito OS v4.0 - Sistema Operativo Autónomo con IA

[![Version](https://img.shields.io/badge/version-4.0-blue.svg)](https://github.com/abelito-os)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🚀 Características Principales

Abelito OS es un sistema operativo autónomo impulsado por IA que puede:

- **🤖 Auto-analizarse y mejorarse** a sí mismo continuamente
- **📱 Ejecutarse en cualquier dispositivo** (móvil, desktop, servidor)
- **🌐 Conectarse automáticamente a redes** usando modo "Oxígeno"
- **🔍 Analizar binarios** e inyectar código de forma inteligente
- **💬 Conectarse a IAs locales** (Ollama, LM Studio, etc.)
- **🌎 Navegar web y extraer información** automáticamente
- **🛠️ Ejecutar herramientas** y convertirse en la herramienta necesaria
- **🔄 Evolucionar** basado en instrucciones en lenguaje natural

---

## 📋 Tabla de Contenidos

1. [Instalación](#-instalación)
2. [Uso en Móviles](#-uso-en-móviles)
3. [Módulos Principales](#-módulos-principales)
4. [Comandos Rápidos](#-comandos-rápidos)
5. [API Reference](#-api-reference)
6. [Ejemplos de Uso](#-ejemplos-de-uso)
7. [Contribuir](#-contribuir)

---

## 🛠️ Instalación

### Requisitos Previos

- Python 3.8+
- pip
- Docker (opcional, para despliegue en contenedores)

### Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/abelito-os.git
cd abelito-os

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python core/selfcheck.py
```

### Instalación con Docker

```bash
# Construir imagen
docker build -t abelito-os:latest .

# Ejecutar contenedor
docker run -d \
  -p 8000:8000 \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  --name abelito-os \
  abelito-os:latest
```

### Variables de Entorno

Crea un archivo `.env` en la raíz:

```bash
# Configuración de IA
OLLAMA_HOST=localhost:11434
LM_STUDIO_HOST=localhost:1234
OPENAI_API_KEY=tu-api-key

# Configuración de Red
OXYGEN_MODE=true
AUTO_CONNECT=true

# Configuración de Seguridad
ENCRYPTION_KEY=tu-clave-secreta
ALLOWED_NETWORKS=*
```

---

## 📱 Uso en Móviles

Abelito OS puede ejecutarse en cualquier teléfono Android (con Termux) o iOS (con jailbreak), o accederse vía navegador web.

### Opción 1: Servidor Web Móvil (Recomendado)

Esta opción permite usar Abelito OS desde cualquier teléfono sin instalar nada, solo accediendo vía navegador.

#### Paso 1: Iniciar el servidor

```bash
# En tu computadora o servidor
python apps/mobile_runtime/mobile_server.py
```

#### Paso 2: Acceder desde el móvil

1. Asegúrate que tu teléfono y el servidor estén en la misma red WiFi
2. Abre el navegador en tu teléfono
3. Ve a: `http://IP-DEL-SERVIDOR:8080`
4. ¡Listo! Tienes la interfaz completa de Abelito OS

#### Características de la Interfaz Móvil:

- ✅ Escaneo de redes WiFi cercanas
- ✅ Conexión automática a redes
- ✅ Información del dispositivo
- ✅ Ejecución de comandos remotos
- ✅ Logs en tiempo real
- ✅ Interface responsive y optimizada para táctil

### Opción 2: Instalación Nativa en Android (Termux)

```bash
# Instalar Termux desde F-Droid (recomendado) o Play Store

# Actualizar paquetes
pkg update && pkg upgrade

# Instalar Python
pkg install python

# Instalar dependencias adicionales
pkg install git curl wget nmap netcat-openbsd

# Clonar repositorio
git clone https://github.com/tu-usuario/abelito-os.git
cd abelito-os

# Instalar dependencias de Python
pip install -r requirements.txt

# Ejecutar
python apps/mobile_runtime/network_manager.py --oxygen
```

### Opción 3: Modo Oxígeno Automático

El **Modo Oxígeno** es la característica que permite a Abelito OS buscar constantemente conectividad como "fuente de vida":

```bash
# Iniciar modo oxígeno
python apps/mobile_runtime/network_manager.py --oxygen

# El sistema:
# 1. Escanea redes WiFi cercanas cada 10 segundos
# 2. Prioriza redes conocidas
# 3. Se conecta automáticamente a redes abiertas
# 4. Usa herramientas de pentesting si están disponibles
# 5. Mantiene logs de toda la actividad
```

#### Herramientas de Pentesting Soportadas:

- `nmcli` - Gestión de redes (Linux/Android root)
- `iwlist` - Escaneo WiFi (requiere root)
- `airodump-ng` - Análisis avanzado WiFi (requiere root + monitor mode)
- `nmap` - Escaneo de puertos y servicios
- `netcat` - Conexiones de red

> ⚠️ **ADVERTENCIA LEGAL**: El uso de herramientas de pentesting solo está permitido en redes propias o con autorización explícita. El uso no autorizado es ilegal.

---

## 🔧 Módulos Principales

### 1. Auto-Análisis (`apps/auto_analyzer`)

El sistema puede analizarse a sí mismo y aplicar mejoras automáticamente.

```python
from apps.auto_analyzer.analyzer import AutoAnalyzer

analyzer = AutoAnalyzer()
issues = analyzer.scan_codebase()
analyzer.apply_fixes(issues)
```

**Características:**
- Detección de código duplicado
- Identificación de vulnerabilidades
- Sugerencias de optimización
- Auto-corrección de bugs

### 2. Conector de IA (`apps/ai_connector`)

Detección y conexión automática a modelos de IA locales.

```python
from apps.ai_connector.connector import AIConnector

connector = AIConnector()
models = connector.detect_local_models()
# Detecta: Ollama, LM Studio, GPT4All, etc.

connector.connect_to_model("ollama://llama2")
response = connector.chat("Hola, ¿cómo estás?")
```

**Modelos Soportados:**
- Ollama (local)
- LM Studio (local)
- GPT4All (local)
- OpenAI API (remoto)
- Anthropic Claude (remoto)
- Google Gemini (remoto)

### 3. Inyector de Binarios (`apps/binary_injector`)

Análisis e inyección de código en binarios.

```python
from apps.binary_injector.injector import BinaryInjector

injector = BinaryInjector()
analysis = injector.analyze_binary("/path/to/binary")
print(f"Tipo: {analysis['type']}")
print(f"Arquitectura: {analysis['architecture']}")
print(f"Strings encontradas: {analysis['strings_count']}")

# Inyección con Frida
injector.inject_with_frida("/path/to/binary", "script.js")
```

**Formatos Soportados:**
- PE (Windows)
- ELF (Linux/Android)
- Mach-O (macOS/iOS)

### 4. Auto-Evolución (`apps/self_evolution`)

El sistema puede modificarse a sí mismo basado en instrucciones en lenguaje natural.

```python
from apps.self_evolution.evolution import SelfEvolution

evolution = SelfEvolution()

# Instrucción en lenguaje natural
instruction = "Agrega un logger que guarde todos los errores en un archivo"
evolution.evolve_from_instruction(instruction)

# El sistema:
# 1. Interpreta la instrucción
# 2. Crea/modifica archivos
# 3. Instala dependencias si es necesario
# 4. Crea backup automático
# 5. Aplica los cambios
```

### 5. Navegación Web (`core/navigation`)

Navegación automática y extracción de información.

```python
from core.navigation.engine import NavigationEngine

nav = NavigationEngine()
results = nav.search_and_extract(
    query="noticias sobre inteligencia artificial",
    max_results=10,
    extract_links=True
)
```

### 6. Runtime Móvil (`apps/mobile_runtime`)

Gestión de ejecución en dispositivos móviles y conexión automática a redes.

```python
from apps.mobile_runtime.network_manager import MobileRuntime, NetworkAutoConnect

runtime = MobileRuntime()
print(f"Plataforma: {runtime.device_info.platform}")
print(f"Root: {runtime.device_info.is_rooted}")
print(f"Herramientas: {runtime.available_tools}")

connector = NetworkAutoConnect(runtime)
connector.start_oxygen_mode()  # Búsqueda continua de redes
```

---

## ⚡ Comandos Rápidos

### Sistema General

```bash
# Verificar estado del sistema
python core/selfcheck.py

# Iniciar API principal
python apps/ceo_api/main.py

# Modo interactivo con IA
python apps/ai_connector/interactive.py
```

### Redes y Móviles

```bash
# Escanear redes cercanas
python apps/mobile_runtime/network_manager.py --scan

# Conectar a red específica
python apps/mobile_runtime/network_manager.py --connect "MiWiFi" --password "clave123"

# Iniciar modo oxígeno
python apps/mobile_runtime/network_manager.py --oxygen

# Iniciar servidor móvil
python apps/mobile_runtime/mobile_server.py

# Guardar red conocida
python apps/mobile_runtime/network_manager.py --save "MiWiFi" "clave123"
```

### Análisis y Evolución

```bash
# Auto-analizar código
python apps/auto_analyzer/analyzer.py --scan

# Analizar binario
python apps/binary_injector/injector.py --analyze /path/to/file

# Evolucionar sistema
python apps/self_evolution/evolution.py --instruction "Mejora la seguridad del login"
```

### Navegación

```bash
# Buscar y extraer información
python core/navigation/engine.py --search "tema de interés" --extract

# Navegar URL específica
python core/navigation/engine.py --url https://ejemplo.com --scrape
```

---

## 🌐 API Reference

### Endpoints Principales

La API corre en `http://localhost:8000/api/v1`

#### Status

```bash
GET /status
```

Respuesta:
```json
{
  "status": "running",
  "version": "4.0",
  "modules_active": 6,
  "uptime": "2h 15m"
}
```

#### Chat con IA

```bash
POST /chat
Content-Type: application/json

{
  "message": "¿Qué puedes hacer?",
  "model": "ollama://llama2"
}
```

#### Escaneo de Redes

```bash
GET /networks/scan
```

Respuesta:
```json
{
  "success": true,
  "networks": [
    {
      "ssid": "WiFi_Casa",
      "signal_strength": -45,
      "security": "WPA2",
      "is_open": false
    }
  ]
}
```

#### Auto-Evolución

```bash
POST /evolve
Content-Type: application/json

{
  "instruction": "Agrega soporte para Telegram bot",
  "auto_apply": true
}
```

---

## 📚 Ejemplos de Uso

### Ejemplo 1: Configuración Inicial en Móvil

```bash
# 1. Instalar en Termux (Android)
pkg install python git
git clone https://github.com/tu-usuario/abelito-os.git
cd abelito-os
pip install -r requirements.txt

# 2. Configurar redes conocidas
python apps/mobile_runtime/network_manager.py --save "Casa" "mi_password"
python apps/mobile_runtime/network_manager.py --save "Oficina" "office_wifi_pass"

# 3. Iniciar modo oxígeno
python apps/mobile_runtime/network_manager.py --oxygen

# El sistema automáticamente:
# - Escaneará redes cada 10 segundos
# - Se conectará a "Casa" o "Oficina" cuando estén disponibles
# - Buscará redes abiertas si no hay conocidas
```

### Ejemplo 2: Auto-Mejora del Sistema

```python
from apps.self_evolution.evolution import SelfEvolution

evolution = SelfEvolution()

# Pedir mejora en lenguaje natural
instructions = [
    "Agrega un endpoint para subir archivos",
    "Mejora el logging para que guarde en formato JSON",
    "Crea un módulo para enviar notificaciones por email"
]

for instruction in instructions:
    print(f"Ejecutando: {instruction}")
    evolution.evolve_from_instruction(instruction, auto_apply=True)
    
print("✅ Sistema evolucionado exitosamente")
```

### Ejemplo 3: Análisis de Binario Sospechoso

```python
from apps.binary_injector.injector import BinaryInjector

injector = BinaryInjector()

# Analizar archivo
analysis = injector.analyze_binary("/downloads/archivo.exe")

print(f"Tipo: {analysis['type']}")
print(f"Imports sospechosos: {analysis['suspicious_imports']}")
print(f"Amenazas potenciales: {analysis['threats']}")

# Si es seguro, inyectar script de monitoreo
if analysis['threats'] == 0:
    injector.inject_monitoring_script("/downloads/archivo.exe")
```

### Ejemplo 4: Conexión a IA Local

```python
from apps.ai_connector.connector import AIConnector

connector = AIConnector()

# Detectar modelos instalados
models = connector.detect_local_models()
print(f"Modelos encontrados: {models}")

# Conectar al primero disponible
if models:
    connector.connect_to_model(models[0]['url'])
    
    # Conversación
    while True:
        user_input = input("Tú: ")
        if user_input.lower() == 'salir':
            break
        
        response = connector.chat(user_input)
        print(f"IA: {response}")
```

---

## 🏗️ Arquitectura

```
abelito-os/
├── apps/
│   ├── auto_analyzer/       # Auto-análisis de código
│   ├── ai_connector/        # Conexión a IAs
│   ├── binary_injector/     # Inyección en binarios
│   ├── self_evolution/      # Auto-evolución
│   ├── mobile_runtime/      # Ejecución en móviles
│   ├── network_autoconnect/ # Conexión automática a redes
│   └── ceo_api/            # API principal
├── core/
│   ├── navigation/         # Navegación web
│   ├── memory.py          # Memoria del sistema
│   └── selfcheck.py       # Verificación interna
├── config/                 # Configuraciones
├── tests/                  # Tests automatizados
└── README.md              # Este archivo
```

---

## 🔒 Seguridad

### Consideraciones Importantes

1. **Herramientas de Pentesting**: Solo úsalas en redes propias o con autorización
2. **Inyección de Binarios**: Puede ser detectado como malware por antivirus
3. **Auto-Evolución**: Crea backups automáticos pero revisa los cambios
4. **Credenciales**: Nunca commits archivos `.env` con credenciales reales

### Mejores Prácticas

```bash
# 1. Usar variables de entorno para credenciales
export OPENAI_API_KEY="tu-key"

# 2. Revisar cambios antes de aplicar evolución
python apps/self_evolution/evolution.py --instruction "..." --dry-run

# 3. Mantener backups
cp -r config config.backup

# 4. Ejecutar en entorno aislado para testing
docker run --rm -it abelito-os:latest
```

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Áreas de Mejora Buscadas

- 📱 Mejor soporte para iOS
- 🌐 Más proveedores de IA soportados
- 🔒 Mejoras de seguridad
- 📊 Dashboard web más completo
- 🧪 Más tests automatizados
- 📚 Documentación en más idiomas

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para detalles.

---

## 🙏 Agradecimientos

- Comunidad de código abierto
- Proyectos de IA local (Ollama, LM Studio)
- Herramientas de pentesting (Aircrack-ng, Nmap)
- Contribuidores del proyecto

---

## 📞 Soporte

- **Issues**: GitHub Issues
- **Discusión**: GitHub Discussions
- **Email**: soporte@abelito-os.dev

---

**Hecho con ❤️ y mucha ☕**

*Abelito OS - Evolucionando constantemente*
