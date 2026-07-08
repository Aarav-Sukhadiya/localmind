import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
import os
import tempfile
from tools.file_tool import FileTool
from tools.memory_tool import MemoryTool
from tools.search_tool import SearchTool
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_file_tool_extended():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileTool(base_directory=tmpdir)
        
        # Test mkdir
        res = await tool.execute("mkdir", "new_folder")
        assert res.success == True
        assert os.path.isdir(os.path.join(tmpdir, "new_folder"))

        # Test list on empty dir
        res = await tool.execute("list", "new_folder")
        assert res.success == True
        assert "empty" in res.output

        # Test list on file
        await tool.execute("write", "test.txt", "data")
        res = await tool.execute("list", "test.txt")
        assert res.success == False

        # Test copy and move
        res = await tool.execute("copy", "test.txt", destination="test2.txt")
        assert res.success == True
        assert os.path.exists(os.path.join(tmpdir, "test2.txt"))

        res = await tool.execute("move", "test2.txt", destination="test3.txt")
        assert res.success == True
        assert not os.path.exists(os.path.join(tmpdir, "test2.txt"))
        assert os.path.exists(os.path.join(tmpdir, "test3.txt"))

        # Test unknown action
        res = await tool.execute("fake", "test.txt")
        assert res.success == False

@pytest.mark.asyncio
async def test_memory_tool_extended():
    ltm = AsyncMock()
    tool = MemoryTool(ltm)

    # Missing arguments
    res = await tool.execute("save")
    assert res.success == False
    assert "required" in res.error

    res = await tool.execute("update")
    assert res.success == False

    res = await tool.execute("delete")
    assert res.success == False
    
    # Not found on update/delete
    ltm.update.return_value = False
    res = await tool.execute("update", memory_id=1, content="x")
    assert res.success == False

    ltm.delete.return_value = False
    res = await tool.execute("delete", memory_id=1)
    assert res.success == False

@pytest.mark.asyncio
@patch('tools.search_tool.DDGS')
async def test_search_tool_extended(mock_ddgs):
    # Test exception handling
    mock_ddgs.side_effect = Exception("network down")
    tool = SearchTool()
    res = await tool.execute("test")
    assert res.success == False
    assert "network down" in res.error

    # Test empty results
    mock_inst = AsyncMock()
    mock_inst.__enter__.return_value = mock_inst
    mock_inst.text.return_value = []
    mock_ddgs.return_value = mock_inst
    res = await tool.execute("asdfghjkl")
    # if it doesn't crash it returns "No results found"
    assert "No results" in res.output or res.success == False
