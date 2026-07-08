import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_app():
    app = create_app()
    app.state.memory_manager = MagicMock()
    app.state.memory_manager.long_term = AsyncMock()
    app.state.memory_manager.short_term = MagicMock()
    app.state.tool_registry = MagicMock()
    app.state.conversation_manager = MagicMock()
    return app

@pytest.fixture
def client(mock_app):
    return TestClient(mock_app)

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_list_tools(client, mock_app):
    mock_app.state.tool_registry.list_tools.return_value = [{"name": "test"}]
    res = client.get("/api/tools")
    assert res.json() == [{"name": "test"}]

def test_context(client, mock_app):
    mock_app.state.memory_manager.short_term.get_context_window_snapshot.return_value = {"total_tokens": 10}
    res = client.get("/api/context")
    assert res.json() == {"total_tokens": 10}

@pytest.mark.asyncio
async def test_memory_routes(client, mock_app):
    # Mocking for standard async handlers in testclient is a bit tricky, 
    # but since TestClient handles the async loop we can just set return values.
    mock_app.state.memory_manager.long_term.save.return_value = 1
    res = client.post("/api/memory", json={"content": "hello", "category": "test"})
    assert res.status_code == 201
    assert res.json() == {"id": 1}
    
    mock_app.state.memory_manager.long_term.list_all.return_value = [{"id": 1, "content": "hello"}]
    res = client.get("/api/memory")
    assert res.status_code == 200
    assert len(res.json()) == 1
    
    mock_app.state.memory_manager.long_term.delete.return_value = True
    res = client.delete("/api/memory/1")
    assert res.status_code == 200
