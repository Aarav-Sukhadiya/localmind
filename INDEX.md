# LocalMind Developer Index & Deep-Dive 📖

This document explains every nook and cranny of the LocalMind architecture, breaking down what each file and function does, and how the entire lifecycle connects the UI to the underlying LLM.

## 1. Core Engine (`/core`)

The `core` module is responsible for abstracting the LLM communication and managing the autonomous conversation loop.

### `core/schemas.py`
- **Purpose**: Defines strict Pydantic data models for everything moving through the system.
- **Key Classes**:
  - `Message`, `Role`: Represent conversation turns.
  - `ToolDefinition`, `ToolCall`: Standardizes how tools are defined to the LLM and requested.
  - `LLMStreamChunk`: Strongly typed chunks yielded during Server-Sent Event (SSE) parsing.

### `core/llm_client.py`
- **Purpose**: Handles HTTP/SSE communication with `llama.cpp` or LM Studio.
- **Key Functions**:
  - `chat_completion()`: Formats tools and messages, sending a POST request to the local LLM. Supports both blocking and `stream=True` responses.
  - `_stream_response()`: Iterates over the raw `httpx.AsyncClient` stream to decode `data: ` SSE format into Pydantic models in real-time.

### `core/conversation.py`
- **Purpose**: The "Agent Loop" that executes the model's logic repeatedly until it is finished.
- **Key Functions**:
  - `run_conversation_stream()`: An async generator that loops `chat_completion()`. If the LLM requests a tool call, this pauses generation, executes the tool via the Registry, appends the result, and loops again.
  - `_auto_compact()`: A crucial nook! When token usage is high (managed by ShortTermMemory), this explicitly prompts the LLM to summarize past messages. It slices the middle of the context (`messages[1:-2]`) and replaces it with a single synthesized summary to free up tokens.

## 2. Tools Engine (`/tools`)

The `tools` directory is where the LLM gains its agency. Each tool subclasses `BaseTool`.

### `tools/registry.py`
- **Purpose**: Dynamically loads tools and registers them.
- **Key Functions**:
  - `register_tools_from_directory()`: Scans the `tools/` and `tools/custom/` directories, using Python's `importlib` to dynamically ingest any valid subclass of `BaseTool`.

### Included Tools:
- **`shell_tool.py`**: Executes native shell commands asynchronously using `asyncio.create_subprocess_shell`. It features an aggressive truncation mechanism (10,000 characters) to prevent token window overflow.
- **`python_tool.py`**: A sandboxed Python execution environment that writes dynamic code to a temporary file, executes it via a subprocess, and pipes `stdout`/`stderr` back to the model.
- **`file_tool.py`**: Manages all local file CRUD (Create, Read, Update, Delete) operations.
- **`search_tool.py`**: Integrates with DuckDuckGo (`ddgs`) to scrape the web for live data.
- **`memory_tool.py`**: Allows the LLM to query its own Vector Database (ChromaDB) to recall old data.
- **`subagent_tool.py`**: Spawns sub-processes for multi-agent delegation.

## 3. Memory Subsystem (`/memory`)

Handles both short-term context windows (which messages the LLM sees right now) and long-term embeddings (Vector DB).

### `memory/token_counter.py`
- **Purpose**: Estimates how many tokens a string will use via `tiktoken`.

### `memory/short_term.py`
- **Purpose**: Tracks live conversation state.
- **Key Functions**:
  - `get_context_window_snapshot()`: Returns an object (`ContextSnapshot`) detailing exact token usage, message breakdown, and usage percentage, pushing this directly to the React ContextPanel UI.

### `memory/long_term_chroma.py`
- **Purpose**: Wraps ChromaDB as an async vector database.
- **Key Functions**:
  - `search()` / `save()`: Converts texts into semantic embeddings and stores them. The LLM can use `memory_tool.py` to trigger these. It uses `asyncio.to_thread` for all operations because ChromaDB's native Python client is blocking.

## 4. FastAPI Server (`/server`)

Exposes the backend functionality to the frontend via HTTP and WebSockets.

### `server/app.py`
- **Purpose**: App factory initializing the database, loading tools, applying CORS, and importing routes.

### `server/routes_chat.py`
- **Purpose**: Houses the `ws://.../ws/chat` WebSocket endpoint.
- **Key Functions**:
  - `chat_websocket()`: Maintains a full-duplex connection. As the user sends a message, it invokes `run_conversation_stream()` and pipes `chunk`, `tool_call`, and `tool_result` events directly over the socket to render live UI updates.

### `server/routes_memory.py` & `routes_tools.py`
- **Purpose**: Standard REST endpoints for fetching available tools, tracking subagent status, and CRUD operations for the Memory UI panel.

## 5. React Frontend Wrapper (`/desktop-app`)

Built with Vite, React, and Tailwind v4. The UI is designed entirely around a futuristic glassmorphism aesthetic.

### `src/App.tsx`
- **Purpose**: The main layout container. Manages tabs (Chat, Memory, Context).

### `src/hooks/useChat.ts`
- **Purpose**: The brain of the frontend.
- **Key Functions**:
  - Connects to the `/ws/chat` WebSocket.
  - Maintains an array of `messages` (combining User, Tool Output, and LLM text).
  - Handles streaming text concatenation and UI state (`isThinking`, `isConnecting`).

### `src/components/ChatPanel.tsx`
- **Purpose**: Renders the conversation. Detects when a message is a `tool_call` vs `tool_result` and renders them inside beautifully styled `<TerminalSquare />` UI boxes instead of plain text bubbles.

### `src/components/ContextPanel.tsx`
- **Purpose**: Polls `/api/memory/context` every 2 seconds. Renders a dynamic gradient progress bar that turns red when the token window hits 80%, visually indicating that `_auto_compact()` is about to trigger.

### `src/components/MemoryPanel.tsx`
- **Purpose**: Connects via REST to list, search, and delete Long-Term Memories manually.

## How to Operate the Nooks and Crannies 🛠️

1. **Adding Custom Tools**: 
   Just create a new file in `/tools/custom/` containing a class that inherits from `BaseTool`. Set the `name`, `description`, and `parameters` dictionary. The `Registry` will automatically parse it on boot, and the LLM will immediately know it exists.

2. **Triggering Auto-Compaction Manually**:
   If the LLM's context gets full, `_auto_compact()` triggers natively. However, you can force context clearance in the frontend by typing `/clear` in the Chat UI, which hits the `useChat` reset hook and re-initializes `short_term.py`.

3. **Modifying Token Limits**:
   The Context Tracker defaults to `8192` tokens. You can modify `max_tokens` via the initialization of the `ShortTermMemory` class in `server/app.py` to match the exact context size of the model you are running on LM Studio/llama.cpp.
