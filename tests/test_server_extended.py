import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from unittest.mock import MagicMock, AsyncMock
from fastapi.websockets import WebSocketDisconnect

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
    return TestClient(mock_app, raise_server_exceptions=False)

def test_routes_memory_errors(client, mock_app):
    mock_app.state.memory_manager.long_term.get.return_value = None
    res = client.get("/api/memory/999")
    assert res.status_code == 404
    
    mock_app.state.memory_manager.long_term.update.return_value = False
    res = client.put("/api/memory/999", json={"content": "test"})
    assert res.status_code == 404

    mock_app.state.memory_manager.long_term.delete.return_value = False
    res = client.delete("/api/memory/999")
    assert res.status_code == 404
    
def test_routes_memory_search(client, mock_app):
    mock_app.state.memory_manager.long_term.search.return_value = [{"id": 1, "content": "found"}]
    res = client.get("/api/memory/search?q=test")
    assert res.status_code == 200
    assert res.json()[0]["content"] == "found"

def test_routes_memory_list_category(client, mock_app):
    mock_app.state.memory_manager.long_term.list_all.return_value = []
    res = client.get("/api/memory?category=work")
    assert res.status_code == 200
    mock_app.state.memory_manager.long_term.list_all.assert_called_with("work")

def test_routes_tools_conversations(client, mock_app):
    res = client.get("/api/conversations")
    assert res.status_code == 200

    res = client.post("/api/conversations/save", json={"path": "test.json"})
    assert res.status_code == 200
    mock_app.state.conversation_manager.save_conversation.assert_called_with("test.json")

    res = client.post("/api/conversations/load", json={"path": "test.json"})
    assert res.status_code == 200
    mock_app.state.conversation_manager.load_conversation.assert_called_with("test.json")

    res = client.post("/api/conversations/clear")
    assert res.status_code == 200
    mock_app.state.conversation_manager.clear_history.assert_called()

def test_routes_tools_execute(client, mock_app):
    mock_app.state.tool_registry.execute = AsyncMock(return_value={"success": True, "output": "done"})
    res = client.post("/api/tools/shell/execute", json={"arguments": {"command": "echo 1"}})
    assert res.status_code == 200

def test_websocket_chat(client, mock_app):
    # Mock conversation manager to yield an event
    from core.schemas import Event
    
    async def mock_process(msg):
        yield Event(type="response_chunk", data={"content": "hello"})
        
    mock_app.state.conversation_manager.process_message = mock_process
    
    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "hi"})
        data = websocket.receive_json()
        assert data["type"] == "response_chunk"

    # Testing disconnect gracefully is handled implicitly by fastAPI testclient when closing context

def test_websocket_chat_error(client, mock_app):
    async def mock_process(msg):
        raise Exception("test error")
        yield
        
    mock_app.state.conversation_manager.process_message = mock_process
    
    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "hi"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "test error" in data["data"]["error"]

def test_routes_memory_internal_errors(client, mock_app):
    mock_app.state.memory_manager.long_term.save.side_effect = Exception("save error")
    res = client.post("/api/memory", json={"content": "test"})
    assert res.status_code == 500

    mock_app.state.memory_manager.long_term.list_all.side_effect = Exception("list error")
    res = client.get("/api/memory")
    assert res.status_code == 500
