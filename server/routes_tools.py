from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["tools", "context", "system"])

class ToolExecRequest(BaseModel):
    arguments: dict

class PathRequest(BaseModel):
    path: str

@router.get("/tools")
async def list_tools(request: Request):
    return request.app.state.tool_registry.list_tools()

@router.post("/tools/{name}/execute")
async def execute_tool(request: Request, name: str, req: ToolExecRequest):
    return await request.app.state.tool_registry.execute(name, req.arguments)

@router.get("/context")
async def get_context(request: Request):
    return request.app.state.memory_manager.short_term.get_context_window_snapshot()

@router.get("/conversations")
async def list_conversations(request: Request):
    import os
    conv_dir = "data/conversations"
    os.makedirs(conv_dir, exist_ok=True)
    return os.listdir(conv_dir)

@router.post("/conversations/save")
async def save_conversation(request: Request, req: PathRequest):
    request.app.state.conversation_manager.save_conversation(req.path)
    return {"success": True}

@router.post("/conversations/load")
async def load_conversation(request: Request, req: PathRequest):
    request.app.state.conversation_manager.load_conversation(req.path)
    return {"success": True}

@router.post("/conversations/clear")
async def clear_conversation(request: Request):
    request.app.state.conversation_manager.clear_history()
    return {"success": True}

@router.get("/health")
async def health_check():
    return {"status": "ok"}
