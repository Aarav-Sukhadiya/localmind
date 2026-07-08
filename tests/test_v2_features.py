import sys
import pytest
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from core.llm_client import MultiplexLLMClient
from core.schemas import Message, Role, ToolDefinition
from unittest.mock import AsyncMock, MagicMock
from core.conversation import ConversationManager

@pytest.mark.asyncio
async def test_multiplex_llm():
    small = AsyncMock()
    small.model = "small"
    small.chat_completion.return_value = "small_resp"
    large = AsyncMock()
    large.model = "large"
    large.chat_completion.return_value = "large_resp"
    
    mpx = MultiplexLLMClient(small, large)
    
    # Simple query -> small
    res1 = await mpx.chat_completion([Message(role=Role.USER, content="hi")])
    assert res1 == "small_resp"
    
    # Tools -> large
    from core.schemas import ToolFunctionDefinition, ToolParameters
    tool_def = ToolDefinition(type="function", function=ToolFunctionDefinition(name="test", description="desc", parameters=ToolParameters(properties={})))
    res2 = await mpx.chat_completion([Message(role=Role.USER, content="hi")], tools=[tool_def])
    assert res2 == "large_resp"
    
    # Code -> large
    res3 = await mpx.chat_completion([Message(role=Role.USER, content="write python code")])
    assert res3 == "large_resp"

@pytest.mark.asyncio
async def test_auto_compact():
    llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "Summary"
    llm.chat_completion.return_value = mock_resp
    
    stm = MagicMock()
    msgs = [
        Message(role=Role.SYSTEM, content="sys"),
        Message(role=Role.USER, content="u1"),
        Message(role=Role.ASSISTANT, content="a1"),
        Message(role=Role.USER, content="u2"),
        Message(role=Role.ASSISTANT, content="a2")
    ]
    stm.get_messages.return_value = msgs
    
    mm = MagicMock()
    mm.short_term = stm
    
    cm = ConversationManager(llm, MagicMock(), mm)
    await cm._auto_compact()
    
    stm.messages = mm.short_term.messages
    assert len(stm.messages) == 4
    assert stm.messages[1].content == "[Prior Context Summary]: Summary"

@pytest.mark.asyncio
async def test_auto_compact_too_short():
    mm = MagicMock()
    mm.short_term.get_messages.return_value = [Message(role=Role.SYSTEM, content="sys")]
    cm = ConversationManager(MagicMock(), MagicMock(), mm)
    await cm._auto_compact()
    assert not mm.short_term.clear.called
