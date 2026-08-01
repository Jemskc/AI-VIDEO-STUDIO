from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Optional
import json
import asyncio

from app.core.security import decode_token

router = APIRouter()


async def _authenticate(websocket: WebSocket, token: Optional[str]) -> Optional[int]:
    """
    Resolve the user id from a JWT passed as a query param, since browsers
    can't set an Authorization header on the WebSocket upgrade request.
    Closes the connection and returns None if the token is missing/invalid.
    """
    payload = decode_token(token) if token else None
    user_id = payload.get("sub") if payload else None

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    return int(user_id)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection might be closed
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for real-time updates. Requires ?token=<JWT>."""
    user_id = await _authenticate(websocket, token)
    if user_id is None:
        return

    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Successfully connected to WebSocket"
        })
        
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await websocket.receive_text()
                
                # Handle incoming messages (e.g., subscribe to specific events)
                message = json.loads(data)
                
                if message.get("action") == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": message.get("channels", [])
                    })
                elif message.get("action") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)
        raise


@router.websocket("/ws/jobs")
async def jobs_websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint specifically for render job updates. Requires ?token=<JWT>."""
    user_id = await _authenticate(websocket, token)
    if user_id is None:
        return

    await manager.connect(websocket, user_id)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "jobs",
            "message": "Connected to job updates channel"
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("action") == "subscribe_job":
                    job_id = message.get("job_id")
                    await websocket.send_json({
                        "type": "subscribed",
                        "job_id": job_id
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)
        raise


async def notify_job_update(job_id: int, status: str, progress: int, user_id: int = None):
    """Helper function to notify about job updates."""
    message = {
        "type": "job_update",
        "job_id": job_id,
        "status": status,
        "progress": progress
    }
    
    if user_id:
        await manager.send_personal_message(message, user_id)
    else:
        await manager.broadcast(message)


async def notify_render_complete(job_id: int, output_url: str, user_id: int = None):
    """Helper function to notify about render completion."""
    message = {
        "type": "render_complete",
        "job_id": job_id,
        "output_url": output_url
    }
    
    if user_id:
        await manager.send_personal_message(message, user_id)
    else:
        await manager.broadcast(message)
