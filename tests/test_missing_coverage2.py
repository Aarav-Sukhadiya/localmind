import sys
import pytest
import asyncio
import os
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from core.conversation import ConversationManager
from core.schemas import Message, Role
from tools.shell_tool import ShellTool
from tools.python_tool import PythonTool
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.asyncio
async def test_tool_exceptions():
    st = ShellTool()
    
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        with patch("asyncio.create_subprocess_shell") as m_exec:
            m_process = AsyncMock()
            m_process.kill = MagicMock(side_effect=ProcessLookupError())
            m_exec.return_value = m_process
            await st.execute("sleep 1", timeout=0.1)
            
    with patch("asyncio.create_subprocess_shell", side_effect=Exception("mocked")):
        await st.execute("sleep 1")

    pt = PythonTool()
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        with patch("asyncio.create_subprocess_exec") as m_exec:
            m_process = AsyncMock()
            m_process.kill = MagicMock(side_effect=ProcessLookupError())
            m_exec.return_value = m_process
            await pt.execute("sleep 1", timeout=0.1)
            
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("mocked")):
        await pt.execute("sleep 1")

@pytest.mark.asyncio
async def test_auto_compact_failure():
    mm = MagicMock()
    mm.short_term.get_messages.return_value = [
        Message(role=Role.SYSTEM, content="sys"),
        Message(role=Role.USER, content="1"),
        Message(role=Role.USER, content="2"),
        Message(role=Role.USER, content="3"),
        Message(role=Role.USER, content="4")
    ]
    llm = AsyncMock()
    llm.chat_completion.side_effect = Exception("failed")
    cm = ConversationManager(llm, MagicMock(), mm)
    await cm._auto_compact()

@pytest.mark.asyncio
async def test_tool_execution_failure():
    mm = MagicMock()
    mm.long_term = AsyncMock()
    mm.short_term.get_messages.return_value = [Message(role=Role.SYSTEM, content="sys")]
    llm = AsyncMock()
    
    # Return a message with a tool call
    from core.schemas import ToolCall, ToolCallFunction, LLMResponse, LLMChoice
    msg = Message(role=Role.ASSISTANT, tool_calls=[
        ToolCall(id="123", function=ToolCallFunction(name="test", arguments="{}"))
    ])
    
    llm.chat_completion.return_value = LLMResponse(choices=[LLMChoice(message=msg)])
    tr = AsyncMock()
    tr.list_tools.return_value = []
    tr.execute.side_effect = Exception("tool failed")
    
    cm = ConversationManager(llm, tr, mm)
    cm.max_tool_loops = 1
    
    async for event in cm.process_message("do it"):
        pass

