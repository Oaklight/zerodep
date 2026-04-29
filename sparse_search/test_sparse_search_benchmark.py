"""Benchmarks comparing sparse_search against rank-bm25 and bm25s.

Requires: pip install rank-bm25 bm25s
Run: pytest sparse_search/test_sparse_search_benchmark.py -v
"""

from __future__ import annotations

import random
import string

import pytest

from sparse_search import (
    Result,
    SparseIndex,
    _default_tokenize,
    jaccard_similarity,
    mmr,
    rrf,
)

rank_bm25 = pytest.importorskip("rank_bm25")
from rank_bm25 import BM25L as RefBM25L
from rank_bm25 import BM25Okapi as RefBM25Okapi
from rank_bm25 import BM25Plus as RefBM25Plus

bm25s = pytest.importorskip("bm25s")

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

    def test_index_1k_bm25s(self, benchmark):
        """bm25s BM25: index 1000 documents."""

        def build():
            retriever = bm25s.BM25()
            tokens = bm25s.tokenize(LARGE_CORPUS, stopwords="en")
            retriever.index(tokens)
            return retriever

        benchmark(build)


# ---------------------------------------------------------------------------
# Performance: search speed
# ---------------------------------------------------------------------------


class TestSearchPerformance:
    """Compare search (scoring) performance on selective queries."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        # Pre-build indexes
        self.our_idx = SparseIndex()
        for i, doc in enumerate(MEDIUM_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(MEDIUM_TOKENIZED)

        self.bm25s_retriever = bm25s.BM25()
        self.bm25s_retriever.index(bm25s.tokenize(MEDIUM_CORPUS, stopwords="en"))

        # Fixed query tokens for consistent benchmarking
        self.query = "quick brown fox search"
        self.query_tokens = _default_tokenize(self.query)

    def test_search_ours(self, benchmark):
        """Our SparseIndex: search 200-doc index."""
        benchmark(self.our_idx.search, self.query, top_k=10)

    def test_search_rank_bm25(self, benchmark):
        """rank-bm25 BM25Okapi: search 200-doc index."""
        benchmark(self.ref_bm25.get_scores, self.query_tokens)

    def test_search_bm25s(self, benchmark):
        """bm25s BM25: search 200-doc index."""
        query_tokens = bm25s.tokenize(self.query, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )


# ---------------------------------------------------------------------------
# Performance: larger corpus search
# ---------------------------------------------------------------------------


class TestLargeSearchPerformance:
    """Compare search on larger corpus with selective queries."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.our_idx = SparseIndex()
        for i, doc in enumerate(LARGE_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(LARGE_TOKENIZED)

        self.bm25s_retriever = bm25s.BM25()
        self.bm25s_retriever.index(bm25s.tokenize(LARGE_CORPUS, stopwords="en"))

        self.query = "quick brown fox search"
        self.query_tokens = _default_tokenize(self.query)

    def test_search_1k_ours(self, benchmark):
        """Our SparseIndex: search 1000-doc index."""
        benchmark(self.our_idx.search, self.query, top_k=10)

    def test_search_1k_rank_bm25(self, benchmark):
        """rank-bm25 BM25Okapi: search 1000-doc index."""
        benchmark(self.ref_bm25.get_scores, self.query_tokens)

    def test_search_1k_bm25s(self, benchmark):
        """bm25s BM25: search 1000-doc index."""
        query_tokens = bm25s.tokenize(self.query, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )


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


# ---------------------------------------------------------------------------
# Performance: RRF
# ---------------------------------------------------------------------------


def _make_result_list(n: int, prefix: str, rng: random.Random) -> list[Result]:
    """Generate a list of n Results with random scores."""
    return [Result(f"{prefix}_d{i}", rng.uniform(0, 10)) for i in range(n)]


class TestRRFPerformance:
    def test_rrf_2_lists_1000_results(self, benchmark):
        """RRF: fuse 2 lists of 1000 results each."""
        rng = random.Random(42)
        list_a = _make_result_list(1000, "a", rng)
        list_b = _make_result_list(1000, "b", rng)
        benchmark(rrf, list_a, list_b, k=60, top_k=10)

    def test_rrf_10_lists_100_results(self, benchmark):
        """RRF: fuse 10 lists of 100 results each."""
        rng = random.Random(42)
        lists = [_make_result_list(100, f"l{i}", rng) for i in range(10)]
        benchmark(lambda: rrf(*lists, k=60, top_k=10))

    def test_rrf_overlapping_docs(self, benchmark):
        """RRF: fuse 2 lists with 50% overlap (500 shared doc_ids)."""
        rng = random.Random(42)
        shared = [Result(f"d{i}", rng.uniform(0, 10)) for i in range(500)]
        unique_a = [Result(f"a{i}", rng.uniform(0, 10)) for i in range(500)]
        unique_b = [Result(f"b{i}", rng.uniform(0, 10)) for i in range(500)]
        list_a = shared + unique_a
        list_b = [Result(r.doc_id, rng.uniform(0, 10)) for r in shared] + unique_b
        benchmark(rrf, list_a, list_b, k=60, top_k=10)


# ---------------------------------------------------------------------------
# Performance: MMR
# ---------------------------------------------------------------------------


class TestMMRPerformance:
    @staticmethod
    def _jaccard_sim(a: Result, b: Result) -> float:
        # Simulate token-based similarity using doc_id hash as proxy
        set_a = set(a.doc_id)
        set_b = set(b.doc_id)
        return jaccard_similarity(set_a, set_b)

    def test_mmr_100_candidates(self, benchmark):
        """MMR: re-rank 100 candidates, select top 10."""
        rng = random.Random(42)
        results = _make_result_list(100, "d", rng)
        benchmark(mmr, results, self._jaccard_sim, lambda_=0.5, top_k=10)

    def test_mmr_500_candidates(self, benchmark):
        """MMR: re-rank 500 candidates, select top 10."""
        rng = random.Random(42)
        results = _make_result_list(500, "d", rng)
        benchmark(mmr, results, self._jaccard_sim, lambda_=0.5, top_k=10)


# ---------------------------------------------------------------------------
# Performance: scale tests with Zipf-distributed vocabulary
# ---------------------------------------------------------------------------

# Zipf distribution: common words match many documents, rare words match few.
# This tests the realistic case where O(matched_docs) may approach O(N).

_ZIPF_VOCAB_SIZE = 10_000
_ZIPF_WORDS_PER_DOC = 80


def _generate_zipf_corpus(
    n_docs: int,
    vocab_size: int = _ZIPF_VOCAB_SIZE,
    words_per_doc: int = _ZIPF_WORDS_PER_DOC,
) -> tuple[list[str], list[list[str]]]:
    """Generate a corpus with Zipf-like word frequency distribution."""
    rng = random.Random(42)
    vocab = [
        "".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 10)))
        for _ in range(vocab_size)
    ]
    weights = [1.0 / (i + 1) ** 0.8 for i in range(vocab_size)]
    docs: list[str] = []
    tokenized: list[list[str]] = []
    for _ in range(n_docs):
        tokens = rng.choices(vocab, weights=weights, k=words_per_doc)
        docs.append(" ".join(tokens))
        tokenized.append(tokens)
    return docs, tokenized


