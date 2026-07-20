"""
Unit tests for EmbeddingsClient.cosine_similarity().

Covers all logical branches of the method:
- identical vectors (similarity = 1.0)
- orthogonal vectors (similarity = 0.0)
- opposite vectors (similarity = -1.0)
- different (non-orthogonal) vectors (0 < similarity < 1)
- zero-magnitude vector guard (division by zero protection)
"""

import math

import pytest

from embeddings_client import EmbeddingsClient


@pytest.fixture
def client():
    return EmbeddingsClient()


def test_identical_vectors_have_similarity_one(client):
    vec = [1.0, 2.0, 3.0]
    result = client.cosine_similarity(vec, vec)
    assert math.isclose(result, 1.0, rel_tol=1e-9)


def test_orthogonal_vectors_have_similarity_zero(client):
    vec1 = [1.0, 0.0]
    vec2 = [0.0, 1.0]
    result = client.cosine_similarity(vec1, vec2)
    assert math.isclose(result, 0.0, abs_tol=1e-9)


def test_opposite_vectors_have_similarity_negative_one(client):
    vec1 = [1.0, 2.0, 3.0]
    vec2 = [-1.0, -2.0, -3.0]
    result = client.cosine_similarity(vec1, vec2)
    assert math.isclose(result, -1.0, rel_tol=1e-9)


def test_different_vectors_have_similarity_between_bounds(client):
    vec1 = [1.0, 2.0, 3.0]
    vec2 = [4.0, 1.0, 0.5]
    result = client.cosine_similarity(vec1, vec2)
    assert -1.0 <= result <= 1.0
    # Sanity check against manual calculation.
    dot = (1.0 * 4.0) + (2.0 * 1.0) + (3.0 * 0.5)
    mag1 = math.sqrt(1.0**2 + 2.0**2 + 3.0**2)
    mag2 = math.sqrt(4.0**2 + 1.0**2 + 0.5**2)
    expected = dot / (mag1 * mag2)
    assert math.isclose(result, expected, rel_tol=1e-9)


def test_zero_magnitude_vector_returns_zero_not_error(client):
    """
    Covers the guard clause (magnitude1 == 0 or magnitude2 == 0),
    which prevents a ZeroDivisionError.
    """
    zero_vec = [0.0, 0.0, 0.0]
    normal_vec = [1.0, 2.0, 3.0]
    result = client.cosine_similarity(zero_vec, normal_vec)
    assert result == 0.0


def test_both_zero_magnitude_vectors_return_zero(client):
    zero_vec1 = [0.0, 0.0]
    zero_vec2 = [0.0, 0.0]
    result = client.cosine_similarity(zero_vec1, zero_vec2)
    assert result == 0.0