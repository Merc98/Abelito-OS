#!/usr/bin/env python3
"""
Abelito OS v5.0 - Punto de Entrada Principal
Este script inicia todos los servicios del sistema:
- CEO API con dashboard interactivo
- Chat con soporte para artefactos (tipo Claude)
- Servidor web para UI
"""

import asyncio
import os
import sys
import uvicorn
from pathlib import Path

# Añadir el workspace al path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    """Muestra banner de inicio"""
    print("=" * 70)
    print("🤖  Abelito OS v5.0 - Segundo Cerebro Digital Autónomo")
    print("=" * 70)
    print()
    print("📍 Servicios disponibles:")
    print("   • CEO API         → http://localhost:8080")
    print("   • Dashboard       → http://localhost:8080/dashboard")
    print("   • Chat + Artefactos → http://localhost:8080/chat")
    print()
    print("🚀 Iniciando servicios...")
    print("=" * 70)


async def main():
    """Función principal que coordina todos los servicios"""
    from core.orchestrator import Orchestrator
    
    # Inicializar orquestador
    orchestrator = Orchestrator()
    status = orchestrator.get_status_report()
    
    print_banner()
    print(f"\n📊 Estado inicial:")
    print(f"   Capacidades: {sum(1 for v in status['capabilities'].values() if v)}/{len(status['capabilities'])}")
    print(f"   Herramientas: {sum(1 for v in status['tools_available'].values() if v)}/{len(status['tools_available'])}")
    print()
    
    # Configurar variables de entorno
    os.environ.setdefault("NATS_URL", "nats://localhost:4222")
    os.environ.setdefault("MEMORY_DB_PATH", "./data/abel_memory.db")
    os.environ.setdefault("USERS_DB_PATH", "./data/abel_users.db")
    
    # Crear directorios necesarios
    Path("./data").mkdir(exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)
    Path("./backups").mkdir(exist_ok=True)
    
    # Iniciar servidor FastAPI
    print("🌐 Iniciando servidor web en http://0.0.0.0:8080")
    print("   Presiona Ctrl+C para detener\n")
    
    config = uvicorn.Config(
        app="apps.ceo_api.main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Deteniendo Abelito OS...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
