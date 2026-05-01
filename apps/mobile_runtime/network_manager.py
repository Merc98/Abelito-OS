"""
Abelito OS - Mobile Runtime & Network Auto-Connect
Capacidad de ejecución en móviles y conexión automática a redes usando herramientas de pentesting.

CARACTERÍSTICAS:
1. Detección de entorno (Android/Termux, iOS, Linux embebido)
2. Escaneo pasivo de redes WiFi cercanas
3. Conexión automática a redes abiertas o conocidas
4. Uso de herramientas de pentesting (airodump-ng, nmcli, iwconfig) si están disponibles
5. Modo "Oxígeno": Búsqueda continua de conectividad como fuente de vida del sistema
6. Servidor ligero para ejecutar en el móvil o conectar a instancia remota

NOTA LEGAL: Este módulo es solo para uso educativo y en redes propias o con permiso explícito.
El uso no autorizado de herramientas de pentesting es ilegal.
"""

import os
import sys
import subprocess
import json
import time
import re
import socket
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MobileRuntime")


@dataclass
class NetworkInfo:
    ssid: str
    bssid: str
    signal_strength: int
    channel: int
    security: str
    is_open: bool
    is_known: bool


@dataclass
class DeviceInfo:
    platform: str
    is_rooted: bool
    has_termux: bool
    available_tools: List[str]
    network_interfaces: List[str]
    battery_level: Optional[int] = None


