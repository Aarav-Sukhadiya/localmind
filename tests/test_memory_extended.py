import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
from memory.token_counter import TokenCounter
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from core.schemas import Message, Role

def test_token_counter_fallback():
    # If a fake model is provided, it falls back to cl100k_base
    tc = TokenCounter(model="fake-model")
    assert tc.count("hello") > 0

    tc2 = TokenCounter(method="approximate")
    assert tc2.count_messages([Message(role=Role.USER, content="test")]) > 0

@pytest.mark.asyncio
async def test_long_term_extended(tmp_path):
    db_path = str(tmp_path / "test.db")
    ltm = LongTermMemory(db_path)
    await ltm.initialize()

    # Empty search / get relevant context
    ctx = await ltm.get_relevant_context("query")
    assert "No relevant" in ctx
    
    ctx_empty = await ltm.get_relevant_context("")
    assert "No relevant" in ctx_empty

    # Get non existent
    assert await ltm.get(999) is None

    # Delete non existent
    assert await ltm.delete(999) is False

    # List category
    await ltm.save("dev task", "work")
    await ltm.save("buy milk", "personal")
    res = await ltm.list_all("work")
    assert len(res) == 1
    assert res[0].category == "work"
    
    # get_relevant context match
    ctx_match = await ltm.get_relevant_context("dev")
    assert "dev task" in ctx_match

    await ltm.close()

def test_short_term_extended():
    tc = TokenCounter(method="approximate")
    stm = ShortTermMemory(max_tokens=10, token_counter=tc)
    
    stm.clear()
    assert len(stm.get_messages()) == 0

    # Test edge case: adding multiple large messages
    stm.add_message(Message(role=Role.USER, content="A" * 100))
    # It should prune, but keep at least 1 message if it's the only one
    # Wait, the prune logic says `while ... and len(self.messages) > 1:`
    assert len(stm.get_messages()) == 1

    # Adding another pushes the first one out
    stm.add_message(Message(role=Role.USER, content="B" * 100))
    assert len(stm.get_messages()) == 1
    assert "B" in stm.get_messages()[0].content
