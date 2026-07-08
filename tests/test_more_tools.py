import sys
import pytest
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from tools.shell_tool import ShellTool
from tools.python_tool import PythonTool
from tools.memory_tool import MemoryTool
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_shell_tool_errors():
    t = ShellTool(blocked_commands=["rm"])
    res = await t.execute(command="rm -rf /")
    assert res.success == False
    
    res2 = await t.execute(command="thiscmd_doesnotexist")
    assert res2.success == False

@pytest.mark.asyncio
async def test_python_tool_timeout():
    t = PythonTool()
    res = await t.execute(code="import time; time.sleep(1)", timeout=0.1)
    assert res.success == False
    assert "timed out" in res.error.lower()

@pytest.mark.asyncio
async def test_memory_tool_errors():
    ltm = AsyncMock()
    t = MemoryTool(ltm)
    
    ltm.search.side_effect = Exception("db error")
    res = await t.execute("search", query="x")
    assert res.success == False
    
    res2 = await t.execute("search")
    assert res2.success == False

from fastapi.testclient import TestClient
from server.app import create_app

def test_install_custom_tool():
    app = create_app()
    app.state.tool_registry = MagicMock()
    client = TestClient(app)
    
    code = """
from tools.registry import BaseTool, ToolResult
class MyTool(BaseTool):
    @property
    def name(self): return "mytool"
    @property
    def description(self): return "desc"
    @property
    def parameters(self): return {}
    async def execute(self, **kwargs): return ToolResult(success=True, output="ok")
"""
    res = client.post("/api/tools/custom/install", json={"name": "my_test_tool", "code": code})
    assert res.status_code == 200
    assert res.json()["success"] == True
    
    res_bad = client.post("/api/tools/custom/install", json={"name": "bad_tool", "code": "print('hello')"})
    assert res_bad.status_code == 200
    assert res_bad.json()["success"] == False
