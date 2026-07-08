from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_state = websocket.app.state
    mgr = app_state.conversation_manager
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_text = msg.get("message", "")
            
            async for event in mgr.process_message(user_text):
                await websocket.send_json(event.model_dump())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "data": {"error": str(e)}})
