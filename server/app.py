from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from server.routes_chat import router as chat_router
from server.routes_memory import router as memory_router
from server.routes_tools import router as tools_router

def create_app(config: dict = None) -> FastAPI:
    app = FastAPI(title="LocalMind API")
    app.state.config = config or {}
    
    app.include_router(chat_router)
    app.include_router(memory_router)
    app.include_router(tools_router)
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/")
    async def get_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
        
    return app
