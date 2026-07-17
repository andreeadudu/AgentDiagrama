"""
Embeddings client.

Handles communication with the local embeddings model (Ollama) and
provides semantic search over previously generated embeddings.
"""

import json
import logging
import os

import requests

from config import (
    EMBEDDINGS_MODEL,
    EMBEDDINGS_ENDPOINT,
    EMBEDDINGS_OUTPUT_PATH,
    SEMANTIC_SEARCH_TOP_N,
    SEMANTIC_SEARCH_MIN_SIMILARITY,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 15


class EmbeddingsClient:
    def get_embedding(self, text: str) -> list[float]:
        """
        Requests an embedding vector for the given text from the
        embeddings model.

        Raises RuntimeError with a clear message if the embeddings
        server is unreachable, times out, or returns an unexpected
        response shape.
        """
        try:
            response = requests.post(
                EMBEDDINGS_ENDPOINT,
                json={
                    "model": EMBEDDINGS_MODEL,
                    "input": text
                },
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Could not reach the embeddings server at "
                f"{EMBEDDINGS_ENDPOINT}. Is it running? ({e})"
            ) from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"Embeddings server timed out after "
                f"{REQUEST_TIMEOUT_SECONDS}s. ({e})"
            ) from e
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Embeddings server returned an error: "
                f"{response.status_code} {response.text}"
            ) from e

        try:
            return response.json()["embeddings"][0]
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(
                f"Unexpected response shape from embeddings server: "
                f"{response.text}"
            ) from e

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Computes the cosine similarity between two embedding vectors.

        Returns a float in the range [-1, 1]:
        1.0  - vectors are semantically identical
        0.0  - vectors are unrelated
        -1.0 - vectors are semantically opposite

        General interpretation:
        > 0.9      very similar
        0.7 - 0.9  similar
        0.5 - 0.7  somewhat related
        < 0.5      likely unrelated
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def semantic_search(
        self,
        user_question: str,
        top_n: int = SEMANTIC_SEARCH_TOP_N,
        min_similarity: float = SEMANTIC_SEARCH_MIN_SIMILARITY,
    ):
        """
        Exercise 5 - Semantic Search.

        Searches, among the previously saved chunk embeddings
        (Exercise 4), for the ones most relevant to user_question.

        Returns a list of dictionaries, sorted descending by
        similarity, in the format:
            [
                {
                    "document_id": "mermaid_syntax_reference",
                    "chunk_index": 3,
                    "similarity": 0.94,
                    "content": "..."
                },
                ...
            ]

        Returns an empty list (rather than raising) if the store file
        is missing or corrupted, so a bad cache never crashes the
        conversation.
        """
        if not os.path.exists(EMBEDDINGS_OUTPUT_PATH):
            return []

        try:
            with open(EMBEDDINGS_OUTPUT_PATH, "r", encoding="utf-8") as f:
                embedded_chunks = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(
                "%s is corrupted (%s). Run embedding_generator.py again.",
                EMBEDDINGS_OUTPUT_PATH, e
            )
            return []

        question_embedding = self.get_embedding(user_question)

        results = []
        for chunk in embedded_chunks:
            similarity = self.cosine_similarity(
                question_embedding, chunk["embedding"]
            )

            if similarity < min_similarity:
                continue

            results.append({
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": similarity,
                "content": chunk["content"]
            })

        results.sort(key=lambda r: r["similarity"], reverse=True)

        return results[:top_n]