"""WebView Chat: Embed web-based AI chats with login support."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

logger = structlog.get_logger()


@dataclass
class ChatSession:
    """Represents a chat session with a web AI service."""
    id: str
    service: str  # "chatgpt", "claude", "gemini", "custom"
    url: str
    authenticated: bool = False
    cookies: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    message_history: list[dict[str, str]] = field(default_factory=list)


class WebViewChatManager:
    """Manages WebView-based chat sessions."""
    
    def __init__(self):
        self.sessions: dict[str, ChatSession] = {}
        self.service_configs = {
            "chatgpt": {
                "name": "ChatGPT",
                "url": "https://chat.openai.com",
                "login_url": "https://chat.openai.com/auth/login",
                "api_endpoint": "https://chat.openai.com/backend-api/conversation",
            },
            "claude": {
                "name": "Claude",
                "url": "https://claude.ai",
                "login_url": "https://claude.ai/login",
                "api_endpoint": "https://claude.ai/api/organizations",
            },
            "gemini": {
                "name": "Gemini",
                "url": "https://gemini.google.com",
                "login_url": "https://accounts.google.com",
                "api_endpoint": None,  # Web-only
            },
            "poe": {
                "name": "Poe",
                "url": "https://poe.com",
                "login_url": "https://poe.com/login",
                "api_endpoint": "https://poe.com/api/gql_POST",
            },
        }
    
    def create_session(self, service: str, session_id: str | None = None) -> ChatSession:
        """Create a new chat session."""
        import uuid
        
        if service not in self.service_configs:
            raise ValueError(f"Unknown service: {service}")
        
        config = self.service_configs[service]
        session = ChatSession(
            id=session_id or str(uuid.uuid4()),
            service=service,
            url=config["url"],
        )
        self.sessions[session.id] = session
        logger.info(f"Created session {session.id} for {service}")
        return session
    
    def get_login_html(self, service: str, session_id: str) -> str:
        """Generate HTML for embedded login WebView."""
        if service not in self.service_configs:
            raise ValueError(f"Unknown service: {service}")
        
        config = self.service_configs[service]
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login to {config['name']} - Abelito OS</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            width: 90%;
            max-width: 800px;
            height: 80vh;
        }}
        .header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 18px; color: #333; }}
        .status {{ 
            padding: 6px 12px; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: 600;
        }}
        .status.pending {{ background: #fff3cd; color: #856404; }}
        .status.authenticated {{ background: #d4edda; color: #155724; }}
        iframe {{ 
            width: 100%; 
            height: calc(100% - 60px); 
            border: none; 
        }}
        .instructions {{
            padding: 15px 20px;
            background: #e7f3ff;
            border-top: 1px solid #b3d9ff;
            font-size: 13px;
            color: #004085;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Login to {config['name']}</h1>
            <span class="status pending" id="status">Waiting for login...</span>
        </div>
        <iframe 
            src="{config['login_url']}" 
            id="loginFrame"
            sandbox="allow-forms allow-scripts allow-same-origin allow-popups"
        ></iframe>
        <div class="instructions">
            <strong>Instructions:</strong> Log in to your {config['name']} account. 
            Once authenticated, click the "I'm logged in" button below or the system will auto-detect.
            <br><br>
            <button onclick="notifyLogin()" style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                ✓ I'm logged in
            </button>
        </div>
    </div>
    <script>
        const sessionId = '{session_id}';
        const service = '{service}';
        
        function notifyLogin() {{
            document.getElementById('status').className = 'status authenticated';
            document.getElementById('status').textContent = 'Authenticated!';
            
            // Send message to parent window
            window.parent.postMessage({{
                type: 'auth_complete',
                sessionId: sessionId,
                service: service
            }}, '*');
        }}
        
        // Auto-detect navigation to main page (post-login)
        let lastUrl = '';
        setInterval(() => {{
            try {{
                const iframe = document.getElementById('loginFrame');
                const currentUrl = iframe.contentWindow.location.href;
                if (currentUrl !== lastUrl && !currentUrl.includes('login')) {{
                    notifyLogin();
                }}
                lastUrl = currentUrl;
            }} catch(e) {{}}
        }}, 1000);
    </script>
</body>
</html>
"""
    
    async def verify_authentication(self, session: ChatSession) -> bool:
        """Verify if session is authenticated."""
        # This would check cookies/tokens
        # For now, simplified implementation
        if session.cookies:
            session.authenticated = True
            return True
        return False
    
    def save_session(self, session: ChatSession, storage_path: str = "./data/chat_sessions") -> None:
        """Save session to disk."""
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        file_path = Path(storage_path) / f"{session.id}.json"
        
        data = {
            "id": session.id,
            "service": session.service,
            "url": session.url,
            "authenticated": session.authenticated,
            "cookies": session.cookies,
            "headers": session.headers,
            "message_history": session.message_history,
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved session {session.id}")
    
    def load_session(self, session_id: str, storage_path: str = "./data/chat_sessions") -> ChatSession | None:
        """Load session from disk."""
        file_path = Path(storage_path) / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path) as f:
            data = json.load(f)
        
        session = ChatSession(
            id=data["id"],
            service=data["service"],
            url=data["url"],
            authenticated=data.get("authenticated", False),
            cookies=data.get("cookies", {}),
            headers=data.get("headers", {}),
            message_history=data.get("message_history", []),
        )
        
        self.sessions[session_id] = session
        return session
    
    def get_chat_interface_html(self, session: ChatSession) -> str:
        """Generate chat interface HTML."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.service_configs.get(session.service, {}).get('name', 'Chat')} - Abelito OS</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .chat-container {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
        }}
        .message {{
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 12px;
            max-width: 80%;
        }}
        .message.user {{
            background: #007bff;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}
        .message.assistant {{
            background: white;
            color: #333;
            margin-right: auto;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .input-area {{
            background: white;
            padding: 20px;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 10px;
        }}
        .input-area input {{
            flex: 1;
            padding: 12px 20px;
            border: 1px solid #ddd;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
        }}
        .input-area input:focus {{
            border-color: #007bff;
        }}
        .input-area button {{
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
        }}
        .input-area button:hover {{
            background: #0056b3;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="chat-container" id="chatContainer">
        <div class="message assistant">
            Hello! I'm connected to {self.service_configs.get(session.service, {}).get('name', 'AI')}. 
            How can I help you today?
        </div>
    </div>
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        const sessionId = '{session.id}';
        const wsUrl = `ws://${{window.location.host}}/ws/chat/${{sessionId}}`;
        let ws;
        
        function connectWebSocket() {{
            ws = new WebSocket(wsUrl);
            ws.onopen = () => console.log('Connected');
            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                appendMessage(data.role, data.content);
            }};
            ws.onclose = () => setTimeout(connectWebSocket, 3000);
        }}
        
        function appendMessage(role, content) {{
            const container = document.getElementById('chatContainer');
            const div = document.createElement('div');
            div.className = `message ${{role}}`;
            div.textContent = content;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            appendMessage('user', message);
            ws.send(JSON.stringify({{ type: 'message', content: message }}));
            input.value = '';
        }}
        
        function handleKeyPress(event) {{
            if (event.key === 'Enter') sendMessage();
        }}
        
        connectWebSocket();
    </script>
</body>
</html>
"""


