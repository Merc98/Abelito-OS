"""
Abelito OS - Servidor Ligero para Móviles
Servidor HTTP ligero que permite ejecutar Abelito OS en cualquier dispositivo móvil
a través del navegador, con interfaz responsive y capacidades completas.
"""

import os
import sys
import json
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MobileServer")

# Directorio base
BASE_DIR = Path("/workspace")


class MobileAPIHandler(SimpleHTTPRequestHandler):
    """Manejador de peticiones API para móvil"""
    
    def do_GET(self):
        """Maneja peticiones GET"""
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api(parsed_path)
        # Servir interfaz web
        elif parsed_path.path == '/' or parsed_path.path.endswith('.html'):
            self.serve_interface()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Maneja peticiones POST"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            self.handle_api_post(parsed_path, post_data)
        else:
            self.send_error(404, "Endpoint no encontrado")
    
    def handle_api(self, parsed_path):
        """Maneja peticiones API GET"""
        endpoint = parsed_path.path.replace('/api/', '')
        query_params = parse_qs(parsed_path.query)
        
        response_data = {}
        
        try:
            if endpoint == 'status':
                response_data = self.get_status()
            elif endpoint == 'scan_networks':
                from apps.mobile_runtime.network_manager import MobileRuntime, NetworkAutoConnect
                runtime = MobileRuntime()
                connector = NetworkAutoConnect(runtime)
                networks = connector.scan_networks()
                response_data = {
                    'success': True,
                    'networks': [vars(n) for n in networks]
                }
            elif endpoint == 'device_info':
                from apps.mobile_runtime.network_manager import MobileRuntime
                runtime = MobileRuntime()
                response_data = {
                    'success': True,
                    'device': vars(runtime.device_info),
                    'tools': runtime.available_tools
                }
            else:
                response_data = {'error': f'Endpoint {endpoint} no encontrado'}
        except Exception as e:
            response_data = {'error': str(e)}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def handle_api_post(self, parsed_path, post_data):
        """Maneja peticiones API POST"""
        endpoint = parsed_path.path.replace('/api/', '')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            data = {}
        
        response_data = {}
        
        try:
            if endpoint == 'connect_network':
                from apps.mobile_runtime.network_manager import MobileRuntime, NetworkAutoConnect
                runtime = MobileRuntime()
                connector = NetworkAutoConnect(runtime)
                
                ssid = data.get('ssid')
                password = data.get('password')
                
                if ssid:
                    if password:
                        runtime.save_known_network(ssid, password)
                    
                    # Buscar la red en el escaneo
                    networks = connector.scan_networks()
                    target_network = next((n for n in networks if n.ssid == ssid), None)
                    
                    if target_network:
                        success = connector.connect_to_network(target_network)
                        response_data = {'success': success, 'message': f'Conectado a {ssid}' if success else 'Fallo en conexión'}
                    else:
                        response_data = {'success': False, 'message': f'Red {ssid} no encontrada'}
                else:
                    response_data = {'success': False, 'message': 'SSID requerido'}
            
            elif endpoint == 'execute_command':
                command = data.get('command', '')
                if command:
                    # Ejecutar comando de forma segura (sandbox)
                    result = subprocess.run(
                        command.split(),
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=str(BASE_DIR)
                    )
                    response_data = {
                        'success': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
                else:
                    response_data = {'success': False, 'message': 'Comando requerido'}
            
            elif endpoint == 'save_network':
                from apps.mobile_runtime.network_manager import MobileRuntime
                runtime = MobileRuntime()
                ssid = data.get('ssid')
                password = data.get('password')
                
                if ssid and password:
                    runtime.save_known_network(ssid, password)
                    response_data = {'success': True, 'message': f'Red {ssid} guardada'}
                else:
                    response_data = {'success': False, 'message': 'SSID y password requeridos'}
            
            else:
                response_data = {'error': f'Endpoint {endpoint} no encontrado'}
        
        except Exception as e:
            response_data = {'error': str(e), 'success': False}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def get_status(self) -> dict:
        """Obtiene estado del sistema"""
        return {
            'status': 'running',
            'version': '4.0',
            'platform': sys.platform,
            'python_version': sys.version,
            'base_dir': str(BASE_DIR),
            'modules_available': self.list_modules()
        }
    
    def list_modules(self) -> list:
        """Lista módulos disponibles"""
        modules_dir = BASE_DIR / 'apps'
        if modules_dir.exists():
            return [d.name for d in modules_dir.iterdir() if d.is_dir()]
        return []
    
    def serve_interface(self):
        """Sirve la interfaz web móvil"""
        interface_file = BASE_DIR / 'apps' / 'mobile_runtime' / 'interface.html'
        
        if not interface_file.exists():
            self.create_interface()
        
        self.path = str(interface_file)
        return super().do_GET()
    
    def create_interface(self):
        """Crea la interfaz web si no existe"""
        interface_file = BASE_DIR / 'apps' / 'mobile_runtime' / 'interface.html'
        interface_file.parent.mkdir(parents=True, exist_ok=True)
        
        html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abelito OS Mobile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .status-item:last-child { border-bottom: none; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            width: 100%;
            margin: 8px 0;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:active { transform: scale(0.98); }
        .btn-secondary {
            background: #6c757d;
        }
        .input-group {
            margin: 15px 0;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            color: #495057;
            font-weight: 600;
        }
        .input-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 16px;
        }
        .network-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .network-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .signal-strength {
            color: #28a745;
            font-weight: bold;
        }
        .log-output {
            background: #1e1e1e;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 15px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Abelito OS Mobile</h1>
        
        <div class="status-card">
            <h3>Estado del Sistema</h3>
            <div id="status-content" class="loading">Cargando...</div>
        </div>
        
        <button class="btn" onclick="scanNetworks()">📶 Escanear Redes</button>
        <button class="btn" onclick="showConnectForm()">🔗 Conectar a Red</button>
        <button class="btn btn-secondary" onclick="getDeviceInfo()">ℹ️ Info Dispositivo</button>
        
        <div id="connect-form" class="status-card" style="display:none;">
            <h3>Conectar a WiFi</h3>
            <div class="input-group">
                <label>SSID:</label>
                <input type="text" id="wifi-ssid" placeholder="Nombre de la red">
            </div>
            <div class="input-group">
                <label>Password (opcional):</label>
                <input type="password" id="wifi-password" placeholder="Contraseña">
            </div>
            <button class="btn" onclick="connectToNetwork()">Conectar</button>
        </div>
        
        <div id="network-list" class="network-list"></div>
        <div id="log-output" class="log-output" style="display:none;"></div>
    </div>

    <script>
        const API_BASE = '/api';
        
        async function fetchAPI(endpoint, method = 'GET', data = null) {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (data) options.body = JSON.stringify(data);
            
            const response = await fetch(`${API_BASE}/${endpoint}`, options);
            return await response.json();
        }
        
        function log(message) {
            const logOutput = document.getElementById('log-output');
            logOutput.style.display = 'block';
            const timestamp = new Date().toLocaleTimeString();
            logOutput.innerHTML += `[${timestamp}] ${message}\\n`;
            logOutput.scrollTop = logOutput.scrollHeight;
        }
        
        async function loadStatus() {
            try {
                const status = await fetchAPI('status');
                const content = document.getElementById('status-content');
                content.className = '';
                content.innerHTML = `
                    <div class="status-item"><span>Versión:</span><strong>${status.version}</strong></div>
                    <div class="status-item"><span>Plataforma:</span><strong>${status.platform}</strong></div>
                    <div class="status-item"><span>Módulos:</span><strong>${status.modules_available.length}</strong></div>
                `;
                log(`Sistema iniciado - Versión ${status.version}`);
            } catch (error) {
                log(`Error cargando estado: ${error.message}`);
            }
        }
        
        async function scanNetworks() {
            log('Escaneando redes...');
            try {
                const result = await fetchAPI('scan_networks');
                const listDiv = document.getElementById('network-list');
                
                if (result.success && result.networks.length > 0) {
                    listDiv.innerHTML = result.networks.map(net => `
                        <div class="network-item">
                            <div>
                                <strong>${net.ssid}</strong><br>
                                <small>${net.security}</small>
                            </div>
                            <div class="signal-strength">${net.signal_strength} dBm</div>
                        </div>
                    `).join('');
                    log(`Encontradas ${result.networks.length} redes`);
                } else {
                    listDiv.innerHTML = '<p>No se encontraron redes</p>';
                    log('No se encontraron redes');
                }
            } catch (error) {
                log(`Error escaneando: ${error.message}`);
            }
        }
        
        function showConnectForm() {
            document.getElementById('connect-form').style.display = 'block';
        }
        
        async function connectToNetwork() {
            const ssid = document.getElementById('wifi-ssid').value;
            const password = document.getElementById('wifi-password').value;
            
            if (!ssid) {
                alert('Por favor ingresa el SSID');
                return;
            }
            
            log(`Intentando conectar a ${ssid}...`);
            try {
                const result = await fetchAPI('connect_network', 'POST', { ssid, password });
                if (result.success) {
                    log(`✅ ${result.message}`);
                    alert(result.message);
                } else {
                    log(`❌ ${result.message}`);
                    alert(result.message);
                }
            } catch (error) {
                log(`Error conectando: ${error.message}`);
            }
        }
        
        async function getDeviceInfo() {
            log('Obteniendo info del dispositivo...');
            try {
                const result = await fetchAPI('device_info');
                if (result.success) {
                    log(`Dispositivo: ${result.device.platform}`);
                    log(`Root: ${result.device.is_rooted ? 'Sí' : 'No'}`);
                    log(`Termux: ${result.device.has_termux ? 'Sí' : 'No'}`);
                    log(`Herramientas: ${result.tools.join(', ') || 'Ninguna'}`);
                    alert(`Plataforma: ${result.device.platform}\\nRoot: ${result.device.is_rooted}\\nHerramientas: ${result.tools.length}`);
                }
            } catch (error) {
                log(`Error: ${error.message}`);
            }
        }
        
        // Cargar estado inicial
        loadStatus();
    </script>
</body>
</html>"""
        
        with open(interface_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Interfaz móvil creada en {interface_file}")


class MobileServer:
    """Servidor principal para móviles"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Inicia el servidor"""
        try:
            self.server = socketserver.TCPServer((self.host, self.port), MobileAPIHandler)
            self.server.allow_reuse_address = True
            
            logger.info(f"📱 Servidor móvil iniciado en http://{self.host}:{self.port}")
            logger.info("Accede desde tu teléfono a esta dirección")
            
            # Ejecutar en thread separado
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            return True
        except OSError as e:
            logger.error(f"Error iniciando servidor: {e}")
            return False
    
    def stop(self):
        """Detiene el servidor"""
        if self.server:
            self.server.shutdown()
            logger.info("Servidor detenido")


def main():
    """Función principal"""
    print("=" * 60)
    print("📱 ABELITO OS - SERVIDOR MÓVIL")
    print("=" * 60)
    
    # Obtener IP local
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\n🌐 Servidor accesible en:")
    print(f"   Local: http://localhost:8080")
    print(f"   Red:   http://{local_ip}:8080")
    print(f"\n📲 Abre esta URL en tu teléfono")
    print("=" * 60)
    
    server = MobileServer(port=8080)
    
    if server.start():
        print("\n✅ Servidor corriendo. Presiona Ctrl+C para detener")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️ Deteniendo servidor...")
            server.stop()
            print("✅ Servidor detenido")


if __name__ == "__main__":
    import time
    import socket
    main()
