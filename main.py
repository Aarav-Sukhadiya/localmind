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

from memory.long_term_chroma import LongTermMemoryChroma

class MemoryManager:
    def __init__(self, ltm, stm):
        self.long_term = ltm
        self.short_term = stm

async def init_services(config):
    # 1. Memory
    if config.get('memory', {}).get('backend') == 'chromadb':
        ltm = LongTermMemoryChroma(config['memory']['db_path'])
    else:
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
    multiplex_conf = config['llm'].get('multiplexing', {})
    if multiplex_conf.get('enabled'):
        from core.llm_client import MultiplexLLMClient
        small_llm = LLMClient(base_url=multiplex_conf['small_model_url'], model=multiplex_conf.get('small_model_name', config['llm']['model']), api_key=config['llm']['api_key'])
        large_llm = LLMClient(base_url=multiplex_conf['large_model_url'], model=multiplex_conf.get('large_model_name', config['llm']['model']), api_key=config['llm']['api_key'])
        llm = MultiplexLLMClient(small_llm, large_llm)
    else:
        llm = LLMClient(
            base_url=config['llm']['base_url'],
            model=config['llm']['model'],
            api_key=config['llm']['api_key']
        )
    conv_manager = ConversationManager(llm, registry, memory_manager)
    conv_manager.prune_strategy = config.get('context', {}).get('prune_strategy', 'oldest_first')
    conv_manager.compaction_threshold = config.get('context', {}).get('compaction_threshold', 0.8)
    
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