# FastAPI app for WebView chat
app = FastAPI(title="Abelito OS WebView Chat")
chat_manager = WebViewChatManager()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/chat/login/{service}", response_class=HTMLResponse)
async def login_page(service: str):
    """Show login WebView for a service."""
    session = chat_manager.create_session(service)
    return chat_manager.get_login_html(service, session.id)


@app.post("/chat/auth-complete/{session_id}")
async def auth_complete(session_id: str):
    """Mark session as authenticated."""
    session = chat_manager.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.authenticated = True
    chat_manager.save_session(session)
    
    return {"status": "authenticated", "session_id": session_id}


@app.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_page(session_id: str):
    """Show chat interface."""
    session = chat_manager.sessions.get(session_id)
    if not session:
        session = chat_manager.load_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return chat_manager.get_chat_interface_html(session)


@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time chat."""
    await websocket.accept()
    
    session = chat_manager.sessions.get(session_id)
    if not session:
        await websocket.close()
        return
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                message = data["content"]
                
                # Add to history
                session.message_history.append({"role": "user", "content": message})
                
                # Here would integrate with actual AI API
                # For now, echo response
                response = f"[{session.service}] Received: {message}"
                
                session.message_history.append({"role": "assistant", "content": response})
                
                await websocket.send_json({
                    "role": "assistant",
                    "content": response
                })
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


def main():
    """Run the WebView chat server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
