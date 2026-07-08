import sys
import pytest
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from memory.long_term_chroma import LongTermMemoryChroma
import os
import shutil

@pytest.fixture
def chroma_db_path(tmp_path):
    path = str(tmp_path / "chroma_test")
    yield path
    shutil.rmtree(path, ignore_errors=True)

@pytest.mark.asyncio
async def test_chroma_memory(chroma_db_path):
    ltm = LongTermMemoryChroma(chroma_db_path)
    await ltm.initialize()
    
    # Save
    id1 = await ltm.save("test memory 1", "general")
    id2 = await ltm.save("test memory 2", "work")
    
    # Get
    m1 = await ltm.get(id1)
    assert m1.content == "test memory 1"
    
    # Search
    res = await ltm.search("memory", 5)
    assert len(res) == 2
    
    # Update
    await ltm.update(id1, "updated memory 1")
    assert (await ltm.get(id1)).content == "updated memory 1"
    
    # List all
    res = await ltm.list_all()
    assert len(res) == 2
    res_work = await ltm.list_all("work")
    assert len(res_work) == 1
    
    # Get relevant context
    ctx = await ltm.get_relevant_context("test")
    assert "updated memory 1" in ctx or "test memory 2" in ctx
    
    # Delete
    await ltm.delete(id1)
    assert await ltm.get(id1) is None
    
    # Edge cases
    assert await ltm.update(999, "fake") is False
    assert await ltm.delete(999) is False
    assert await ltm.get(999) is None
    assert "No relevant" in await ltm.get_relevant_context("")
    assert "No relevant" in await ltm.get_relevant_context("")
    
    await ltm.close()
    
@pytest.mark.asyncio
async def test_chroma_memory_empty(chroma_db_path):
    ltm = LongTermMemoryChroma(chroma_db_path)
    await ltm.initialize()
    res = await ltm.search("test", 5)
    assert len(res) == 0
