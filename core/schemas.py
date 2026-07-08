"""
Shared Pydantic schemas used across all modules.
Placed here so every engineer imports from the same source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallFunction(BaseModel):
    name: str
    arguments: str  # JSON-encoded string


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: ToolCallFunction


class Message(BaseModel):
    role: Role
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None


# ---------------------------------------------------------------------------
# Tool Definitions (sent to the LLM)
# ---------------------------------------------------------------------------

class ToolParameter(BaseModel):
    type: str
    description: str = ""
    enum: list[str] | None = None
    default: Any = None


class ToolParameters(BaseModel):
    type: str = "object"
    properties: dict[str, ToolParameter]
    required: list[str] = Field(default_factory=list)


class ToolFunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: ToolParameters


class ToolDefinition(BaseModel):
    type: str = "function"
    function: ToolFunctionDefinition


# ---------------------------------------------------------------------------
# Tool Results
# ---------------------------------------------------------------------------

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None


# ---------------------------------------------------------------------------
# LLM Responses
# ---------------------------------------------------------------------------

class LLMChoice(BaseModel):
    message: Message
    finish_reason: str | None = None


class LLMResponse(BaseModel):
    choices: list[LLMChoice]


class LLMResponseDelta(BaseModel):
    role: str | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


class LLMStreamChoice(BaseModel):
    delta: LLMResponseDelta
    finish_reason: str | None = None


class LLMStreamChunk(BaseModel):
    choices: list[LLMStreamChoice]


# ---------------------------------------------------------------------------
# Events (yielded by ConversationManager to the server/UI)
# ---------------------------------------------------------------------------

class Event(BaseModel):
    type: Literal["thinking", "tool_call", "tool_result", "response_chunk", "error", "done"]
    data: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class MemoryEntry(BaseModel):
    id: int
    content: str
    category: str = "general"
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Context Snapshot
# ---------------------------------------------------------------------------

class MessageTokenInfo(BaseModel):
    role: str
    preview: str
    tokens: int


class ContextSnapshot(BaseModel):
    messages: list[Message]
    total_tokens: int
    max_tokens: int
    usage_percent: float
    per_message_tokens: list[MessageTokenInfo]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMConnectionError(Exception):
    """Raised when the LLM backend is unreachable."""
    pass


class ToolNotFoundError(Exception):
    """Raised when an unknown tool is requested."""
    pass


class ToolExecutionError(Exception):
    """Raised when a tool fails during execution."""
    pass
