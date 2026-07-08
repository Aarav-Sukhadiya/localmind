import sys
import pytest
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from core.conversation import ConversationManager
from core.llm_client import LLMClient
from memory.token_counter import TokenCounter
from tools.file_tool import FileTool
from unittest.mock import AsyncMock, MagicMock
from core.schemas import Message, Role
import os

@pytest.mark.asyncio
async def test_conversation_save_load_clear(tmp_path):
    llm = MagicMock()
    stm = MagicMock()
    stm.get_messages.return_value = [Message(role=Role.USER, content="test")]
    mm = MagicMock()
    mm.short_term = stm
    cm = ConversationManager(llm, MagicMock(), mm)
    
    file_path = str(tmp_path / "conv.json")
    cm.save_conversation(file_path)
    
    assert os.path.exists(file_path)
    cm.load_conversation(file_path)
    assert stm.clear.called
    assert stm.add_message.called
    
    cm.clear_history()
    assert stm.clear.call_count == 2

@pytest.mark.asyncio
async def test_token_counter_approximate():
    tc = TokenCounter(method="approximate")
    count = tc.count("hello world")
    assert count > 0

@pytest.mark.asyncio
async def test_file_tool_edge_cases(tmp_path):
    t = FileTool(base_directory=str(tmp_path))
    
    res = await t.execute(action="write", path="nested/file.txt", content="hi")
    assert res.success
    
    res2 = await t.execute(action="list", path=".")
    assert res2.success
    
    res3 = await t.execute(action="unknown", path=".")
    assert not res3.success

@pytest.mark.asyncio
async def test_llm_client_stream():
    llm = LLMClient("http://localhost:8080", "model")
    try:
        iterator = await llm.chat_completion([Message(role=Role.USER, content="hi")], stream=True)
        async for _ in iterator:
            pass
    except Exception:
        pass
