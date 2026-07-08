import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
import os
from memory.token_counter import TokenCounter
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from core.schemas import Message, Role

def test_token_counter():
    tc = TokenCounter()
    assert tc.count("hello world") > 0
    assert tc.count("") == 0
    
    tc_approx = TokenCounter(method="approximate")
    assert tc_approx.count("abcd") == 1

@pytest.mark.asyncio
async def test_long_term_memory(tmp_path):
    db_path = str(tmp_path / "test.db")
    ltm = LongTermMemory(db_path)
    await ltm.initialize()
    
    id1 = await ltm.save("My favorite color is blue", "personal")
    assert id1 > 0
    
    memories = await ltm.search("blue")
    assert len(memories) == 1
    assert memories[0].id == id1
    
    await ltm.update(id1, "My favorite color is red")
    updated = await ltm.get(id1)
    assert "red" in updated.content
    
    await ltm.delete(id1)
    assert await ltm.get(id1) is None
    
    await ltm.close()

def test_short_term_memory():
    tc = TokenCounter(method="approximate")
    stm = ShortTermMemory(max_tokens=10, token_counter=tc)
    
    stm.add_message(Message(role=Role.SYSTEM, content="system prompt")) # ~3 tokens
    stm.add_message(Message(role=Role.USER, content="0123456789")) # ~2 tokens
    
    assert len(stm.messages) == 2
    stm.add_message(Message(role=Role.USER, content="0123456789012345678901234567890123456789")) # ~10 tokens -> forces prune
    
    # Prune should keep system prompt
    assert len(stm.messages) == 2
    assert stm.messages[0].role == Role.SYSTEM
    
    snap = stm.get_context_window_snapshot()
    assert snap.total_tokens <= 15
