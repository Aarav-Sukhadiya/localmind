import sys
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
import pytest
from core.llm_client import LLMClient
from core.schemas import Message, Role, ToolDefinition, LLMConnectionError
import httpx

@pytest.mark.asyncio
async def test_chat_completion_success(respx_mock):
    client = LLMClient("http://mock", "test-model")
    respx_mock.post("http://mock/chat/completions").mock(return_value=httpx.Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": "hello"}}]
    }))
    resp = await client.chat_completion([Message(role=Role.USER, content="hi")])
    assert resp.choices[0].message.content == "hello"

@pytest.mark.asyncio
async def test_chat_completion_connection_error(respx_mock):
    client = LLMClient("http://mock", "test-model")
    respx_mock.post("http://mock/chat/completions").mock(side_effect=httpx.ConnectError("offline"))
    with pytest.raises(LLMConnectionError):
        await client.chat_completion([Message(role=Role.USER, content="hi")])

@pytest.mark.asyncio
async def test_chat_completion_http_error(respx_mock):
    client = LLMClient("http://mock", "test-model")
    respx_mock.post("http://mock/chat/completions").mock(return_value=httpx.Response(500, text="error"))
    with pytest.raises(LLMConnectionError):
        await client.chat_completion([Message(role=Role.USER, content="hi")])

@pytest.mark.asyncio
async def test_chat_completion_invalid_format(respx_mock):
    client = LLMClient("http://mock", "test-model")
    respx_mock.post("http://mock/chat/completions").mock(return_value=httpx.Response(200, json={"bad": "data"}))
    with pytest.raises(ValueError):
        await client.chat_completion([Message(role=Role.USER, content="hi")])

@pytest.mark.asyncio
async def test_chat_completion_stream(respx_mock):
    client = LLMClient("http://mock", "test-model")
    stream_content = b'data: {"choices": [{"delta": {"content": "hel"}}]}\n\ndata: {"choices": [{"delta": {"content": "lo"}}]}\n\ndata: [DONE]\n\n'
    respx_mock.post("http://mock/chat/completions").mock(return_value=httpx.Response(200, content=stream_content))
    chunks = []
    async for chunk in await client.chat_completion([Message(role=Role.USER, content="hi")], stream=True):
        chunks.append(chunk.choices[0].delta.content)
    assert chunks == ["hel", "lo"]

@pytest.mark.asyncio
async def test_chat_completion_tool_call(respx_mock):
    client = LLMClient("http://mock", "test-model")
    respx_mock.post("http://mock/chat/completions").mock(return_value=httpx.Response(200, json={
        "choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "1", "type": "function", "function": {"name": "test", "arguments": "{}"}}]}}]
    }))
    resp = await client.chat_completion([Message(role=Role.USER, content="hi")])
    assert resp.choices[0].message.tool_calls[0].function.name == "test"
