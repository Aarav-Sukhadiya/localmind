import yaml
import uvicorn
import asyncio
from server.app import create_app
from core.llm_client import LLMClient
from core.conversation import ConversationManager
from tools.registry import ToolRegistry
from tools.shell_tool import ShellTool
from tools.python_tool import PythonTool
from tools.file_tool import FileTool
from tools.search_tool import SearchTool
from tools.memory_tool import MemoryTool
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from memory.token_counter import TokenCounter

class MemoryManager:
    def __init__(self, ltm, stm):
        self.long_term = ltm
        self.short_term = stm

async def init_services(config):
    # 1. Memory
    ltm = LongTermMemory(config['memory']['db_path'])
    await ltm.initialize()
    tc = TokenCounter(config['context']['token_counter'])
    stm = ShortTermMemory(config['context']['max_tokens'], tc)
    memory_manager = MemoryManager(ltm, stm)
    
    # 2. Tools
    registry = ToolRegistry()
    if config['tools']['shell']['enabled']:
        registry.register(ShellTool(config['tools']['shell']['blocked_commands']))
    if config['tools']['python']['enabled']:
        registry.register(PythonTool())
    if config['tools']['file']['enabled']:
        registry.register(FileTool(config['tools']['file']['base_directory']))
    if config['tools']['web_search']['enabled']:
        registry.register(SearchTool())
    if config['tools']['memory']['enabled']:
        registry.register(MemoryTool(ltm))
        
    # 3. LLM & Conversation
    llm = LLMClient(
        base_url=config['llm']['base_url'],
        model=config['llm']['model'],
        api_key=config['llm']['api_key']
    )
    conv_manager = ConversationManager(llm, registry, memory_manager)
    
    return memory_manager, registry, conv_manager

def main():
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
        
    app = create_app(config)
    
    @app.on_event("startup")
    async def startup():
        mm, tr, cm = await init_services(config)
        app.state.memory_manager = mm
        app.state.tool_registry = tr
        app.state.conversation_manager = cm
        
    uvicorn.run(app, host=config['server']['host'], port=config['server']['port'])

if __name__ == '__main__':
    main()
