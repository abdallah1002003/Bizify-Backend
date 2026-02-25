from typing import List, Dict
from uuid import UUID
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.chat import chat_service
import jwt
from config.settings import settings
import app.models as models
from app.models.enums import ChatRole

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):  # type: ignore
        # session_id -> list of active websockets
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: UUID):  # type: ignore
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: UUID):  # type: ignore
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):  # type: ignore
        await websocket.send_text(message)

    async def broadcast(self, message: str, session_id: UUID):  # type: ignore
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)

manager = ConnectionManager()

async def get_user_from_token(token: str, db: Session) -> models.User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None  # type: ignore
        return db.query(models.User).filter(models.User.id == user_id).first()  # type: ignore
    except Exception as e:
        logger.error(f"FAILED TOKEN DECODE: {type(e).__name__} - {str(e)}")
        return None  # type: ignore

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(  # type: ignore
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    user = await get_user_from_token(token, db)
    
    if not user:
        logger.warning(f"FAILED WS: User not found for token {token}. Payload parse result?")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify session ownership
    chat_session = chat_service.get_chat_session(db, id=session_id)
    if not chat_session or chat_session.user_id != user.id:
        logger.warning(f"FAILED WS: Session issue. Session: {chat_session}. user_id: {user.id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                content = message_data.get("content")
            except json.JSONDecodeError:
                content = data

            if not content:
                continue

            # 1. Save User Message
            chat_service.add_message(
                db, 
                session_id=session_id, 
                role=ChatRole.USER, 
                content=content
            )

            # 2. Mock AI Response (for now, or hook into real AI service later)
            # In a real app, you'd call an LLM here.
            ai_response_content = f"Echo from AI: {content}"
            
            chat_service.add_message(
                db,
                session_id=session_id,
                role=ChatRole.AI,
                content=ai_response_content
            )

            # 3. Broadcast to all connections in this session
            response_payload = {
                "role": ChatRole.AI.value,
                "content": ai_response_content,
                "session_id": str(session_id)
            }
            await manager.broadcast(json.dumps(response_payload), session_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
