from duckduckgo_search import DDGS
from tools.registry import BaseTool
from core.schemas import ToolResult

class SearchTool(BaseTool):
    name = "web_search"
    description = "Search the web and return top results with titles, URLs, and snippets"
    parameters = {
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results", "default": 5}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        if not query:
            return ToolResult(success=False, output="", error="Query cannot be empty")
            
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                
            if not results:
                return ToolResult(success=True, output="No results found.")
                
            output = ""
            for i, r in enumerate(results):
                output += f"{i+1}. {r.get('title')}\nURL: {r.get('href')}\n{r.get('body')}\n\n"
                
            return ToolResult(success=True, output=output.strip())
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Search failed: {str(e)}")
