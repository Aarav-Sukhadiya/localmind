
from tools.registry import BaseTool, ToolResult
class MyTool(BaseTool):
    @property
    def name(self): return "mytool"
    @property
    def description(self): return "desc"
    @property
    def parameters(self): return {}
    async def execute(self, **kwargs): return ToolResult(success=True, output="ok")
