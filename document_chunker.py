"""
Document Chunker.

Exercise 3 - Chunking and preparing documents for Embeddings.

Loads Knowledge Base documents marked with "always_load": false
(the ones that don't go directly into the System Prompt) and splits
them into overlapping chunks, so they can later be turned into
embeddings.

Chunk Overlap Strategy: consecutive chunks share a configurable
number of characters (CHUNK_OVERLAP) at their boundaries. This
ensures that content falling at a chunk boundary is fully present
in at least one chunk, improving semantic search accuracy - without
overlap, a concept split across two chunks might not match well
against any single chunk.
"""

import knowledge_base_loader as kb
from config import CHUNK_SIZE, CHUNK_OVERLAP


def _split_into_chunks(text, chunk_size, overlap):
    """
    Splits text into chunks of chunk_size characters, with overlap
    characters repeated between consecutive chunks.

    Example with chunk_size=500, overlap=100:
      Chunk 0: characters   0 - 499
      Chunk 1: characters 400 - 899
      Chunk 2: characters 800 - 1299
      ...

    If overlap >= chunk_size, falls back to no overlap to avoid
    infinite loops.
    """
    if overlap >= chunk_size:
        overlap = 0

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def chunk_documents():
    """
    Loads and processes all documents marked with "always_load": false
    from facts/ and procedures/, then splits them into overlapping
    chunks (CHUNK_SIZE and CHUNK_OVERLAP from config.py).

    Returns a list of dictionaries in the format:
        [
            {
                "document_id": "mermaid_syntax_reference",
                "chunk_index": 0,
                "content": "..."
            },
            ...
        ]
    """
    documents = (
        kb.load_facts(only_always_load=False)
        + kb.load_procedures(only_always_load=False)
    )

    chunks = []
    for document in documents:
        text_chunks = _split_into_chunks(
            document["content"], CHUNK_SIZE, CHUNK_OVERLAP
        )

        for chunk_index, chunk_content in enumerate(text_chunks):
            chunks.append({
                "document_id": document["id"],
                "chunk_index": chunk_index,
                "content": chunk_content
            })

    return chunks


if __name__ == "__main__":
    result = chunk_documents()
    print(f"Generated {len(result)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    if result:
        print("First chunk:", result[0])