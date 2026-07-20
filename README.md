# 📐 Diagrama — AI Diagram Generation Agent

An AI-powered agent that generates validated Mermaid diagrams from plain-text descriptions of systems, processes, and data models. Built for software architects and engineers who need to produce architecture diagrams quickly and consistently.

## What It Does

You describe a system in natural language — or point to a `.txt` file with a design doc — and Diagrama produces a syntactically valid Mermaid diagram with an explanation of what it shows. The agent validates every diagram before returning it, and can export diagrams to `.mmd` files for use in VS Code, documentation, or design reviews.

**Supported diagram types:** Flowchart, Sequence Diagram, Class Diagram, ER Diagram, State Diagram.

**Example interaction:**
```
You: Draw a sequence diagram for a user logging in through an auth service that checks a database

AI: ```mermaid
sequenceDiagram
    participant User
    participant AuthService
    participant Database
    User->>AuthService: POST /login (credentials)
    AuthService->>Database: SELECT user WHERE username=...
    Database-->>AuthService: User record
    alt Password matches
        AuthService-->>User: 200 OK + JWT token
    else Invalid
        AuthService-->>User: 401 Unauthorized
    end
```
This sequence diagram shows the login flow where the auth service
queries a database and returns a token on success.
```

## Architecture

The project follows a RAG (Retrieval-Augmented Generation) architecture with dedicated models for different tasks:

```
User Input (text or .txt file)
    │
    ▼
┌──────────────────────────────────┐
│           Agent (agent.py)       │
│                                  │
│  1. Semantic Search              │◄── Embedding Model (bge-m3, local via Ollama)
│     └─ Retrieve relevant chunks  │        └─ Converts text to vectors
│        from Knowledge Base       │        └─ Cosine similarity search
│                                  │
│  2. Context Injection            │
│     └─ Add retrieved context     │
│        to conversation           │
│                                  │
│  3. LLM Call                     │◄── Chat Model (gpt-5-mini, Azure AI Foundry)
│     └─ Generate diagram          │        └─ Natural language understanding
│                                  │        └─ Mermaid code generation
│  4. Tool Execution               │
│     └─ Validate syntax           │
│     └─ Export to file            │
│     └─ Read requirement file     │
│                                  │
│  5. Response Cleanup             │
│     └─ Strip internal metadata   │
└──────────────────────────────────┘
    │
    ▼
Mermaid Diagram + Explanation
```

**Model Orchestration — Dedicated Models:**
- **Chat Model** (`gpt-5-mini` via Azure): handles all natural language tasks — interpreting requirements, generating Mermaid code, explaining diagrams, deciding when to call tools.
- **Embedding Model** (`bge-m3` via Ollama): dedicated to converting text into vector embeddings for semantic search. Runs locally to avoid network latency and API costs on high-frequency embedding operations.

## Project Structure

```
diagrama-agent/
├── main.py                      # CLI entry point
├── web_app.py                   # Flask Web UI + REST API
├── streamlit_app.py             # Streamlit Web UI
├── config.py                    # All configurable settings
├── agent.py                     # Core agent orchestration
├── llm_client.py                # Chat model communication (Azure)
├── embeddings_client.py         # Embedding model + semantic search (Ollama)
├── conversation_context.py      # Conversation memory + token tracking
├── document_chunker.py          # Chunk documents with overlap (generator)
├── embedding_generator.py       # Generate and cache embeddings
├── knowledge_base_loader.py     # Load KB documents from registry
├── utils.py                     # Token counting + @timed decorator
├── logging_config.py            # Centralized structured logging
├── test_mermaid.py              # Validator unit tests
│
├── tools/
│   ├── __init__.py
│   ├── tool.py                  # Tool base class
│   ├── tools.py                 # Tool registry
│   ├── validate_mermaid_tool.py # Syntax validation tool
│   ├── export_mermaid_to_file_tool.py  # File export tool
│   └── read_requirement_file_tool.py   # Read .txt requirements tool
│
├── knowledge/
│   ├── prompts/
│   │   └── agent_identity.md    # Agent persona definition
│   ├── facts/
│   │   ├── registry.json
│   │   ├── mermaid_diagram_types.md        # always_load: true
│   │   ├── mermaid_syntax_reference.md     # always_load: false (retrieved via search)
│   │   └── software_architecture_patterns.md # always_load: false (retrieved via search)
│   └── procedures/
│       ├── registry.json
│       └── diagram_generation_procedure.md # always_load: true
│
├── web/
│   └── index.html               # Flask Web UI frontend
│
├── requirements.txt
├── .gitignore
└── README.md
```

## How to Run

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed locally with the `bge-m3` embedding model
- Azure AI Foundry API key (for the chat model)

### Setup

```bash
# Clone the repository
git clone https://github.com/andreeadudu/AgentDiagrama.git
cd AgentDiagrama

# Install dependencies
pip install -r requirements.txt

# Start Ollama and pull the embedding model
ollama pull bge-m3

# Set your API key in config.py
# Replace YOUR_AZURE_API_KEY and YOUR_AZURE_ENDPOINT with your values

# Generate embeddings (required on first run)
python embedding_generator.py
```

### Run — CLI

```bash
python main.py
```

Commands: type a diagram request, `export` to save session, `import` to restore, `exit` to quit.

