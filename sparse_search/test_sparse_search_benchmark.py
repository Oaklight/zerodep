"""Benchmarks comparing sparse_search against rank-bm25.

Requires: pip install rank-bm25
Run: pytest sparse_search/test_sparse_search_benchmark.py -v
"""

from __future__ import annotations

import random
import string

import pytest

from sparse_search import SparseIndex, _default_tokenize

rank_bm25 = pytest.importorskip("rank_bm25")
from rank_bm25 import BM25L as RefBM25L
from rank_bm25 import BM25Okapi as RefBM25Okapi
from rank_bm25 import BM25Plus as RefBM25Plus

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

CORPUS = [
    "the quick brown fox jumps over the lazy dog",
    "the quick brown fox",
    "the lazy dog sleeps all day long in the sun",
    "a brown cat chased the white mouse across the yard",
    "foxes are wild animals that live in forests",
    "dogs are loyal companions to humans",
    "the weather today is sunny and warm",
    "machine learning algorithms process large datasets",
    "natural language processing enables text understanding",
    "information retrieval systems help users find documents",
    "search engines index billions of web pages",
    "the brown fox and the lazy dog are friends",
    "quick sort is a fast sorting algorithm",
    "binary search trees provide efficient lookups",
    "the dog barked loudly at the passing car",
    "python is a popular programming language",
    "deep learning models require large amounts of data",
    "the fox ran quickly through the dense forest",
    "lazy evaluation defers computation until needed",
    "retrieval augmented generation combines search with LLMs",
]

QUERIES = [
    "quick brown fox",
    "lazy dog",
    "machine learning",
    "search retrieval",
    "python programming",
    "fox forest",
    "brown animals",
    "deep learning data",
]

TOKENIZED_CORPUS = [_default_tokenize(doc) for doc in CORPUS]


def _generate_large_corpus(
    n_docs: int, words_per_doc: int = 50, vocab_size: int = 5000
) -> tuple[list[str], list[list[str]]]:
    """Generate a synthetic corpus for performance benchmarks."""
    rng = random.Random(42)
    vocab = [
        "".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 10)))
        for _ in range(vocab_size)
    ]
    docs: list[str] = []
    tokenized: list[list[str]] = []
    for _ in range(n_docs):
        tokens = rng.choices(vocab, k=words_per_doc)
        docs.append(" ".join(tokens))
        tokenized.append(tokens)
    return docs, tokenized


# ---------------------------------------------------------------------------
# Correctness: ranking order comparison
# ---------------------------------------------------------------------------


class TestRankingCorrectness:
    """Verify that our BM25 variants produce the same ranking order
    as rank-bm25 for the same parameters.

    Note: absolute scores differ due to IDF formula variations,
    but ranking order should match.
    """

    def _get_our_ranking(
        self, variant: str, query: str, delta: float, top_k: int = 10
    ) -> list[str]:
        idx = SparseIndex(variant=variant, delta=delta)
        for i, doc in enumerate(CORPUS):
            idx.add(f"d{i}", doc)
        results = idx.search(query, top_k=top_k)
        return [r.doc_id for r in results]

    def _get_ref_ranking(
        self,
        ref_cls: type,
        query: str,
        delta: float | None = None,
        top_k: int = 10,
    ) -> list[str]:
        kwargs: dict = {"k1": 1.5, "b": 0.75}
        if delta is not None:
            kwargs["delta"] = delta
        ref = ref_cls(TOKENIZED_CORPUS, **kwargs)
        tokens = _default_tokenize(query)
        scores = ref.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [f"d{i}" for i, s in ranked[:top_k] if s > 0]

    @pytest.mark.parametrize("query", QUERIES)
    def test_bm25_okapi_ranking(self, query: str):
        """BM25 (delta=0) vs rank-bm25 BM25Okapi ranking order."""
        ours = self._get_our_ranking("bm25", query, delta=0.0)
        ref = self._get_ref_ranking(RefBM25Okapi, query)
        # Top results should match (allow minor reordering for tied scores)
        n = min(len(ours), len(ref), 5)
        if n > 0:
            assert set(ours[:n]) == set(ref[:n]), (
                f"Top-{n} mismatch for query {query!r}:\n"
                f"  ours: {ours[:n]}\n"
                f"  ref:  {ref[:n]}"
            )

    @pytest.mark.parametrize("query", QUERIES)
    def test_bm25plus_ranking(self, query: str):
        """BM25+ (delta=1) vs rank-bm25 BM25Plus ranking order."""
        ours = self._get_our_ranking("bm25", query, delta=1.0)
        ref = self._get_ref_ranking(RefBM25Plus, query, delta=1.0)
        n = min(len(ours), len(ref), 5)
        if n > 0:
            assert set(ours[:n]) == set(ref[:n]), (
                f"Top-{n} mismatch for query {query!r}:\n"
                f"  ours: {ours[:n]}\n"
                f"  ref:  {ref[:n]}"
            )

    @pytest.mark.parametrize("query", QUERIES)
    def test_bm25l_ranking(self, query: str):
        """BM25L vs rank-bm25 BM25L ranking order."""
        ours = self._get_our_ranking("bm25l", query, delta=0.5)
        ref = self._get_ref_ranking(RefBM25L, query, delta=0.5)
        n = min(len(ours), len(ref), 5)
        if n > 0:
            assert set(ours[:n]) == set(ref[:n]), (
                f"Top-{n} mismatch for query {query!r}:\n"
                f"  ours: {ours[:n]}\n"
                f"  ref:  {ref[:n]}"
            )