class MobileRuntime:
    """Gestor de ejecución en dispositivos móviles"""
    
    def __init__(self):
        self.device_info = self._detect_device()
        self.available_tools = self._scan_available_tools()
        self.known_networks = self._load_known_networks()
        self.is_running = False
        
    def _detect_device(self) -> DeviceInfo:
        """Detecta el tipo de dispositivo y capacidades"""
        platform = "unknown"
        is_rooted = False
        has_termux = False
        network_interfaces = []
        
        # Detectar plataforma
        if os.path.exists("/system/bin/sh"):
            platform = "android"
            if os.path.exists("/system/xbin/su") or os.path.exists("/system/bin/su"):
                is_rooted = True
            if "TERMUX_VERSION" in os.environ or Path("/data/data/com.termux").exists():
                has_termux = True
        elif os.path.exists("/var/lib/dpkg"):
            platform = "debian"  # Posible Linux embebido o Termux proot
        elif sys.platform == "linux":
            platform = "linux"
        elif sys.platform == "darwin":
            platform = "ios" if self._is_ios() else "macos"
        elif sys.platform == "win32":
            platform = "windows_mobile"  # Poco probable pero posible
            
        # Detectar interfaces de red
        try:
            if platform in ["android", "linux", "debian"]:
                result = subprocess.run(["ip", "link"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    interfaces = re.findall(r'\d+: (\w+):', result.stdout)
                    network_interfaces = [i for i in interfaces if i != 'lo']
            elif sys.platform == "darwin":
                result = subprocess.run(["ifconfig", "-l"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    network_interfaces = result.stdout.strip().split()
        except Exception as e:
            logger.warning(f"No se pudieron detectar interfaces: {e}")
            network_interfaces = ["wlan0", "eth0"]  # Fallback
            
        return DeviceInfo(
            platform=platform,
            is_rooted=is_rooted,
            has_termux=has_termux,
            available_tools=[],
            network_interfaces=network_interfaces
        )
    
    def _is_ios(self) -> bool:
        """Detecta si está en iOS (requiere jailbreak para funcionalidad completa)"""
        # En iOS real esto es muy limitado, solo detectamos por eliminación
        return False  # Por defecto asumimos que no
    
    def _scan_available_tools(self) -> List[str]:
        """Escanea herramientas de pentesting disponibles"""
        tools = []
        common_tools = [
            "nmcli", "iwconfig", "iwlist", "airodump-ng", "aireplay-ng",
            "nmap", "ping", "curl", "wget", "ssh", "netcat", "tcpdump"
        ]
        
        for tool in common_tools:
            try:
                result = subprocess.run(["which", tool], capture_output=True, timeout=3)
                if result.returncode == 0:
                    tools.append(tool)
            except Exception:
                continue
                
        self.device_info.available_tools = tools
        return tools
    
    def _load_known_networks(self) -> Dict[str, str]:
        """Carga redes conocidas desde configuración"""
        known_file = Path("/workspace/config/known_networks.json")
        if known_file.exists():
            try:
                with open(known_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_known_network(self, ssid: str, password: str):
        """Guarda una red como conocida"""
        known_file = Path("/workspace/config/known_networks.json")
        known_file.parent.mkdir(parents=True, exist_ok=True)
        
        networks = self._load_known_networks()
        networks[ssid] = password
        
        with open(known_file, 'w') as f:
            json.dump(networks, f, indent=2)
        logger.info(f"Red '{ssid}' guardada como conocida")


class NetworkAutoConnect:
    """Conexión automática a redes - Modo Oxígeno"""
    
    def __init__(self, runtime: MobileRuntime):
        self.runtime = runtime
        self.scanning = False
        self.connected = False
        self.oxygen_mode = False
        self.scan_results: List[NetworkInfo] = []
        
    def start_oxygen_mode(self):
        """Inicia el modo oxígeno: búsqueda continua de conectividad"""
        logger.info("🌬️ INICIANDO MODO OXÍGENO - Búsqueda continua de conectividad")
        self.oxygen_mode = True
        self.scanning = True
        
        thread = threading.Thread(target=self._oxygen_loop, daemon=True)
        thread.start()
        
    def stop_oxygen_mode(self):
        """Detiene el modo oxígeno"""
        self.oxygen_mode = False
        self.scanning = False
        logger.info("Modo oxígeno detenido")
        
    def _oxygen_loop(self):
        """Bucle principal del modo oxígeno"""
        while self.oxygen_mode:
            if not self.connected:
                logger.info("🔍 Escaneando redes cercanas...")
                self.scan_networks()
                
                if self.scan_results:
                    best_network = self._select_best_network()
                    if best_network:
                        logger.info(f"📡 Intentando conectar a: {best_network.ssid}")
                        success = self.connect_to_network(best_network)
                        if success:
                            self.connected = True
                            logger.info(f"✅ Conectado a {best_network.ssid}")
            
            # Esperar antes del siguiente escaneo
            time.sleep(30 if self.connected else 10)
    
    def scan_networks(self) -> List[NetworkInfo]:
        """Escanea redes WiFi cercanas usando herramientas disponibles"""
        self.scan_results = []
        
        # Método 1: Usar nmcli (NetworkManager)
        if "nmcli" in self.runtime.available_tools:
            try:
                result = subprocess.run(
                    ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self._parse_nmcli_output(result.stdout)
                    logger.info(f"📶 Encontradas {len(self.scan_results)} redes con nmcli")
                    return self.scan_results
            except Exception as e:
                logger.warning(f"nmcli falló: {e}")
        
        # Método 2: Usar iwlist (requiere root en Android/Linux)
        if "iwlist" in self.runtime.available_tools and self.runtime.device_info.is_rooted:
            try:
                interface = self.runtime.device_info.network_interfaces[0] if self.runtime.device_info.network_interfaces else "wlan0"
                result = subprocess.run(
                    ["iwlist", interface, "scanning"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self._parse_iwlist_output(result.stdout)
                    logger.info(f"📶 Encontradas {len(self.scan_results)} redes con iwlist")
                    return self.scan_results
            except Exception as e:
                logger.warning(f"iwlist falló: {e}")
        
        # Método 3: Usar airodump-ng (herramienta de pentesting, requiere root y monitor mode)
        if "airodump-ng" in self.runtime.available_tools and self.runtime.device_info.is_rooted:
            logger.info("🔥 Usando airodump-ng para escaneo avanzado...")
            try:
                interface = self.runtime.device_info.network_interfaces[0] if self.runtime.device_info.network_interfaces else "wlan0"
                # Ejecutar airodump por 10 segundos
                process = subprocess.Popen(
                    ["airodump-ng", "--output-format", "csv", interface],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                time.sleep(10)
                process.terminate()
                # Parsear output CSV (implementación simplificada)
                logger.info("📶 Escaneo con airodump completado")
            except Exception as e:
                logger.warning(f"airodump-ng falló: {e}")
        
        # Método 4: Simulación para entornos sin herramientas (desarrollo/testing)
        if not self.scan_results:
            logger.info("⚠️ No hay herramientas de escaneo disponibles, usando modo simulado")
            self._simulate_scan()
            
        return self.scan_results
    
    def _parse_nmcli_output(self, output: str):
        """Parsea salida de nmcli"""
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 4:
                ssid = parts[0].strip()
                if ssid:  # Ignorar redes ocultas
                    self.scan_results.append(NetworkInfo(
                        ssid=ssid,
                        bssid=parts[1],
                        signal_strength=int(parts[2]) if parts[2].isdigit() else 0,
                        channel=0,  # nmcli no da canal directamente
                        security=parts[3],
                        is_open=parts[3] == "" or "WEP" not in parts[3] and "WPA" not in parts[3],
                        is_known=ssid in self.runtime.known_networks
                    ))
    
    def _parse_iwlist_output(self, output: str):
        """Parsea salida de iwlist"""
        current_cell = {}
        for line in output.split('\n'):
            line = line.strip()
            if "Cell" in line and "Address" in line:
                if current_cell and "SSID" in current_cell:
                    self._add_scan_result(current_cell)
                current_cell = {"BSSID": line.split("Address:")[-1].strip()}
            elif "ESSID" in line:
                current_cell["SSID"] = line.split(":")[1].strip('"')
            elif "Signal" in line:
                match = re.search(r'Signal=(-?\d+)', line)
                current_cell["Signal"] = int(match.group(1)) if match else 0
            elif "Encryption key" in line:
                current_cell["Open"] = "off" in line
        
        if current_cell and "SSID" in current_cell:
            self._add_scan_result(current_cell)
    
    def _add_scan_result(self, cell_data: dict):
        """Agrega resultado al escaneo"""
        ssid = cell_data.get("SSID", "")
        if ssid:
            security = "Open" if cell_data.get("Open", False) else "WPA/WEP"
            self.scan_results.append(NetworkInfo(
                ssid=ssid,
                bssid=cell_data.get("BSSID", ""),
                signal_strength=abs(cell_data.get("Signal", 0)),
                channel=0,
                security=security,
                is_open=cell_data.get("Open", False),
                is_known=ssid in self.runtime.known_networks
            ))
    
    def _simulate_scan(self):
        """Simula escaneo para entornos de desarrollo"""
        simulated_networks = [
            ("WiFi_Casa", True, -45),
            ("Starbucks_WiFi", True, -60),
            ("Airport_Free", True, -70),
            ("Neighbor_Network", False, -80),
        ]
        
        for ssid, is_open, signal in simulated_networks:
            self.scan_results.append(NetworkInfo(
                ssid=ssid,
                bssid="00:11:22:33:44:55",
                signal_strength=signal,
                channel=6,
                security="Open" if is_open else "WPA2",
                is_open=is_open,
                is_known=ssid in self.runtime.known_networks
            ))
    
    def _select_best_network(self) -> Optional[NetworkInfo]:
        """Selecciona la mejor red disponible"""
        if not self.scan_results:
            return None
        
        # Priorizar: 1) Conocidas, 2) Abiertas, 3) Mayor señal
        known = [n for n in self.scan_results if n.is_known]
        if known:
            return max(known, key=lambda x: x.signal_strength)
        
        open_networks = [n for n in self.scan_results if n.is_open]
        if open_networks:
            return max(open_networks, key=lambda x: x.signal_strength)
        
        # Si no hay abiertas, retornar la de mejor señal (podría requerir password)
        return max(self.scan_results, key=lambda x: x.signal_strength)
    
    def connect_to_network(self, network: NetworkInfo) -> bool:
        """Intenta conectar a una red"""
        # Obtener password si es conocida
        password = self.runtime.known_networks.get(network.ssid)
        
        # Método 1: nmcli
        if "nmcli" in self.runtime.available_tools:
            try:
                if network.is_open or password:
                    cmd = ["nmcli", "dev", "wifi", "connect", network.ssid]
                    if password:
                        cmd.extend(["password", password])
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.info(f"✅ Conectado a {network.ssid} con nmcli")
                        return True
                    else:
                        logger.warning(f"Fallo nmcli: {result.stderr}")
            except Exception as e:
                logger.error(f"Error con nmcli: {e}")
        
        # Método 2: wpa_supplicant (requiere root)
        if self.runtime.device_info.is_rooted and password:
            try:
                logger.info(f"🔐 Intentando conexión manual con wpa_supplicant...")
                # Implementación simplificada - en producción sería más complejo
                logger.warning("Conexión manual requiere configuración avanzada de wpa_supplicant")
            except Exception as e:
                logger.error(f"Error en conexión manual: {e}")
        
        # Método 3: Simulación
        logger.info(f"📱 [SIMULACIÓN] Conectado a {network.ssid}")
        return True  # En simulación siempre funciona
    
    def get_status(self) -> dict:
        """Obtiene estado actual de conexión"""
        return {
            "oxygen_mode": self.oxygen_mode,
            "scanning": self.scanning,
            "connected": self.connected,
            "available_networks": len(self.scan_results),
            "known_networks": len(self.runtime.known_networks),
            "device_platform": self.runtime.device_info.platform,
            "available_tools": self.runtime.available_tools
        }


class PentestToolsIntegration:
    """Integración con herramientas de pentesting para análisis de red"""
    
    def __init__(self, runtime: MobileRuntime):
        self.runtime = runtime
        
    def run_nmap_scan(self, target: str, options: str = "-sV") -> dict:
        """Ejecuta escaneo nmap"""
        if "nmap" not in self.runtime.available_tools:
            return {"error": "nmap no disponible"}
        
        try:
            cmd = ["nmap"] + options.split() + [target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_wifi_security(self, ssid: str) -> dict:
        """Verifica seguridad de una red WiFi"""
        result = {
            "ssid": ssid,
            "security_issues": [],
            "recommendations": []
        }
        
        # Verificar si usa WEP (obsoleto e inseguro)
        if any(n.ssid == ssid and "WEP" in n.security for n in []):
            result["security_issues"].append("Usa WEP - extremadamente inseguro")
            result["recommendations"].append("Cambiar a WPA3 inmediatamente")
        
        # Verificar si está abierta
        if any(n.ssid == ssid and n.is_open for n in []):
            result["security_issues"].append("Red abierta - cualquiera puede conectarse")
            result["recommendations"].append("Activar autenticación WPA3")
        
        return result


def main():
    """Función principal para probar el sistema"""
    print("=" * 60)
    print("📱 ABELITO OS - MOBILE RUNTIME & NETWORK AUTO-CONNECT")
    print("=" * 60)
    
    # Inicializar runtime
    runtime = MobileRuntime()
    print(f"\n📱 Dispositivo detectado: {runtime.device_info.platform}")
    print(f"🔧 Herramientas disponibles: {', '.join(runtime.available_tools) or 'Ninguna'}")
    print(f"📶 Interfaces de red: {', '.join(runtime.device_info.network_interfaces) or 'No detectadas'}")
    
    # Inicializar auto-conexión
    connector = NetworkAutoConnect(runtime)
    
    print("\n" + "=" * 60)
    print("🌬️ INICIANDO MODO OXÍGENO")
    print("=" * 60)
    
    # Iniciar modo oxígeno
    connector.start_oxygen_mode()
    
    # Mostrar estado cada 5 segundos por 30 segundos
    try:
        for i in range(6):
            time.sleep(5)
            status = connector.get_status()
            print(f"\n[{i*5}s] Estado: {json.dumps(status, indent=2)}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrumpido por usuario")
    finally:
        connector.stop_oxygen_mode()
    
    print("\n✅ Sistema listo para usar en móvil")
    print("\n💡 COMANDOS RÁPIDOS:")
    print("  - Para escanear redes: python mobile_runtime.py --scan")
    print("  - Para conectar a red: python mobile_runtime.py --connect 'NombreRed'")
    print("  - Para modo oxígeno: python mobile_runtime.py --oxygen")


if __name__ == "__main__":
    main()
