"""
Embedding Generator.

Takes the chunks produced by document_chunker.py, generates an
embedding for each one using EmbeddingsClient, and saves the result
to disk so semantic_search() can use it later without recomputing
embeddings on every run.
"""

import json
import logging
import os

from config import EMBEDDINGS_OUTPUT_PATH
from document_chunker import chunk_documents
from embeddings_client import EmbeddingsClient

logger = logging.getLogger(__name__)


def generate_embeddings(force=False):
    """
    Generates embeddings for every chunk and saves them to
    EMBEDDINGS_OUTPUT_PATH. If the output file already exists and
    force is False, it is reused instead of regenerating everything
    (avoids unnecessary calls to the embeddings model on every run).

    If the embeddings server fails partway through, everything
    computed so far is still saved to disk before the error is
    re-raised - a crash on chunk 15/40 doesn't throw away the first
    14 embeddings.
    """
    if not force and os.path.exists(EMBEDDINGS_OUTPUT_PATH):
        with open(EMBEDDINGS_OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    embeddings_client = EmbeddingsClient()
    chunks = chunk_documents()

    embedded_chunks = []
    try:
        for i, chunk in enumerate(chunks, start=1):
            embedding = embeddings_client.get_embedding(chunk["content"])
            embedded_chunks.append({**chunk, "embedding": embedding})
            logger.info(
                "%d/%d chunks embedded (%s #%d)",
                i, len(chunks), chunk['document_id'], chunk['chunk_index']
            )
    except RuntimeError as e:
        logger.error(
            "Failed after %d/%d chunks: %s",
            len(embedded_chunks), len(chunks), e
        )
        if embedded_chunks:
            with open(EMBEDDINGS_OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(embedded_chunks, f, ensure_ascii=False, indent=2)
            logger.info(
                "Partial progress saved to %s. Re-run with force=True to retry.",
                EMBEDDINGS_OUTPUT_PATH
            )
        raise

    with open(EMBEDDINGS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(embedded_chunks, f, ensure_ascii=False, indent=2)

    return embedded_chunks


if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging()

    result = generate_embeddings(force=True)
    logger.info(
        "%d chunks embedded and saved to %s",
        len(result), EMBEDDINGS_OUTPUT_PATH
    )