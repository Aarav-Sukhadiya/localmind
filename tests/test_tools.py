import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
import os
import tempfile
from tools.registry import ToolRegistry, BaseTool
from core.schemas import ToolResult
from tools.shell_tool import ShellTool
from tools.python_tool import PythonTool
from tools.file_tool import FileTool
from tools.search_tool import SearchTool
from tools.memory_tool import MemoryTool
from unittest.mock import AsyncMock, patch, MagicMock

# Registry Tests
class DummyTool(BaseTool):
    name = "dummy"
    description = "desc"
    parameters = {"properties": {}, "required": []}
    async def execute(self, **kwargs): return ToolResult(success=True, output="ok")

def test_registry():
    reg = ToolRegistry()
    reg.register(DummyTool())
    assert reg.get_tool("dummy").name == "dummy"
    assert len(reg.list_tools()) == 1

@pytest.mark.asyncio
async def test_registry_exec():
    reg = ToolRegistry()
    reg.register(DummyTool())
    res = await reg.execute("dummy", {})
    assert res.output == "ok"
    res2 = await reg.execute("missing", {})
    assert res2.success == False

# Shell Tests
@pytest.mark.asyncio
async def test_shell_basic():
    tool = ShellTool()
    res = await tool.execute("echo hello")
    assert "hello" in res.output
    assert res.success == True

@pytest.mark.asyncio
async def test_shell_blocked():
    tool = ShellTool()
    res = await tool.execute("rm -rf /")
    assert res.success == False
    assert "blocked" in res.error

@pytest.mark.asyncio
async def test_shell_timeout():
    tool = ShellTool()
    res = await tool.execute("sleep 2", timeout=1)
    assert res.success == False
    assert "timed out" in res.error

# Python Tests
@pytest.mark.asyncio
async def test_python_basic():
    tool = PythonTool()
    res = await tool.execute("print('hello')")
    assert "hello" in res.output
    assert res.success == True

@pytest.mark.asyncio
async def test_python_error():
    tool = PythonTool()
    res = await tool.execute("1/0")
    assert res.success == False
    assert "ZeroDivisionError" in res.output

# File Tests
@pytest.mark.asyncio
async def test_file_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileTool(base_directory=tmpdir)
        
        res = await tool.execute("write", "test.txt", "hello")
        assert res.success == True
        
        res = await tool.execute("read", "test.txt")
        assert res.output == "hello"
        
        res = await tool.execute("append", "test.txt", " world")
        assert res.success == True
        
        res = await tool.execute("read", "test.txt")
        assert res.output == "hello world"
        
        res = await tool.execute("exists", "test.txt")
        assert res.output == "True"
        
        res = await tool.execute("delete", "test.txt")
        assert res.success == True
        
        res = await tool.execute("read", "test.txt")
        assert res.success == False

@pytest.mark.asyncio
async def test_file_traversal():
    tool = FileTool(base_directory="/tmp/localmind_test")
    res = await tool.execute("read", "../../../etc/passwd")
    assert res.success == False
    assert "traversal" in res.error.lower()

# Search Tests
@pytest.mark.asyncio
async def test_search_empty():
    tool = SearchTool()
    res = await tool.execute("")
    assert res.success == False

@pytest.mark.asyncio
@patch('tools.search_tool.DDGS')
async def test_search_mocked(mock_ddgs):
    mock_inst = MagicMock()
    mock_inst.__enter__.return_value = mock_inst
    mock_inst.text.return_value = [{"title": "t", "href": "url", "body": "snip"}]
    mock_ddgs.return_value = mock_inst
    
    tool = SearchTool()
    res = await tool.execute("test")
    assert "url" in res.output

# Memory Tests
@pytest.mark.asyncio
async def test_memory_tool():
    ltm = AsyncMock()
    ltm.save.return_value = 1
    ltm.search.return_value = []
    ltm.list_all.return_value = []
    ltm.delete.return_value = True
    ltm.update.return_value = True
    
    tool = MemoryTool(ltm)
    res = await tool.execute("save", content="hi")
    assert res.success == True
    
    res = await tool.execute("search", query="hi")
    assert res.success == True
