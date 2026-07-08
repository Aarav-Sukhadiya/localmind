from typing import AsyncIterator
from core.schemas import Message, Event, Role
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, llm_client, tool_registry, memory_manager):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.max_tool_loops = 10

    async def process_message(self, user_message: str) -> AsyncIterator[Event]:
        # 1. Prepend system prompt + long-term memory context
        context = await self.memory_manager.long_term.get_relevant_context(user_message)
        system_prompt = Message(role=Role.SYSTEM, content=f"You are LocalMind, a helpful AI assistant.\n\nRelevant Memories:\n{context}")
        
        # In a real app we'd keep the system prompt persistent. Here we'll just ensure it's in short-term memory.
        messages = self.memory_manager.short_term.get_messages()
        if not messages or messages[0].role != Role.SYSTEM:
             self.memory_manager.short_term.add_message(system_prompt)

        # 2. Add user message
        msg = Message(role=Role.USER, content=user_message)
        self.memory_manager.short_term.add_message(msg)
        
        yield Event(type="thinking", data={"message": "Processing user input..."})
        
        tools = self.tool_registry.list_tools()
        
        loop_count = 0
        while loop_count < self.max_tool_loops:
            loop_count += 1
            messages = self.memory_manager.short_term.get_messages()
            
            try:
                response = await self.llm_client.chat_completion(messages, tools=tools if tools else None, stream=False)
            except Exception as e:
                yield Event(type="error", data={"error": str(e)})
                break
                
            choice = response.choices[0]
            assistant_message = choice.message
            self.memory_manager.short_term.add_message(assistant_message)
            
            if assistant_message.content:
                yield Event(type="response_chunk", data={"content": assistant_message.content})
            
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    yield Event(type="tool_call", data={"tool_call": tool_call.model_dump()})
                    try:
                        import json
                        args = json.loads(tool_call.function.arguments)
                        result = await self.tool_registry.execute(tool_call.function.name, args)
                        tool_msg = Message(
                            role=Role.TOOL, 
                            content=result.output if result.success else f"Error: {result.error}",
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name
                        )
                    except Exception as e:
                        tool_msg = Message(
                            role=Role.TOOL,
                            content=f"Execution failed: {str(e)}",
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name
                        )
                    
                    self.memory_manager.short_term.add_message(tool_msg)
                    yield Event(type="tool_result", data={"tool_call_id": tool_call.id, "result": tool_msg.content})
            else:
                break
                
        if loop_count >= self.max_tool_loops:
            yield Event(type="error", data={"error": "Max tool loop iterations reached."})
            
        yield Event(type="done", data={})

    def get_history(self) -> list[Message]:
        return self.memory_manager.short_term.get_messages()

    def clear_history(self) -> None:
        self.memory_manager.short_term.clear()

    def save_conversation(self, path: str) -> None:
        import json
        msgs = [m.model_dump() for m in self.get_history()]
        with open(path, "w") as f:
            json.dump(msgs, f)

    def load_conversation(self, path: str) -> None:
        import json
        with open(path, "r") as f:
            msgs = json.load(f)
        self.clear_history()
        for m in msgs:
            self.memory_manager.short_term.add_message(Message.model_validate(m))
