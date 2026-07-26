from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.core.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    device_token = websocket.query_params.get("device_token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    if not payload or payload.get("type") != "access":
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")

    await manager.connect(user_id, websocket)

    if device_token:
        manager.register_device_token(user_id, device_token)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)