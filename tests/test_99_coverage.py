import sys
import pytest
import httpx
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")

from core.conversation import ConversationManager
from core.llm_client import LLMClient
from server.app import create_app
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_llm_client_exceptions():
    llm = LLMClient("http://localhost", "m")
    
    mock_req = MagicMock()
    with patch("httpx.AsyncClient.post", side_effect=httpx.RequestError("error", request=mock_req)):
        with pytest.raises(Exception):
            await llm.chat_completion([])
            
        with pytest.raises(Exception):
            async for _ in await llm.chat_completion([], stream=True):
                pass

@pytest.mark.asyncio
async def test_conversation_compaction_trigger():
    mm = MagicMock()
    mm.short_term = MagicMock()
    mm.short_term.get_context_window_snapshot.return_value = MagicMock(usage_percent=90.0)
    
    from core.schemas import Message, Role
    mm.short_term.get_messages.return_value = [Message(role=Role.SYSTEM, content="sys")]
    
    mm.long_term = AsyncMock()
    mm.long_term.get_relevant_context.return_value = ""
    
    llm = AsyncMock()
    from core.schemas import LLMResponse, LLMChoice
    llm.chat_completion.return_value = LLMResponse(choices=[LLMChoice(message=Message(role=Role.ASSISTANT, content="hey"))])
    
    cm = ConversationManager(llm, MagicMock(), mm)
    cm.prune_strategy = 'compact'
    cm.max_tool_loops = 1
    
    async for event in cm.process_message("test"):
        pass

def test_app_index_and_unhandled_exception():
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    
    # Hit index
    res = client.get("/")
    assert res.status_code == 200
    
    # Mock importlib to test custom tool exception
    with patch("importlib.util.spec_from_file_location", side_effect=Exception("import err")):
        res = client.post("/api/tools/custom/install", json={"name": "test", "code": "pass"})
        assert res.status_code == 200
        assert not res.json()["success"]

def test_routes_memory_success_paths():
    app = create_app()
    
    class DummyLTM:
        async def get(self, id):
            return {"id": id, "content": "c"}
        async def update(self, id, c):
            return True
            
    app.state.memory_manager = MagicMock()
    app.state.memory_manager.long_term = DummyLTM()
    
    client = TestClient(app)
    res = client.get("/api/memory/1")
    assert res.status_code == 200
    
    res = client.put("/api/memory/1", json={"content": "new"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_long_term_sql_exceptions():
    from memory.long_term import LongTermMemory
    ltm = LongTermMemory(":memory:")
    await ltm.initialize()
    await ltm.list_all()
    res = await ltm.get_relevant_context("*")
    assert "No relevant" in res
    await ltm.close()

@pytest.mark.asyncio
async def test_long_term_chroma_exceptions():
    from memory.long_term_chroma import LongTermMemoryChroma
    ltm = LongTermMemoryChroma("/tmp/test_chroma_dummy")
    await ltm.initialize()
    res = await ltm.get_relevant_context("query")
    assert "No relevant" in res
    with patch.object(ltm, "search", side_effect=Exception("error")):
        res = await ltm.get_relevant_context("query")
        assert "No relevant" in res

@pytest.mark.asyncio
async def test_file_tool_binary_and_copytree(tmp_path):
    from tools.file_tool import FileTool
    ft = FileTool(str(tmp_path))
    bin_file = tmp_path / "bin.dat"
    bin_file.write_bytes(b"\0\1\2")
    res = await ft.execute("read", "bin.dat")
    assert res.success
    assert "Binary file" in res.output
    d = tmp_path / "src_dir"
    d.mkdir()
    (d / "f.txt").write_text("hello")
    res = await ft.execute("copy", "src_dir", destination="dst_dir")
    assert res.success
    assert (tmp_path / "dst_dir" / "f.txt").exists()

@pytest.mark.asyncio
async def test_memory_tool_missing_args():
    from tools.memory_tool import MemoryTool
    mt = MemoryTool(AsyncMock())
    res1 = await mt.execute("update", content="test")
    assert not res1.success
    res2 = await mt.execute("delete")
    assert not res2.success

@pytest.mark.asyncio
async def test_base_tool():
    from tools.registry import BaseTool
    class DummyTool(BaseTool):
        name="d"
        description="d"
        parameters={}
        async def execute(self, **kwargs): return await super().execute(**kwargs)
    dt = DummyTool()
    assert await dt.execute() is None

@pytest.mark.asyncio
async def test_llm_client_coverage():
    from core.llm_client import LLMClient
    from core.schemas import Message, Role, ToolDefinition
    import httpx
    
    llm = LLMClient("http://localhost", "m")
    
    class DummyTool(ToolDefinition):
        def model_dump(self, **kwargs):
            return {"type": "function", "function": {"name": "test"}}
            
    tools = [MagicMock(model_dump=lambda **kwargs: {"type": "function", "function": {"name": "test"}})]
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": []}
        mock_post.return_value = mock_resp
        await llm.chat_completion([Message(role=Role.USER, content="hi")], tools=tools)

    with patch("httpx.AsyncClient.stream") as mock_stream:
        mock_ctx = AsyncMock()
        mock_resp = AsyncMock()
        async def aiter():
            yield "data: {bad json"
            yield "data: [DONE]"
        mock_resp.aiter_lines = aiter
        mock_ctx.__aenter__.return_value = mock_resp
        mock_stream.return_value = mock_ctx
        
        async for chunk in await llm.chat_completion([Message(role=Role.USER, content="hi")], stream=True):
            pass

@pytest.mark.asyncio
async def test_conversation_compact_empty_slice():
    mm = MagicMock()
    mm.short_term = MagicMock()
    mm.short_term.get_context_window_snapshot.return_value = MagicMock(usage_percent=90.0)
    
    class MockList(list):
        def __getitem__(self, i):
            if isinstance(i, slice):
                return []
            return super().__getitem__(i)

    from core.schemas import Message, Role
    mm.short_term.get_messages.return_value = MockList([1,2,3,4])
    
    cm = ConversationManager(MagicMock(), MagicMock(), mm)
    cm.prune_strategy = 'compact'
    await cm._auto_compact()

@pytest.mark.asyncio
async def test_shell_truncation_and_search_empty():
    from tools.shell_tool import ShellTool
    from tools.search_tool import SearchTool
    import asyncio
    
    st = ShellTool()
    res = await st.execute("python3 -c 'print(\"A\" * 11000)'")
    assert "[TRUNCATED]" in res.output
    
    wt = SearchTool()
    with patch("duckduckgo_search.DDGS.text", return_value=[]):
        res2 = await wt.execute("test")
        assert "No results found" in res2.output

@pytest.mark.asyncio
async def test_memory_tool_returns():
    from tools.memory_tool import MemoryTool
    ltm = AsyncMock()
    ltm.search.return_value = [MagicMock(id=1, category="c", content="c")]
    mt = MemoryTool(ltm)
    res = await mt.execute("search", query="q")
    assert "c" in res.output
    
    ltm.list_all.return_value = []
    res2 = await mt.execute("list")
    assert "No memories found" in res2.output
