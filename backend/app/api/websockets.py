from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import json
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.websocket import manager
from app.core.security import verify_token
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["websockets"])


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None,
) -> Optional[User]:
    """Get current user from WebSocket connection"""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    email = payload.get("sub")
    if not email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        return user
    except Exception as e:
        print(f"WebSocket auth error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    finally:
        db.close()


@router.websocket("/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Main WebSocket endpoint"""
    user = await get_current_user_ws(websocket, token)
    if not user:
        return

    await manager.connect(websocket, user.id)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Welcome {user.full_name}!",
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "watch_project":
                project_id = message.get("project_id")
                if project_id is not None:
                    await manager.watch_project(user.id, int(project_id))
                await websocket.send_json({
                    "type": "watching",
                    "project_id": project_id,
                })

            elif message.get("type") == "unwatch_project":
                project_id = message.get("project_id")
                if project_id is not None:
                    await manager.unwatch_project(user.id, int(project_id))
                await websocket.send_json({
                    "type": "unwatched",
                    "project_id": project_id,
                })

            elif message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
    except Exception as e:
        print(f"WebSocket error for user {user.id}: {e}")
        manager.disconnect(websocket, user.id)


@router.get("/online-users")
async def get_online_users():
    """Get list of currently online user IDs"""
    return {
        "online_users": manager.get_online_users(),
        "total_connections": manager.get_total_connections(),
    }