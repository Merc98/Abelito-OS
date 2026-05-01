#!/bin/bash
# Abelito OS v5.0 - Instalador Universal Nativo
# Se adapta a cualquier sistema operativo sin necesidad de Docker
# Detecta el entorno, instala dependencias y configura el sistema automáticamente

set -e

echo "🚀 Abelito OS v5.0 - Instalador Universal"
echo "=========================================="

# Detectar sistema operativo
detect_os() {
    if [[ "$OSTYPE" == "linux-android"* ]]; then
        echo "android"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo "📱 Sistema detectado: $OS"

# Funciones de instalación por plataforma
install_linux() {
    echo "🔧 Instalando dependencias para Linux..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git curl wget
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip git curl wget
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python python-pip git curl wget
    fi
    
    install_common
}

install_macos() {
    echo "🔧 Instalando dependencias para macOS..."
    
    if ! command -v brew &> /dev/null; then
        echo "   Instalando Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install python3 git
    install_common
}

install_android() {
    echo "🔧 Configurando entorno para Android (Termux)..."
    
    pkg update -y
    pkg install -y python python-pip git curl wget tool-repo
    install_common
}

install_windows() {
    echo "🔧 Configurando entorno para Windows..."
    
    # Verificar si Python está instalado
    if ! command -v python &> /dev/null; then
        echo "   ⚠️  Python no detectado. Por favor instale Python 3.8+ desde https://python.org"
        exit 1
    fi
    
    install_common
}

install_common() {
    echo ""
    echo "📦 Instalando dependencias Python..."
    
    # Crear entorno virtual
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activar entorno
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    echo ""
    echo "✅ Dependencias instaladas exitosamente"
}

# Verificar herramientas externas
print_optional_tool_instructions() {
    local tool="$1"
    case "$tool" in
        adb)
            echo "      - Linux: sudo apt install android-tools-adb | sudo dnf install android-tools"
            echo "      - macOS: brew install android-platform-tools"
            echo "      - Windows: instalar Android Platform Tools (adb)"
            echo "      - URL: https://developer.android.com/tools/adb"
            ;;
        appium)
            echo "      - Requiere Node.js y npm"
            echo "      - Comando: npm install -g appium"
            echo "      - URL: https://appium.io/docs/en/latest/quickstart/"
            ;;
        frida)
            echo "      - Python: pip install frida-tools"
            echo "      - URL: https://frida.re/docs/installation/"
            ;;
        ollama)
            echo "      - Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh"
            echo "      - Windows: descargar instalador oficial"
            echo "      - URL: https://ollama.com/download"
            ;;
    esac
}

check_external_tools() {
    echo ""
    echo "🔍 Verificando herramientas externas..."

    tools_needed=("adb" "appium" "frida" "ollama")
    tools_missing=()

    for tool in "${tools_needed[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo "   ✅ $tool encontrado"
        else
            echo "   ⚠️  $tool no encontrado (opcional)"
            tools_missing+=("$tool")
        fi
    done

    if [ ${#tools_missing[@]} -gt 0 ]; then
        echo ""
        echo "💡 Herramientas opcionales faltantes detectadas."
        echo "   Abelito OS seguirá funcionando con rutas de fallback, pero con capacidades reducidas:"
        echo "   - Sin adb/appium: se desactiva automatización HID móvil."
        echo "   - Sin frida: se desactiva inyección dinámica de binarios."
        echo "   - Sin ollama: se usa solo integración remota de IA (si está configurada)."
        echo ""
        echo "🛠️  Instalación sugerida por herramienta:"
        for tool in "${tools_missing[@]}"; do
            echo "   • $tool"
            print_optional_tool_instructions "$tool"
        done
    fi
}

# Configurar variables de entorno
setup_environment() {
    echo ""
    echo "⚙️  Configurando entorno..."
    
    # Crear archivo .env si no existe
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Abelito OS Configuration
ABELITO_VERSION=5.0
DATA_DIR=./data
LOG_LEVEL=INFO
AUTO_EVOLVE=true
MEMORY_PERSISTENT=true
EOF
        echo "   ✅ Archivo .env creado"
    fi
    
    # Crear directorios necesarios
    mkdir -p data logs backups
    echo "   ✅ Directorios creados"
}

# Mostrar instrucciones de uso
show_usage() {
    echo ""
    echo "=========================================="
    echo "✅ ¡Instalación completada!"
    echo "=========================================="
    echo ""
    echo "📚 Cómo usar Abelito OS:"
    echo ""
    echo "1. Activar entorno:"
    echo "   source venv/bin/activate  # Linux/Mac"
    echo "   venv\\Scripts\\activate     # Windows"
    echo ""
    echo "2. Ejecutar el orquestador:"
    echo "   python core/orchestrator.py"
    echo ""
    echo "3. O usar comandos directos:"
    echo "   python -m apps.osint_orchestrator.main"
    echo "   python -m apps.self_evolution.evolution"
    echo ""
    echo "4. En móvil (Android/iOS):"
    echo "   - Abre el navegador en http://localhost:8080"
    echo "   - Toca 'Agregar a pantalla de inicio'"
    echo "   - ¡Listo! Funciona como app nativa"
    echo ""
    echo "🎯 Ejemplo de uso:"
    echo '   python -c "from core.orchestrator import Orchestrator; import asyncio; asyncio.run(Orchestrator().process_intention(\"Limpia mis contactos\"))"'
    echo ""
    echo "📖 Más información en README.md"
    echo ""
}

# Ejecutar instalación según SO
case $OS in
    linux)
        install_linux
        ;;
    macos)
        install_macos
        ;;
    android)
        install_android
        ;;
    windows)
        install_windows
        ;;
    *)
        echo "❌ Sistema operativo no reconocido: $OS"
        echo "   Intentando instalación genérica..."
        install_common
        ;;
esac

# Pasos comunes
check_external_tools
setup_environment
show_usage

echo "🎉 ¡Bienvenido a Abelito OS v5.0!"
echo "   Tu segundo cerebro digital está listo."
