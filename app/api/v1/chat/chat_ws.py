from typing import List, Dict, Optional
from uuid import UUID
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.services.chat import chat_service
import jwt
from config.settings import settings
import app.models as models
from app.models.enums import ChatRole

from app.services.users.user_service import UserService, get_user_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # session_id -> list of active websockets
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: UUID):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: UUID):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, session_id: UUID):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)

manager = ConnectionManager()

async def get_user_from_token(token: str, user_service: UserService) -> Optional[models.User]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True}
        )
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            return None
        return await user_service.get_user(UUID(str(user_id_raw)))
    except jwt.ExpiredSignatureError:
        logger.warning("WS Token expired")
        return None
    except Exception as e:
        logger.error(f"FAILED TOKEN DECODE: {type(e).__name__} - {str(e)}")
        return None

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_async_db),
    user_service: UserService = Depends(get_user_service),
):
    user = await get_user_from_token(token, user_service)
    
    if not user:
        logger.warning(f"FAILED WS: User not found for token {token}. Payload parse result?")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify session ownership
    chat_session = await chat_service.get_chat_session(db, id=session_id)
    if not chat_session or chat_session.user_id != user.id:
        logger.warning(f"FAILED WS: Session issue. Session: {chat_session}. user_id: {user.id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, session_id)
    last_auth_check = 0.0
    auth_check_interval = 60.0 # Re-verify token every 60 seconds

    try:
        while True:
            # Periodic token validity check
            import time
            current_time = time.time()
            if current_time - last_auth_check > auth_check_interval:
                # Re-decode to check expiration without DB hit (cost-effective)
                try:
                    jwt.decode(
                        token,
                        settings.jwt_verify_key,
                        algorithms=[settings.jwt_algorithm],
                        options={"verify_exp": True}
                    )
                    last_auth_check = current_time
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                    logger.warning(f"WS session {session_id} token expired during active connection")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break

            # Use a timeout on receive to allow periodic auth checks
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            except asyncio.TimeoutError:
                continue

            try:
                message_data = json.loads(data)
                content = message_data.get("content")
            except json.JSONDecodeError:
                content = data

            if not content:
                continue

            # 1. Save User Message
            await chat_service.add_message(
                db, 
                session_id=session_id, 
                role=ChatRole.USER, 
                content=content
            )

            # 2. Mock AI Response (or real if implemented)
            ai_response_content = f"Echo from AI: {content}"
            
            await chat_service.add_message(
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
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(websocket, session_id)
