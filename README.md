# LocalMind 🧠

LocalMind is a privacy-first, self-hosted AI workspace that connects to local Large Language Models (LLMs) via **llama.cpp** or **LM Studio**, giving them real agency on your machine.

Unlike typical chat-only interfaces, LocalMind allows the LLM to:
- 💻 **Execute Shell Commands**
- 🐍 **Run Python Scripts**
- 📂 **Manage Local Files (CRUD)**
- 🌐 **Search the Web**
- 🧠 **Maintain Long-Term Persistent Memory (ChromaDB + SQLite)**

All while remaining completely local and open-source.

## Architecture

LocalMind is split into a robust **Python (FastAPI)** backend and a stunning **React/Vite (Tailwind CSS v4)** frontend.

- **`core/`**: LLM API integration and agentic conversation loop.
- **`tools/`**: Secure and sandboxed tool engine for Shell, Python, Web Search, and File execution.
- **`memory/`**: Advanced short-term context window management and long-term memory embeddings using ChromaDB.
- **`server/`**: FastAPI REST + WebSocket servers.
- **`desktop-app/`**: A beautiful glassmorphism React UI wrapper.

## Features
- **Real-Time Token Usage Tracking**: View live updates of the LLM context window.
- **Dynamic Tool Execution**: See streaming output and truncated results right in the chat panel.
- **Auto-Context Compaction**: Context is seamlessly summarized when it nears the 8192 token limit.
- **Extensive Test Coverage**: Built by an AI team with **99.88% backend test coverage** using `pytest`, and comprehensive frontend testing via `vitest`.

## Quickstart

### 1. Requirements
- Python 3.10+
- Node.js v18+
- [llama.cpp](https://github.com/ggerganov/llama.cpp) or LM Studio

### 2. Backend Setup
1. Clone the repository and CD into it:
   ```bash
   cd localmind
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start your local LLM (e.g., llama.cpp):
   ```bash
   llama-server -m your_model.gguf --port 8080 -c 8192
   ```
4. Start the FastAPI server:
   ```bash
   python main.py
   ```
   The backend will be available at `http://localhost:8000`.

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd desktop-app
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The beautiful Glassmorphism UI will be accessible on your browser!

## Testing
We take reliability seriously. The project ships with both backend and frontend tests.

**Backend Coverage (99.88%)**:
```bash
python -m pytest tests/ --cov=core --cov=tools --cov=memory --cov=server --cov-report=term-missing
```

**Frontend Coverage**:
```bash
cd desktop-app
npx vitest run --coverage
```

## Security & Safety
LocalMind executes code on your local system. By default, destructive shell commands (like `rm -rf /`) are blocked, and file access is sandboxed. You can configure safety limits and blocked commands within `config.yaml`.
