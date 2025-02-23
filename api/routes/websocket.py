from fastapi import APIRouter, Depends, WebSocket

from api.services.okx_service import OKXService
from api.services.websocket_service import WebSocketManager

router = APIRouter(prefix="/ws", tags=["WebSocket"])


def get_websocket_manager(okx_service: OKXService = Depends()):
    return WebSocketManager(okx_service)


@router.websocket("/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket,
    symbol: str,
    manager: WebSocketManager = Depends(get_websocket_manager),
):
    await manager.connect(websocket)
    try:
        await manager.subscribe_to_ticker(symbol)
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "received", "data": data})
    except:
        await manager.disconnect(websocket)
