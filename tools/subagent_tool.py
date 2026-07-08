import asyncio
from typing import Optional
from tools.registry import BaseTool, ToolResult
from core.schemas import Message, Role

class SubagentTool(BaseTool):
    def __init__(self, agent_factory):
        self.agent_factory = agent_factory

    @property
    def name(self) -> str:
        return "invoke_subagent"

    @property
    def description(self) -> str:
        return "Spawn a parallel AI subagent to perform a sub-task. Use this when a task is complex and can be delegated (e.g., separate research, writing a different file). Returns the subagent's final answer."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "The role of the subagent (e.g., 'Python Developer', 'Web Researcher')"
                },
                "task": {
                    "type": "string",
                    "description": "The specific task instruction for the subagent to complete."
                }
            },
            "required": ["role", "task"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        role = kwargs.get("role")
        task = kwargs.get("task")
        
        try:
            # agent_factory returns a fresh ConversationManager
            subagent = self.agent_factory()
            
            # Setup the subagent's memory
            system_prompt = Message(role=Role.SYSTEM, content=f"You are a specialized subagent. Your role is: {role}. Complete the following task and provide the final result clearly.")
            subagent.memory_manager.short_term.add_message(system_prompt)
            
            async for _ in subagent.process_message(task):
                pass
                
            # Extract the final answer from the subagent's history
            history = subagent.get_history()
            for msg in reversed(history):
                if msg.role == Role.ASSISTANT and msg.content:
                    return ToolResult(success=True, output=f"Subagent '{role}' completed the task:\n{msg.content}")
                    
            return ToolResult(success=False, output="", error="Subagent did not return a concrete text response.")
            
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
