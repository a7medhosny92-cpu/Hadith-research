"""Tests for the dense-vector index (semantic search backend)."""

from __future__ import annotations

from app.search import VectorIndex


def test_search_ranks_by_cosine():
    vi = VectorIndex(dim=3)
    vi.add([1, 2, 3], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0]])
    hits = vi.search([1.0, 0.0, 0.0], k=3)
    assert [rid for rid, _ in hits] == [1, 3, 2]          # 1.0 > 0.6 > 0.0
    assert hits[0][1] == 1.0 and abs(hits[1][1] - 0.6) < 1e-6


def test_search_top_k_truncates():
    vi = VectorIndex(dim=2)
    vi.add([1, 2, 3, 4], [[1, 0], [0.9, 0.1], [0.1, 0.9], [0, 1]])
    assert len(vi.search([1.0, 0.0], k=2)) == 2


def test_empty_index_returns_nothing():
    assert VectorIndex(dim=4).search([1, 0, 0, 0], k=5) == []
    assert VectorIndex().count() == 0


def test_dim_inferred_from_first_add():
    vi = VectorIndex()
    vi.add([7], [[0.0, 1.0, 0.0, 0.0]])
    assert vi.dim == 4


def test_persists_to_disk(tmp_path):
    path = tmp_path / "vectors.db"
    vi = VectorIndex(path)
    vi.add([1, 2], [[1.0, 0.0], [0.0, 1.0]])
    vi.close()

    reopened = VectorIndex(path)
    assert reopened.count() == 2
    assert reopened.search([1.0, 0.0], k=1)[0][0] == 1
