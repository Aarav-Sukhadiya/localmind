import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, MagicMock
from core.conversation import ConversationManager
from core.schemas import Message, Role, ToolResult, ToolCall, ToolCallFunction

@pytest.fixture
def mocks():
    llm = AsyncMock()
    reg = MagicMock()
    mem = MagicMock()
    mem.long_term = AsyncMock()
    mem.short_term = MagicMock()
    mem.long_term.get_relevant_context.return_value = "memory"
    
    # Track messages
    msgs = []
    def add_msg(m): msgs.append(m)
    def get_msgs(): return msgs
    def clear(): msgs.clear()
    
    mem.short_term.add_message = add_msg
    mem.short_term.get_messages = get_msgs
    mem.short_term.clear = clear
    return llm, reg, mem

@pytest.mark.asyncio
async def test_simple_message(mocks):
    llm, reg, mem = mocks
    llm.chat_completion.return_value = MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, content="hello"))])
    mgr = ConversationManager(llm, reg, mem)
    
    events = [e async for e in mgr.process_message("hi")]
    assert any(e.type == "response_chunk" and e.data["content"] == "hello" for e in events)
    assert any(e.type == "done" for e in events)

@pytest.mark.asyncio
async def test_tool_call(mocks):
    llm, reg, mem = mocks
    tool_call = ToolCall(id="1", type="function", function=ToolCallFunction(name="test", arguments="{}"))
    llm.chat_completion.side_effect = [
        MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, tool_calls=[tool_call], content=None))]),
        MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, content="done"))])
    ]
    
    async def mock_exec(name, args):
        return ToolResult(success=True, output="result")
    reg.execute = mock_exec
    
    mgr = ConversationManager(llm, reg, mem)
    events = [e async for e in mgr.process_message("do something")]
    assert any(e.type == "tool_call" for e in events)
    assert any(e.type == "tool_result" and e.data["result"] == "result" for e in events)

@pytest.mark.asyncio
async def test_max_loops(mocks):
    llm, reg, mem = mocks
    tool_call = ToolCall(id="1", type="function", function=ToolCallFunction(name="test", arguments="{}"))
    llm.chat_completion.return_value = MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, tool_calls=[tool_call], content=None))])
    
    async def mock_exec(name, args):
        return ToolResult(success=True, output="result")
    reg.execute = mock_exec
    
    mgr = ConversationManager(llm, reg, mem)
    mgr.max_tool_loops = 3
    events = [e async for e in mgr.process_message("loop")]
    assert any(e.type == "error" and "Max tool loop iterations reached" in e.data["error"] for e in events)

@pytest.mark.asyncio
async def test_tool_error(mocks):
    llm, reg, mem = mocks
    tool_call = ToolCall(id="1", type="function", function=ToolCallFunction(name="test", arguments="{}"))
    llm.chat_completion.side_effect = [
        MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, tool_calls=[tool_call], content=None))]),
        MagicMock(choices=[MagicMock(message=Message(role=Role.ASSISTANT, content="handled error"))])
    ]
    
    async def mock_exec(name, args):
        return ToolResult(success=False, output="", error="fail")
    reg.execute = mock_exec
    
    mgr = ConversationManager(llm, reg, mem)
    events = [e async for e in mgr.process_message("do it")]
    assert any(e.type == "tool_result" and "Error: fail" in e.data["result"] for e in events)

@pytest.mark.asyncio
async def test_save_load(mocks):
    llm, reg, mem = mocks
    mgr = ConversationManager(llm, reg, mem)
    mem.short_term.add_message(Message(role=Role.USER, content="hi"))
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
        
    try:
        mgr.save_conversation(path)
        mgr.clear_history()
        assert len(mgr.get_history()) == 0
        mgr.load_conversation(path)
        assert len(mgr.get_history()) == 1
        assert mgr.get_history()[0].content == "hi"
    finally:
        os.remove(path)

@pytest.mark.asyncio
async def test_clear(mocks):
    llm, reg, mem = mocks
    mgr = ConversationManager(llm, reg, mem)
    mem.short_term.add_message(Message(role=Role.USER, content="hi"))
    mgr.clear_history()
    assert len(mgr.get_history()) == 0
    
@pytest.mark.asyncio
async def test_llm_error(mocks):
    llm, reg, mem = mocks
    llm.chat_completion.side_effect = Exception("offline")
    mgr = ConversationManager(llm, reg, mem)
    
    events = [e async for e in mgr.process_message("hi")]
    assert any(e.type == "error" and e.data["error"] == "offline" for e in events)
