from abc import ABC, abstractmethod
from typing import Dict, List, Any
from core.schemas import ToolResult, ToolDefinition, ToolFunctionDefinition, ToolParameters

class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema for parameters
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
        
    def get_definition(self) -> ToolDefinition:
        # Convert simple dict to Pydantic models
        params = ToolParameters(
            type="object",
            properties=self.parameters.get("properties", {}),
            required=self.parameters.get("required", [])
        )
        func_def = ToolFunctionDefinition(
            name=self.name,
            description=self.description,
            parameters=params
        )
        return ToolDefinition(type="function", function=func_def)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        return self._tools[name]
        
    def list_tools(self) -> List[ToolDefinition]:
        return [tool.get_definition() for tool in self._tools.values()]
        
    async def execute(self, name: str, arguments: dict) -> ToolResult:
        try:
            tool = self.get_tool(name)
            return await tool.execute(**arguments)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
