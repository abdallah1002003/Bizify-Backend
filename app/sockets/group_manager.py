import json
import logging
from typing import Dict, List
import uuid

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class GroupConnectionManager:
    """
    Manages active WebSocket connections for real-time group chat.
    Groups connections by group_id.
    """
    def __init__(self):
        # Dictionary mapping group_id to a dictionary of user_id -> WebSocket
        self.active_connections: Dict[uuid.UUID, Dict[uuid.UUID, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_id: uuid.UUID, user_id: uuid.UUID):
        await websocket.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = {}
        self.active_connections[group_id][user_id] = websocket
        logger.info(f"User {user_id} connected to group chat {group_id}")

    def disconnect(self, group_id: uuid.UUID, user_id: uuid.UUID):
        if group_id in self.active_connections:
            if user_id in self.active_connections[group_id]:
                del self.active_connections[group_id][user_id]
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
        logger.info(f"User {user_id} disconnected from group chat {group_id}")

    async def broadcast_to_group(self, group_id: uuid.UUID, message: dict):
        if group_id in self.active_connections:
            for user_id, connection in self.active_connections[group_id].items():
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to {user_id} in {group_id}: {e}")

group_manager = GroupConnectionManager()
