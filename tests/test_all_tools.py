import sys
import pytest
import os
sys.path.insert(0, "/home/aarav/Projects/python_projects/localmind")
from tools.memory_tool import MemoryTool
from tools.shell_tool import ShellTool
from tools.python_tool import PythonTool
from tools.file_tool import FileTool
from unittest.mock import AsyncMock, MagicMock, patch
import memory.models

@pytest.mark.asyncio
async def test_tools_exhaustive(tmp_path):
    # MemoryTool
    ltm = AsyncMock()
    mt = MemoryTool(ltm)
    ltm.save.return_value = 1
    await mt.execute(action="save", content="x", category="y")
    ltm.update.return_value = True
    await mt.execute(action="update", memory_id=1, content="y")
    ltm.delete.return_value = True
    await mt.execute(action="delete", memory_id=1)
    await mt.execute(action="list", category="general")
    await mt.execute(action="get_context", query="x")
    await mt.execute(action="get", memory_id=1)
    
    # PythonTool
    pt = PythonTool()
    res = await pt.execute("print('x')")
    
    # FileTool
    ft = FileTool(str(tmp_path))
    await ft.execute("mkdir", "new_dir")
    await ft.execute("write", "new_dir/test.txt", "content")
    st = ShellTool()
    with patch("asyncio.create_subprocess_shell", side_effect=Exception("mocked")):
        await st.execute("sleep 1")

    # SubagentTool properties
    from tools.subagent_tool import SubagentTool
    sbat = SubagentTool(lambda: None)
    _ = sbat.name
    _ = sbat.description
    _ = sbat.parameters
    
    # Memory tool exception
    ltm.save.side_effect = Exception("failed")
    await mt.execute("save", content="x")
    
    # Token counter tool calls
    from memory.token_counter import TokenCounter
    from core.schemas import ToolCall, ToolCallFunction, Message, Role
    tc = TokenCounter()
    msg = Message(role=Role.ASSISTANT, content="", tool_calls=[ToolCall(id="1", function=ToolCallFunction(name="f", arguments="{}"))])
    tc.count_messages([msg])
    await ft.execute("append", "new_dir/test.txt", "more")
    await ft.execute("read", "new_dir/test.txt")
    await ft.execute("exists", "new_dir/test.txt")
    await ft.execute("copy", "new_dir/test.txt", destination="new_dir/test2.txt")
    await ft.execute("move", "new_dir/test2.txt", destination="new_dir/test3.txt")
    await ft.execute("delete", "new_dir/test3.txt")
    await ft.execute("delete", "new_dir")
    
    # Error cases
    await ft.execute("read", "missing.txt")
    await ft.execute("delete", "missing.txt")
    await ft.execute("list", "missing.txt")
    await ft.execute("copy", "a") # missing dest
    
    # Path traversal
    res = await ft.execute("read", "../../../etc/passwd")
    assert res.success == False
    
    # ShellTool
    st = ShellTool()
    await st.execute("echo test")
