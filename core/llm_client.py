import httpx
import json
import logging
from typing import AsyncIterator, Optional, List
from core.schemas import Message, ToolDefinition, LLMResponse, LLMStreamChunk, LLMConnectionError

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str, model: str, api_key: str = 'not-needed'):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        if tools:
            payload["tools"] = [t.model_dump(exclude_none=True) for t in tools]

        logger.info(f"Sending request to {url} (stream={stream})")
        
        if stream:
            return self._stream_response(url, payload)
            
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return LLMResponse.model_validate(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM backend: {e.response.text}")
            raise LLMConnectionError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Connection error to LLM backend: {e}")
            raise LLMConnectionError(f"Failed to connect to LLM at {self.base_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error formatting LLM response: {e}")
            raise ValueError(f"Invalid response format: {e}")

    async def _stream_response(self, url: str, payload: dict) -> AsyncIterator[LLMStreamChunk]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if line.startswith("data: "):
                            data_str = line[len("data: "):]
                            try:
                                data = json.loads(data_str)
                                yield LLMStreamChunk.model_validate(data)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse stream chunk: {data_str}")
        except httpx.RequestError as e:
            logger.error(f"Connection error to LLM backend during stream: {e}")
            raise LLMConnectionError(f"Stream connection failed: {e}")

class MultiplexLLMClient:
    def __init__(self, small_client: LLMClient, large_client: LLMClient):
        self.small_client = small_client
        self.large_client = large_client

    async def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ):
        # Routing logic: if there are tools requested or a complex prompt, use large_client
        # For simple conversational queries or summarizations (like compaction), use small_client
        is_complex = bool(tools) or any("code" in m.content.lower() for m in messages if m.content)
        client = self.large_client if is_complex else self.small_client
        
        logger.info(f"Multiplexing: Routing request to {client.model}")
        return await client.chat_completion(messages, tools, temperature, max_tokens, stream)
