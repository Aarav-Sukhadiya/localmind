from core.schemas import Message, Role, ContextSnapshot, MessageTokenInfo
from memory.token_counter import TokenCounter

class ShortTermMemory:
    def __init__(self, max_tokens: int = 8192, token_counter: TokenCounter = None):
        self.max_tokens = max_tokens
        self.token_counter = token_counter or TokenCounter()
        self.messages = []
        
    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.prune()
        
    def get_messages(self) -> list[Message]:
        return list(self.messages)
        
    def get_context_window_snapshot(self) -> ContextSnapshot:
        total = self.token_counter.count_messages(self.messages)
        per_msg = []
        for m in self.messages:
            preview = m.content[:50] + "..." if m.content and len(m.content) > 50 else (m.content or "Tool Call")
            per_msg.append(MessageTokenInfo(role=m.role.value, preview=preview, tokens=self.token_counter.count_messages([m])))
            
        return ContextSnapshot(
            messages=self.get_messages(),
            total_tokens=total,
            max_tokens=self.max_tokens,
            usage_percent=round((total / self.max_tokens) * 100, 2),
            per_message_tokens=per_msg
        )
        
    def prune(self) -> list[Message]:
        pruned = []
        while self.token_counter.count_messages(self.messages) > self.max_tokens and len(self.messages) > 1:
            # Never prune the system prompt
            if self.messages[0].role == Role.SYSTEM:
                if len(self.messages) > 2:
                    pruned.append(self.messages.pop(1))
                else:
                    break
            else:
                pruned.append(self.messages.pop(0))
        return pruned
        
    def clear(self) -> None:
        self.messages.clear()
