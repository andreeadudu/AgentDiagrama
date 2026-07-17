"""
Application configuration.

Contains all configurable settings used by the AI agent:
model settings, Knowledge Base location, chunking, embeddings,
semantic search, context recycling, and token pricing.

Model Orchestration — Dedicated Models
---------------------------------------
This application uses two separate models, each chosen for its
specific role:

1. Chat Model: gpt-5-mini (Azure AI Foundry)
   - Handles all natural language tasks: interpreting user
     requirements, generating Mermaid diagram code, explaining
     diagrams, and deciding when to call tools.
   - Accessed via the OpenAI-compatible API at AZURE_ENDPOINT.

2. Embedding Model: bge-m3 (local, via Ollama)
   - Dedicated to converting text into vector embeddings for
     semantic search over the Knowledge Base.
   - Runs locally to avoid network latency and API costs on
     high-frequency embedding operations (every user message
     triggers an embedding call for retrieval).
   - Accessed via Ollama's REST API at EMBEDDINGS_ENDPOINT.

This separation is intentional: embedding models are optimized
for dense retrieval (small, fast, cheap), while chat models are
optimized for generation (larger, slower, more expensive). Using
a single model for both would either sacrifice retrieval quality
or waste generation budget on simple vector lookups.
"""

# --- Chat Model (Azure AI Foundry) ---
MODEL_NAME = "gpt-5-mini"
AZURE_ENDPOINT = "https://ai...."
API_KEY = "..."

# --- Embedding Model (local, via Ollama) ---
EMBEDDINGS_MODEL = "bge-m3:latest"
EMBEDDINGS_ENDPOINT = "http://localhost:11434/api/embed"

# --- Knowledge Base ---
KNOWLEDGE_BASE_DIR = "knowledge"

# --- Chunking ---
CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 100  # characters of overlap between consecutive chunks

# --- Embeddings storage & Semantic Search ---
EMBEDDINGS_OUTPUT_PATH = "embeddings_store.json"
SEMANTIC_SEARCH_TOP_N = 3
SEMANTIC_SEARCH_MIN_SIMILARITY = 0.3

# --- Context Recycling ---
MAX_CONTEXT_TOKENS = 8000
CONTEXT_TRIM_KEEP_LAST = 6

# --- Token pricing (USD per 1M tokens) ---
INPUT_TOKEN_PRICE_PER_MILLION = 2.0
OUTPUT_TOKEN_PRICE_PER_MILLION = 10.0