# ---------------------------------------------------------------------------
# Performance: indexing speed
# ---------------------------------------------------------------------------

LARGE_CORPUS, LARGE_TOKENIZED = _generate_large_corpus(1000)
MEDIUM_CORPUS, MEDIUM_TOKENIZED = _generate_large_corpus(200)


class TestIndexingPerformance:
    """Compare indexing (corpus loading) performance."""

    def test_index_1k_ours(self, benchmark):
        """Our SparseIndex: index 1000 documents."""

        def build():
            idx = SparseIndex()
            for i, doc in enumerate(LARGE_CORPUS):
                idx.add(f"d{i}", doc)
            return idx

        benchmark(build)

    def test_index_1k_rank_bm25(self, benchmark):
        """rank-bm25 BM25Okapi: index 1000 documents."""

        def build():
            return RefBM25Okapi(LARGE_TOKENIZED)

        benchmark(build)


# ---------------------------------------------------------------------------
# Performance: search speed
# ---------------------------------------------------------------------------


class TestSearchPerformance:
    """Compare search (scoring) performance."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        # Pre-build indexes
        self.our_idx = SparseIndex()
        for i, doc in enumerate(MEDIUM_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(MEDIUM_TOKENIZED)

        # Fixed query tokens for consistent benchmarking
        self.query = "quick brown fox search"
        self.query_tokens = _default_tokenize(self.query)

    def test_search_ours(self, benchmark):
        """Our SparseIndex: search 200-doc index."""
        benchmark(self.our_idx.search, self.query, top_k=10)

    def test_search_rank_bm25(self, benchmark):
        """rank-bm25 BM25Okapi: search 200-doc index."""
        benchmark(self.ref_bm25.get_scores, self.query_tokens)


# ---------------------------------------------------------------------------
# Performance: larger corpus search
# ---------------------------------------------------------------------------


class TestLargeSearchPerformance:
    """Compare search on larger corpus."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.our_idx = SparseIndex()
        for i, doc in enumerate(LARGE_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(LARGE_TOKENIZED)

        self.query = "quick brown fox search"
        self.query_tokens = _default_tokenize(self.query)

    def test_search_1k_ours(self, benchmark):
        """Our SparseIndex: search 1000-doc index."""
        benchmark(self.our_idx.search, self.query, top_k=10)

    def test_search_1k_rank_bm25(self, benchmark):
        """rank-bm25 BM25Okapi: search 1000-doc index."""
        benchmark(self.ref_bm25.get_scores, self.query_tokens)


# ---------------------------------------------------------------------------
# Performance: Bayesian calibration overhead
# ---------------------------------------------------------------------------


class TestCalibrationPerformance:
    """Measure Bayesian BM25 calibration overhead."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.idx_raw = SparseIndex()
        self.idx_cal = SparseIndex()
        for i, doc in enumerate(CORPUS):
            self.idx_raw.add(f"d{i}", doc)
            self.idx_cal.add(f"d{i}", doc)
        self.idx_cal.calibrate()
        self.query = "quick brown fox search"

    def test_calibrate_corpus(self, benchmark):
        """Benchmark calibrate() on 20-doc corpus."""
        idx = SparseIndex()
        for i, doc in enumerate(CORPUS):
            idx.add(f"d{i}", doc)
        benchmark(idx.calibrate)

    def test_search_raw(self, benchmark):
        """Baseline: raw BM25 search."""
        benchmark(self.idx_raw.search, self.query, top_k=10)

    def test_search_calibrated(self, benchmark):
        """Calibrated BM25 search (probability output)."""
        benchmark(self.idx_cal.search, self.query, top_k=10)
