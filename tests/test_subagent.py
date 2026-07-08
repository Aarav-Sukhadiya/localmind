import sys
import pytest
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from tools.subagent_tool import SubagentTool
from unittest.mock import AsyncMock, MagicMock
from core.schemas import Message, Role, Event

@pytest.mark.asyncio
async def test_subagent_tool_success():
    mock_cm = MagicMock()
    mock_cm.memory_manager.short_term = MagicMock()
    
    async def mock_process(task):
        yield Event(type="thinking", data={})
        
    mock_cm.process_message = mock_process
    mock_cm.get_history.return_value = [Message(role=Role.ASSISTANT, content="Subagent result")]
    
    def factory():
        return mock_cm
        
    tool = SubagentTool(factory)
    res = await tool.execute(role="test", task="do this")
    assert res.success == True
    assert "Subagent result" in res.output

@pytest.mark.asyncio
async def test_subagent_tool_no_response():
    mock_cm = MagicMock()
    mock_cm.memory_manager.short_term = MagicMock()
    
    async def mock_process(task):
        yield Event(type="thinking", data={})
        
    mock_cm.process_message = mock_process
    mock_cm.get_history.return_value = [Message(role=Role.USER, content="hi")]
    
    def factory():
        return mock_cm
        
    tool = SubagentTool(factory)
    res = await tool.execute(role="test", task="do this")
    assert res.success == False
    assert "did not return" in res.error

@pytest.mark.asyncio
async def test_subagent_tool_exception():
    def factory():
        raise ValueError("crash")
    tool = SubagentTool(factory)
    res = await tool.execute(role="test", task="do this")
    assert res.success == False
    assert "crash" in res.error
