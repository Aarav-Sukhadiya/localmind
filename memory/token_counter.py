import tiktoken
from core.schemas import Message

class TokenCounter:
    def __init__(self, method: str = 'tiktoken', model: str = 'gpt-4'):
        self.method = method
        if method == 'tiktoken':
            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                self.encoding = tiktoken.get_encoding('cl100k_base')

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self.method == 'tiktoken':
            return len(self.encoding.encode(text))
        else:
            return len(text) // 4

    def count_messages(self, messages: list[Message]) -> int:
        total = 0
        for msg in messages:
            total += self.count(msg.content or "")
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += self.count(tc.function.name)
                    total += self.count(tc.function.arguments)
        return total
