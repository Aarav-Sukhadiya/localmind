from tools.registry import BaseTool
from core.schemas import ToolResult

class MemoryTool(BaseTool):
    name = "memory"
    description = "Store, retrieve, update, or delete long-term memories"
    parameters = {
        "properties": {
            "action": {"type": "string", "enum": ["save", "search", "list", "delete", "update"]},
            "content": {"type": "string", "description": "Memory content to save/update"},
            "category": {"type": "string", "description": "Category tag", "default": "general"},
            "query": {"type": "string", "description": "Search query for retrieval"},
            "memory_id": {"type": "integer", "description": "ID for update/delete"}
        },
        "required": ["action"]
    }

    def __init__(self, long_term_memory):
        self.ltm = long_term_memory

    async def execute(self, action: str, content: str = "", category: str = "general", query: str = "", memory_id: int = 0) -> ToolResult:
        try:
            if action == "save":
                if not content:
                    return ToolResult(success=False, output="", error="Content required")
                new_id = await self.ltm.save(content, category)
                return ToolResult(success=True, output=f"Saved memory ID {new_id}")
                
            elif action == "search":
                if not query:
                    return ToolResult(success=False, output="", error="Query required")
                results = await self.ltm.search(query)
                if not results:
                    return ToolResult(success=True, output="No relevant memories found.")
                out = "\n".join([f"[{r.id}] ({r.category}): {r.content}" for r in results])
                return ToolResult(success=True, output=out)
                
            elif action == "list":
                results = await self.ltm.list_all(category if category != "general" else None)
                if not results:
                    return ToolResult(success=True, output="No memories found.")
                out = "\n".join([f"[{r.id}] ({r.category}): {r.content}" for r in results])
                return ToolResult(success=True, output=out)
                
            elif action == "delete":
                if not memory_id:
                    return ToolResult(success=False, output="", error="memory_id required")
                success = await self.ltm.delete(memory_id)
                if success:
                    return ToolResult(success=True, output=f"Deleted memory ID {memory_id}")
                return ToolResult(success=False, output="", error="Memory not found")
                
            elif action == "update":
                if not memory_id or not content:
                    return ToolResult(success=False, output="", error="memory_id and content required")
                success = await self.ltm.update(memory_id, content)
                if success:
                    return ToolResult(success=True, output=f"Updated memory ID {memory_id}")
                return ToolResult(success=False, output="", error="Memory not found")
                
            return ToolResult(success=False, output="", error="Unknown action")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