ZIPF_1K_CORPUS, ZIPF_1K_TOKENIZED = _generate_zipf_corpus(1000)
ZIPF_10K_CORPUS, ZIPF_10K_TOKENIZED = _generate_zipf_corpus(10_000)

# Queries using common words (high df) — broad matches, many docs hit
_ZIPF_VOCAB = _generate_zipf_corpus(1)[0][0].split()  # just to get the vocab
_zipf_rng = random.Random(42)
_zipf_vocab = [
    "".join(_zipf_rng.choices(string.ascii_lowercase, k=_zipf_rng.randint(3, 10)))
    for _ in range(_ZIPF_VOCAB_SIZE)
]
BROAD_QUERY = f"{_zipf_vocab[0]} {_zipf_vocab[1]} {_zipf_vocab[2]}"
SELECTIVE_QUERY = f"{_zipf_vocab[5000]} {_zipf_vocab[7000]} {_zipf_vocab[9000]}"


class TestScaleSearch1K:
    """Compare search at 1K docs with Zipf vocabulary distribution."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.our_idx = SparseIndex()
        for i, doc in enumerate(ZIPF_1K_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(ZIPF_1K_TOKENIZED)

        self.bm25s_retriever = bm25s.BM25()
        self.bm25s_retriever.index(bm25s.tokenize(ZIPF_1K_CORPUS, stopwords="en"))

    def test_broad_query_ours(self, benchmark):
        """Our SparseIndex: broad query on 1K Zipf corpus."""
        benchmark(self.our_idx.search, BROAD_QUERY, top_k=10)

    def test_broad_query_rank_bm25(self, benchmark):
        """rank-bm25: broad query on 1K Zipf corpus."""
        tokens = _default_tokenize(BROAD_QUERY)
        benchmark(self.ref_bm25.get_scores, tokens)

    def test_broad_query_bm25s(self, benchmark):
        """bm25s: broad query on 1K Zipf corpus."""
        query_tokens = bm25s.tokenize(BROAD_QUERY, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )

    def test_selective_query_ours(self, benchmark):
        """Our SparseIndex: selective query on 1K Zipf corpus."""
        benchmark(self.our_idx.search, SELECTIVE_QUERY, top_k=10)

    def test_selective_query_rank_bm25(self, benchmark):
        """rank-bm25: selective query on 1K Zipf corpus."""
        tokens = _default_tokenize(SELECTIVE_QUERY)
        benchmark(self.ref_bm25.get_scores, tokens)

    def test_selective_query_bm25s(self, benchmark):
        """bm25s: selective query on 1K Zipf corpus."""
        query_tokens = bm25s.tokenize(SELECTIVE_QUERY, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )


class TestScaleSearch10K:
    """Compare search at 10K docs with Zipf vocabulary distribution."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.our_idx = SparseIndex()
        for i, doc in enumerate(ZIPF_10K_CORPUS):
            self.our_idx.add(f"d{i}", doc)

        self.ref_bm25 = RefBM25Okapi(ZIPF_10K_TOKENIZED)

        self.bm25s_retriever = bm25s.BM25()
        self.bm25s_retriever.index(bm25s.tokenize(ZIPF_10K_CORPUS, stopwords="en"))

    def test_broad_query_ours(self, benchmark):
        """Our SparseIndex: broad query on 10K Zipf corpus."""
        benchmark(self.our_idx.search, BROAD_QUERY, top_k=10)

    def test_broad_query_rank_bm25(self, benchmark):
        """rank-bm25: broad query on 10K Zipf corpus."""
        tokens = _default_tokenize(BROAD_QUERY)
        benchmark(self.ref_bm25.get_scores, tokens)

    def test_broad_query_bm25s(self, benchmark):
        """bm25s: broad query on 10K Zipf corpus."""
        query_tokens = bm25s.tokenize(BROAD_QUERY, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )

    def test_selective_query_ours(self, benchmark):
        """Our SparseIndex: selective query on 10K Zipf corpus."""
        benchmark(self.our_idx.search, SELECTIVE_QUERY, top_k=10)

    def test_selective_query_rank_bm25(self, benchmark):
        """rank-bm25: selective query on 10K Zipf corpus."""
        tokens = _default_tokenize(SELECTIVE_QUERY)
        benchmark(self.ref_bm25.get_scores, tokens)

    def test_selective_query_bm25s(self, benchmark):
        """bm25s: selective query on 10K Zipf corpus."""
        query_tokens = bm25s.tokenize(SELECTIVE_QUERY, stopwords="en")
        benchmark(
            self.bm25s_retriever.retrieve,
            query_tokens,
            k=10,
            return_as="documents",
            show_progress=False,
        )
