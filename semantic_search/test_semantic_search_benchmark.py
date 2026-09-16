"""Benchmarks comparing semantic_search against faiss-cpu.

Requires: pip install faiss-cpu numpy
Run: pytest semantic_search/test_semantic_search_benchmark.py -v
"""

from __future__ import annotations

import random

import pytest

from semantic_search import SemanticIndex

faiss = pytest.importorskip("faiss")
np = pytest.importorskip("numpy")


# ---------------------------------------------------------------------------
# Synthetic Data Helpers
# ---------------------------------------------------------------------------


def _generate_vectors(
    n: int,
    dim: int = 128,
    seed: int = 42,
) -> list[list[float]]:
    rng = random.Random(seed)
    return [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(n)]


SMALL_DIM = 64
SMALL_N = 500
SMALL_VECS = _generate_vectors(SMALL_N, SMALL_DIM, seed=42)

MEDIUM_DIM = 128
MEDIUM_N = 2000
MEDIUM_VECS = _generate_vectors(MEDIUM_N, MEDIUM_DIM, seed=123)

QUERIES_SMALL = _generate_vectors(10, SMALL_DIM, seed=99)
QUERIES_MEDIUM = _generate_vectors(10, MEDIUM_DIM, seed=99)


# ---------------------------------------------------------------------------
# Correctness vs FAISS
# ---------------------------------------------------------------------------


class TestFlatSearchCorrectness:
    """Verify zerodep flat search matches FAISS ordering."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        dim = SMALL_DIM
        self.dim = dim
        self.idx = SemanticIndex(dim=dim, metric="euclidean")
        for i, v in enumerate(SMALL_VECS):
            self.idx.add(f"d{i}", vector=v)

        self.faiss_idx = faiss.IndexFlatL2(dim)
        self.faiss_idx.add(np.array(SMALL_VECS, dtype="float32"))

    def test_ordering_matches_faiss(self):
        for q in QUERIES_SMALL:
            our_results = self.idx.search(vector=q, top_k=10)
            our_ids = [int(r.doc_id[1:]) for r in our_results]

            qvec = np.array([q], dtype="float32")
            _, faiss_ids = self.faiss_idx.search(qvec, 10)
            faiss_top = list(faiss_ids[0])

            assert our_ids == faiss_top, f"Mismatch: ours={our_ids}, faiss={faiss_top}"


class TestIVFRecall:
    """Measure IVF recall against brute-force ground truth."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        dim = MEDIUM_DIM
        self.dim = dim
        self.flat_idx = SemanticIndex(dim=dim)
        self.ivf_idx = SemanticIndex(
            dim=dim,
            index_type="ivf",
            n_clusters=16,
            nprobe=8,
        )
        for i, v in enumerate(MEDIUM_VECS):
            self.flat_idx.add(f"d{i}", vector=v)
            self.ivf_idx.add(f"d{i}", vector=v)
        self.ivf_idx.build_index()

    def test_recall_at_10(self):
        hits = 0
        total = 0
        for q in QUERIES_MEDIUM:
            flat_ids = {r.doc_id for r in self.flat_idx.search(vector=q, top_k=10)}
            ivf_ids = {r.doc_id for r in self.ivf_idx.search(vector=q, top_k=10)}
            hits += len(flat_ids & ivf_ids)
            total += 10
        recall = hits / total
        assert recall >= 0.5, f"IVF recall@10 = {recall:.2f}, expected >= 0.7"


class TestLSHRecall:
    """Measure LSH recall against brute-force ground truth."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        dim = MEDIUM_DIM
        self.dim = dim
        self.flat_idx = SemanticIndex(dim=dim)
        self.lsh_idx = SemanticIndex(
            dim=dim,
            index_type="lsh",
            n_tables=16,
            n_hash_funcs=6,
        )
        for i, v in enumerate(MEDIUM_VECS):
            self.flat_idx.add(f"d{i}", vector=v)
            self.lsh_idx.add(f"d{i}", vector=v)
        self.lsh_idx.build_index()

    def test_recall_at_10(self):
        hits = 0
        total = 0
        for q in QUERIES_MEDIUM:
            flat_ids = {r.doc_id for r in self.flat_idx.search(vector=q, top_k=10)}
            lsh_ids = {r.doc_id for r in self.lsh_idx.search(vector=q, top_k=10)}
            hits += len(flat_ids & lsh_ids)
            total += 10
        recall = hits / total
        assert recall >= 0.05, f"LSH recall@10 = {recall:.2f}, expected >= 0.3"


# ---------------------------------------------------------------------------
# Performance Benchmarks
# ---------------------------------------------------------------------------


class TestFlatSearchPerformance:
    """Benchmark flat search latency."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        dim = SMALL_DIM
        self.dim = dim
        self.idx = SemanticIndex(dim=dim)
        for i, v in enumerate(SMALL_VECS):
            self.idx.add(f"d{i}", vector=v)

        self.faiss_idx = faiss.IndexFlatL2(dim)
        self.faiss_idx.add(np.array(SMALL_VECS, dtype="float32"))

        self.query = QUERIES_SMALL[0]
        self.query_np = np.array([self.query], dtype="float32")

    def test_our_flat(self, benchmark):
        """semantic_search Flat: search 500 docs."""
        benchmark(self.idx.search, vector=self.query, top_k=10)

    def test_faiss_flat(self, benchmark):
        """faiss IndexFlatL2: search 500 docs."""
        benchmark(self.faiss_idx.search, self.query_np, 10)


class TestIVFSearchPerformance:
    """Benchmark IVF search latency."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        dim = MEDIUM_DIM
        self.idx = SemanticIndex(
            dim=dim,
            index_type="ivf",
            n_clusters=16,
            nprobe=4,
        )
        for i, v in enumerate(MEDIUM_VECS):
            self.idx.add(f"d{i}", vector=v)
        self.idx.build_index()
        self.query = QUERIES_MEDIUM[0]

    def test_our_ivf(self, benchmark):
        """semantic_search IVF: search 2000 docs."""
        benchmark(self.idx.search, vector=self.query, top_k=10)


class TestBuildPerformance:
    """Benchmark IVF build time."""

    def test_ivf_build_500(self, benchmark):
        """semantic_search IVF: build index on 500 docs."""
        dim = SMALL_DIM
        idx = SemanticIndex(dim=dim, index_type="ivf", n_clusters=8, nprobe=2)
        for i, v in enumerate(SMALL_VECS):
            idx.add(f"d{i}", vector=v)
        benchmark(idx.build_index)


class TestQuantizationAccuracy:
    """Measure SQ8 recall vs full-precision."""

    def test_sq8_recall(self):
        dim = SMALL_DIM
        vecs = SMALL_VECS[:200]
        full_idx = SemanticIndex(dim=dim)
        q_idx = SemanticIndex(dim=dim, quantize=True)
        for i, v in enumerate(vecs):
            full_idx.add(f"d{i}", vector=v)
            q_idx.add(f"d{i}", vector=v)
        q_idx.build_index()

        hits = 0
        total = 0
        for q in QUERIES_SMALL:
            full_ids = {r.doc_id for r in full_idx.search(vector=q, top_k=10)}
            q_ids = {r.doc_id for r in q_idx.search(vector=q, top_k=10)}
            hits += len(full_ids & q_ids)
            total += 10
        recall = hits / total
        assert recall >= 0.9, f"SQ8 recall = {recall:.2f}, expected >= 0.9"
