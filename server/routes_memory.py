from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/memory", tags=["memory"])

class MemoryCreate(BaseModel):
    content: str
    category: str = "general"

class MemoryUpdate(BaseModel):
    content: str

@router.get("")
async def list_memories(request: Request, category: str = None):
    mgr = request.app.state.memory_manager
    return await mgr.long_term.list_all(category)

@router.get("/search")
async def search_memories(request: Request, q: str):
    mgr = request.app.state.memory_manager
    return await mgr.long_term.search(q)

@router.get("/{id}")
async def get_memory(request: Request, id: int):
    mgr = request.app.state.memory_manager
    mem = await mgr.long_term.get(id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    return mem

@router.post("", status_code=201)
async def create_memory(request: Request, mem: MemoryCreate):
    mgr = request.app.state.memory_manager
    new_id = await mgr.long_term.save(mem.content, mem.category)
    return {"id": new_id}

@router.put("/{id}")
async def update_memory(request: Request, id: int, mem: MemoryUpdate):
    mgr = request.app.state.memory_manager
    success = await mgr.long_term.update(id, mem.content)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"success": True}

@router.delete("/{id}")
async def delete_memory(request: Request, id: int):
    mgr = request.app.state.memory_manager
    success = await mgr.long_term.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"success": True}