You can also point to a file: `Generate a diagram from the file requirements.txt`

### Run — Flask Web UI

```bash
pip install flask
python web_app.py
```

Open `http://localhost:5000` in your browser. Diagrams are rendered visually using Mermaid.js.

**REST API endpoints:**
- `POST /api/chat` — send a message, receive a diagram
- `POST /api/reset` — start a new session
- `GET /api/health` — health check

### Run — Streamlit Web UI

```bash
pip install streamlit
streamlit run streamlit_app.py
```

## Features Implemented

### Mandatory (10p)

| Feature | Module |
|---|---|
| Agent with custom persona | `agent_identity.md` — "Diagrama" for software architects |
| Conversation Context | `conversation_context.py` — message history management |
| Dynamic System Prompt | `assemble_system_prompt()` — built from KB at runtime |
| Knowledge Base (Prompts/Facts/Procedures) | `knowledge_base_loader.py` + folder structure |
| Registries for Facts and Procedures | `registry.json` files with `always_load` flag |
| Document Chunking | `document_chunker.py` — generator with configurable overlap |
| Embeddings Generation | `embedding_generator.py` — cached to disk |
| Semantic Search | `embeddings_client.semantic_search()` — cosine similarity |
| Retrieval-based Context Injection | `agent._inject_relevant_context()` with fallback |
| Token Usage Tracking | `input_tokens` / `output_tokens` accumulated per session |
| Cost Estimation | `get_estimated_cost()` using configurable per-million pricing |

### Required Extensions (12p)

| Extension | Points | Implementation |
|---|---|---|
| Context Recycling / Compression | 2p | Sliding-window trimming in `_maybe_trim_history()` — drops oldest messages when token budget exceeded, protects system prompt + last N messages |
| Cost Optimization | 2p | Stale retrieval removal in `_remove_last_retrieval_message()` — only latest retrieval is sent to model, previous ones are deleted to avoid linear cost growth |
| Robust Error Handling | 2p | Try/except with clear messages in `embeddings_client.py` (timeout, connection, bad response), `llm_client.py` (API errors), `knowledge_base_loader.py` (missing files, corrupt JSON), `agent.py` (tool crashes) |
| Fallback Strategy | 2p | Retrieval fallback (no results → explicit notice to model), tool crash fallback (error reported as tool result), CLI session preserved on model failure, procedure limits validation retries to 2 |
| Scalability & Extensibility | 2p | Added `export_mermaid_to_file` tool (1 file + 1 line), added `software_architecture_patterns.md` fact (1 file + 1 registry entry) — zero changes to agent/llm/core code |
| Code Quality | 2p | Full EN translation, API key removed from code, consistent docstrings, structured logging, message sanitization before API calls |

### Optional Enhancements (~12p)

| Enhancement | Points | Implementation |
|---|---|---|
| Extra Tool (3 tools) | 3p | `validate_mermaid_syntax` (validation), `export_mermaid_to_file` (file I/O), `read_requirement_file` (file input) |
| Chunk Overlap Strategy | 2p | `CHUNK_OVERLAP = 100` in config, implemented as generator in `_split_into_chunks()` |
| Colored Terminal UI | 1p | Colorama integration in `main.py` — green (AI), cyan (prompt), red (errors), gray (stats) |
| Structured Logging | 2p | `logging_config.py` + `logging.getLogger(__name__)` in all modules, configurable level |
| Export/Import Conversation History | 1p | `export` / `import` CLI commands, JSON format with timestamps |
| Embedding Cache | 2p | `embedding_generator.py` — skips regeneration if file exists (`force=False`) |
| Dedicated Embedding + Chat Model | 2p | `bge-m3` (local, Ollama) for embeddings + `gpt-5-mini` (Azure) for chat — documented in `config.py` |

### Python Concepts Applied

| Concept | Where |
|---|---|
| Generator | `_split_into_chunks()` in `document_chunker.py` — lazy chunk production with `yield` |
| Decorator | `@timed` in `utils.py` — logs execution time of `process_message()` |
| List Comprehension | `_split_into_chunks` (original), message sanitization in `llm_client.py` |
| Dictionary Comprehension | `self.tools = {tool.name: tool for tool in tools}` in `agent.py` |
| Type Hints | `count_tokens(text: str) -> int`, `get_embedding(text: str) -> list[float]` |
| Modules | Each `.py` file is a separate module with clear responsibility |

## Configuration

All settings are centralized in `config.py`:

| Setting | Default | Purpose |
|---|---|---|
| `CHUNK_SIZE` | 500 | Characters per chunk |
| `CHUNK_OVERLAP` | 100 | Overlap between consecutive chunks |
| `SEMANTIC_SEARCH_TOP_N` | 3 | Max chunks returned by search |
| `SEMANTIC_SEARCH_MIN_SIMILARITY` | 0.3 | Minimum cosine similarity threshold |
| `MAX_CONTEXT_TOKENS` | 8000 | Triggers history trimming |
| `CONTEXT_TRIM_KEEP_LAST` | 6 | Recent messages protected from trimming |
| `INPUT_TOKEN_PRICE_PER_MILLION` | 2.0 | USD per 1M input tokens |
| `OUTPUT_TOKEN_PRICE_PER_MILLION` | 10.0 | USD per 1M output tokens |
