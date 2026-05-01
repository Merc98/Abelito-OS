"""AI Connector: Auto-detect and connect to local AI installations."""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class AIInstallation:
    """Represents a detected AI installation."""
    name: str
    type: Literal["ollama", "lmstudio", "llama_cpp", "vllm", "text_generation_inference", "openai_api"]
    path: str
    version: str | None = None
    models: list[str] = field(default_factory=list)
    endpoint: str | None = None
    status: Literal["running", "stopped", "unknown"] = "unknown"
    auto_startable: bool = False


@dataclass
class AIConnection:
    """Active connection to an AI service."""
    installation: AIInstallation
    client: httpx.AsyncClient | None = None
    selected_model: str | None = None
    authenticated: bool = False


class AIDetector:
    """Detects AI installations on the system."""
    
    def __init__(self):
        self.installations: list[AIInstallation] = []
    
    async def scan_system(self) -> list[AIInstallation]:
        """Scan system for AI installations."""
        logger.info("Scanning for AI installations...")
        self.installations = []
        
        # Detect Ollama
        await self._detect_ollama()
        
        # Detect LM Studio
        await self._detect_lmstudio()
        
        # Detect other common AI runtimes
        await self._detect_python_ai()
        
        # Detect Docker-based AI services
        await self._detect_docker_ai()
        
        logger.info(f"Found {len(self.installations)} AI installations")
        return self.installations
    
    async def _detect_ollama(self) -> None:
        """Detect Ollama installation."""
        # Check if ollama command exists
        ollama_path = shutil.which("ollama")
        if ollama_path:
            try:
                result = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.strip() if result.returncode == 0 else None
                
                # Get list of models
                models = []
                try:
                    result = subprocess.run(
                        ["ollama", "list"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.split("\n")[1:]  # Skip header
                        models = [line.split()[0] for line in lines if line.strip()]
                except Exception:
                    pass
                
                # Check if running
                status = "stopped"
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:11434/api/tags", timeout=2)
                        if resp.status_code == 200:
                            status = "running"
                except Exception:
                    pass
                
                self.installations.append(AIInstallation(
                    name="Ollama",
                    type="ollama",
                    path=ollama_path,
                    version=version,
                    models=models,
                    endpoint="http://localhost:11434",
                    status=status,
                    auto_startable=True,
                ))
            except Exception as e:
                logger.error(f"Error detecting Ollama: {e}")
    
    async def _detect_lmstudio(self) -> None:
        """Detect LM Studio installation."""
        # Common LM Studio paths
        lmstudio_paths = [
            Path.home() / ".lmstudio",
            Path("/Applications/LM Studio.app"),
            Path(os.environ.get("PROGRAMFILES", "")) / "LM Studio",
        ]
        
        for path in lmstudio_paths:
            if path.exists():
                # Check if server is running
                status = "stopped"
                models = []
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:1234/v1/models", timeout=2)
                        if resp.status_code == 200:
                            status = "running"
                            data = resp.json()
                            models = [m["id"] for m in data.get("data", [])]
                except Exception:
                    pass
                
                self.installations.append(AIInstallation(
                    name="LM Studio",
                    type="lmstudio",
                    path=str(path),
                    version=None,
                    models=models,
                    endpoint="http://localhost:1234",
                    status=status,
                    auto_startable=False,
                ))
                break
    
    async def _detect_python_ai(self) -> None:
        """Detect Python-based AI installations."""
        # Check for transformers models
        transformers_path = Path.home() / ".cache" / "huggingface"
        if transformers_path.exists():
            models_dir = transformers_path / "hub"
            if models_dir.exists():
                # Count models
                model_count = len([d for d in models_dir.iterdir() if d.is_dir()])
                if model_count > 0:
                    self.installations.append(AIInstallation(
                        name="Hugging Face Transformers",
                        type="llama_cpp",
                        path=str(transformers_path),
                        version=None,
                        models=[f"Local models ({model_count})"],
                        endpoint=None,
                        status="unknown",
                        auto_startable=False,
                    ))
    
    async def _detect_docker_ai(self) -> None:
        """Detect AI services running in Docker."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}:{{.Image}}:{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                containers = result.stdout.strip().split("\n")
                for container in containers:
                    if not container:
                        continue
                    parts = container.split(":")
                    if len(parts) >= 2:
                        name, image = parts[0], parts[1]
                        
                        # Detect vLLM
                        if "vllm" in image.lower():
                            self.installations.append(AIInstallation(
                                name=f"vLLM ({name})",
                                type="vllm",
                                path=f"docker://{name}",
                                version=None,
                                models=[],
                                endpoint="http://localhost:8000",
                                status="running",
                                auto_startable=True,
                            ))
                        
                        # Detect TGI
                        if "text-generation-inference" in image.lower():
                            self.installations.append(AIInstallation(
                                name=f"TGI ({name})",
                                type="text_generation_inference",
                                path=f"docker://{name}",
                                version=None,
                                models=[],
                                endpoint="http://localhost:8080",
                                status="running",
                                auto_startable=True,
                            ))
        except Exception as e:
            logger.debug(f"Error detecting Docker AI: {e}")


class AIConnector:
    """Manages connections to AI services."""
    
    def __init__(self):
        self.detector = AIDetector()
        self.connections: dict[str, AIConnection] = {}
        self.selected_connection: AIConnection | None = None
    
    async def discover_and_connect(self, ai_type: str | None = None, model_name: str | None = None) -> AIConnection | None:
        """Discover AI installations and connect to one."""
        installations = await self.detector.scan_system()
        
        if not installations:
            logger.warning("No AI installations found")
            return None
        
        # Filter by type if specified
        if ai_type:
            installations = [i for i in installations if i.type == ai_type]
        
        if not installations:
            logger.warning(f"No installations of type {ai_type} found")
            return None
        
        # Select first available or match model
        selected = None
        if model_name:
            for inst in installations:
                if any(model_name.lower() in m.lower() for m in inst.models):
                    selected = inst
                    break
        
        if not selected:
            # Pick first running, or first available
            running = [i for i in installations if i.status == "running"]
            selected = running[0] if running else installations[0]
        
        # Create connection
        connection = AIConnection(installation=selected)
        connection.client = httpx.AsyncClient(
            base_url=selected.endpoint,
            timeout=60.0
        )
        
        # Auto-start if needed and possible
        if selected.status == "stopped" and selected.auto_startable:
            await self._auto_start(selected)
        
        self.connections[selected.name] = connection
        self.selected_connection = connection
        
        logger.info(f"Connected to {selected.name}")
        return connection
    
    async def _auto_start(self, installation: AIInstallation) -> None:
        """Auto-start an AI service if possible."""
        if installation.type == "ollama":
            try:
                # Start ollama serve in background
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                await asyncio.sleep(3)  # Wait for startup
                installation.status = "running"
                logger.info("Started Ollama server")
            except Exception as e:
                logger.error(f"Failed to start Ollama: {e}")
    
    async def chat(self, message: str, model: str | None = None, system_prompt: str | None = None) -> str:
        """Send a chat message to the connected AI."""
        if not self.selected_connection or not self.selected_connection.client:
            raise RuntimeError("Not connected to any AI")
        
        conn = self.selected_connection
        model = model or conn.selected_model or (conn.installation.models[0] if conn.installation.models else None)
        
        if not model:
            raise RuntimeError("No model selected")
        
        # Build request based on AI type
        if conn.installation.type == "ollama":
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are Abelito OS assistant."},
                    {"role": "user", "content": message}
                ],
                "stream": False
            }
            endpoint = "/api/chat"
        elif conn.installation.type == "lmstudio":
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are Abelito OS assistant."},
                    {"role": "user", "content": message}
                ]
            }
            endpoint = "/v1/chat/completions"
        else:
            # Generic OpenAI-compatible
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are Abelito OS assistant."},
                    {"role": "user", "content": message}
                ]
            }
            endpoint = "/v1/chat/completions"
        
        try:
            resp = await conn.client.post(endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract response based on format
            if "message" in data:  # Ollama
                return data["message"]["content"]
            elif "choices" in data:  # OpenAI format
                return data["choices"][0]["message"]["content"]
            else:
                return str(data)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    async def list_models(self) -> list[str]:
        """List available models."""
        if not self.selected_connection:
            return []
        return self.selected_connection.installation.models
    
    def select_model(self, model_name: str) -> None:
        """Select a model for future requests."""
        if self.selected_connection:
            self.selected_connection.selected_model = model_name


async def main():
    """Demo AI detection and connection."""
    connector = AIConnector()
    
    print("\n=== ABELITO OS AI CONNECTOR ===\n")
    
    # Discover
    installations = await connector.detector.scan_system()
    print(f"Found {len(installations)} AI installations:\n")
    for inst in installations:
        print(f"• {inst.name} ({inst.type})")
        print(f"  Path: {inst.path}")
        print(f"  Status: {inst.status}")
        print(f"  Models: {', '.join(inst.models[:5])}{'...' if len(inst.models) > 5 else ''}")
        print()
    
    # Connect
    if installations:
        conn = await connector.discover_and_connect()
        if conn:
            print(f"\n✓ Connected to {conn.installation.name}")
            
            # List models
            models = await connector.list_models()
            if models:
                print(f"\nAvailable models: {', '.join(models[:5])}")
            
            # Test chat
            try:
                response = await connector.chat("Hello! What can you help me with?")
                print(f"\nAI Response: {response[:200]}...")
            except Exception as e:
                print(f"\nChat test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
