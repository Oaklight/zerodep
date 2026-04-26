"""Correctness tests: zerodep sparse_search."""

from __future__ import annotations

import pytest

from sparse_search import (
    Result,
    SparseIndex,
    _default_tokenize,
    _log_odds_conjunction,
    _logit,
    _prob_or,
    _sigmoid,
    jaccard_similarity,
    mmr,
    rrf,
)

# ---------------------------------------------------------------------------
# Default tokenizer
# ---------------------------------------------------------------------------


class TestDefaultTokenizer:
    def test_basic(self):
        assert _default_tokenize("Hello World") == ["hello", "world"]

    def test_punctuation(self):
        assert _default_tokenize("foo, bar! baz?") == ["foo", "bar", "baz"]

    def test_unicode(self):
        tokens = _default_tokenize("café résumé")
        assert tokens == ["café", "résumé"]

    def test_empty(self):
        assert _default_tokenize("") == []
        assert _default_tokenize("   ") == []

    def test_numbers(self):
        assert _default_tokenize("item42 v2") == ["item42", "v2"]


# ---------------------------------------------------------------------------
# SparseIndex basics
# ---------------------------------------------------------------------------


class TestSparseIndexBasics:
    def test_create_empty(self):
        idx = SparseIndex()
        assert len(idx) == 0
        assert idx.doc_count == 0
        assert idx.vocab_size == 0

    def test_invalid_variant(self):
        with pytest.raises(ValueError, match="Unknown variant"):
            SparseIndex(variant="invalid")

    def test_add_and_contains(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        assert "d1" in idx
        assert "d2" not in idx
        assert len(idx) == 1

    def test_add_duplicate_raises(self):
        idx = SparseIndex()
        idx.add("d1", "hello")
        with pytest.raises(ValueError, match="already exists"):
            idx.add("d1", "world")

    def test_remove(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        idx.remove("d1")
        assert "d1" not in idx
        assert len(idx) == 0
        assert idx.vocab_size == 0

    def test_remove_missing_raises(self):
        idx = SparseIndex()
        with pytest.raises(KeyError, match="not found"):
            idx.remove("d1")

    def test_update(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        idx.update("d1", "foo bar")
        results = idx.search("hello")
        assert len(results) == 0
        results = idx.search("foo")
        assert len(results) == 1
        assert results[0].doc_id == "d1"

    def test_update_missing_raises(self):
        idx = SparseIndex()
        with pytest.raises(KeyError, match="not found"):
            idx.update("d1", "text")

    def test_metadata(self):
        idx = SparseIndex()
        meta = {"source": "arxiv", "year": 2024, "tags": ["ml", "nlp"]}
        idx.add("d1", "deep learning paper", metadata=meta)
        results = idx.search("deep learning")
        assert results[0].metadata == meta

    def test_custom_tokenizer(self):
        idx = SparseIndex(tokenize=lambda s: s.split("-"))
        idx.add("d1", "hello-world-foo")
        results = idx.search("world")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# BM25 scoring
# ---------------------------------------------------------------------------


class TestBM25Scoring:
    def _build_index(self, **kwargs):
        idx = SparseIndex(**kwargs)
        idx.add("d1", "the quick brown fox jumps over the lazy dog")
        idx.add("d2", "the quick brown fox")
        idx.add("d3", "the lazy dog sleeps all day long")
        return idx

    def test_basic_ranking(self):
        idx = self._build_index()
        results = idx.search("quick fox")
        assert len(results) >= 2
        # d2 should rank higher (shorter doc, same terms)
        doc_ids = [r.doc_id for r in results]
        assert doc_ids[0] == "d2"

    def test_idf_effect(self):
        idx = self._build_index()
        # "the" appears in all docs (low IDF), "jumps" in only one (high IDF)
        results_rare = idx.search("jumps")
        assert len(results_rare) == 1
        assert results_rare[0].doc_id == "d1"

    def test_nonexistent_term(self):
        idx = self._build_index()
        results = idx.search("xyznotexist")
        assert results == []

    def test_empty_query(self):
        idx = self._build_index()
        results = idx.search("")
        assert results == []

    def test_empty_index(self):
        idx = SparseIndex()
        results = idx.search("hello")
        assert results == []

    def test_top_k(self):
        idx = self._build_index()
        results = idx.search("the", top_k=1)
        assert len(results) <= 1

    def test_bm25_vs_bm25_no_delta(self):
        """BM25+ (delta=1) should give higher scores than classic BM25 (delta=0)."""
        idx_plus = self._build_index(delta=1.0)
        idx_classic = self._build_index(delta=0.0)

        r_plus = idx_plus.search("quick fox")
        r_classic = idx_classic.search("quick fox")

        assert r_plus[0].score > r_classic[0].score


class TestBM25LScoring:
    def test_bm25l_returns_results(self):
        idx = SparseIndex(variant="bm25l")
        idx.add("d1", "the quick brown fox")
        idx.add("d2", "the lazy dog")
        results = idx.search("quick fox")
        assert len(results) >= 1
        assert results[0].doc_id == "d1"

    def test_bm25l_long_doc_not_over_penalized(self):
        """BM25L should penalize long documents less than BM25+.

        With delta>0, BM25L and BM25+ apply the correction differently:
        BM25+ adds delta after TF normalization, BM25L adds delta before.
        BM25L's approach is more favorable to long documents.
        Note: with delta=0 the two formulas are mathematically equivalent.
        """
        long_text = "the quick brown fox " + " ".join(["padding"] * 100)
        short_text = "the quick brown fox"

        idx_bm25 = SparseIndex(variant="bm25", delta=1.0)
        idx_bm25.add("long", long_text)
        idx_bm25.add("short", short_text)

        idx_bm25l = SparseIndex(variant="bm25l", delta=1.0)
        idx_bm25l.add("long", long_text)
        idx_bm25l.add("short", short_text)

        r_bm25 = idx_bm25.search("quick brown fox")
        r_bm25l = idx_bm25l.search("quick brown fox")

        bm25_scores = {r.doc_id: r.score for r in r_bm25}
        bm25l_scores = {r.doc_id: r.score for r in r_bm25l}

        # BM25L should give the long doc a relatively higher score
        bm25_ratio = bm25_scores["long"] / bm25_scores["short"]
        bm25l_ratio = bm25l_scores["long"] / bm25l_scores["short"]

        assert bm25l_ratio > bm25_ratio


# ---------------------------------------------------------------------------
# BM25F (multi-field)
# ---------------------------------------------------------------------------


class TestBM25F:
    def test_field_weights_boost_title(self):
        idx = SparseIndex(field_weights={"title": 3.0, "body": 1.0})
        idx.add(
            "d1", {"title": "Python Guide", "body": "Learn Java and other languages"}
        )
        idx.add(
            "d2", {"title": "Java Guide", "body": "Learn Python programming basics"}
        )
        results = idx.search("python")
        # d1 has "python" in title (weight 3.0), d2 has it in body (weight 1.0)
        assert results[0].doc_id == "d1"

    def test_single_field_fallback(self):
        """When field_weights is set but content is a string, use _default."""
        idx = SparseIndex(field_weights={"_default": 1.0})
        idx.add("d1", "hello world")
        results = idx.search("hello")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# TF-IDF scoring
# ---------------------------------------------------------------------------


class TestTFIDFScoring:
    def test_basic_ranking(self):
        idx = SparseIndex(variant="tfidf")
        idx.add("d1", "the quick brown fox jumps over the lazy dog")
        idx.add("d2", "the quick brown fox")
        idx.add("d3", "the lazy dog sleeps all day long")
        results = idx.search("quick fox")
        assert len(results) >= 2
        assert results[0].doc_id == "d2"

    def test_cosine_scores_bounded(self):
        """Cosine similarity should be between 0 and 1."""
        idx = SparseIndex(variant="tfidf")
        idx.add("d1", "machine learning deep learning")
        idx.add("d2", "deep learning neural network")
        results = idx.search("deep learning")
        for r in results:
            assert 0.0 <= r.score <= 1.0 + 1e-9

    def test_identical_doc_query(self):
        """A document identical to the query should get high cosine score."""
        idx = SparseIndex(variant="tfidf")
        idx.add("d1", "hello world foo bar")
        idx.add("d2", "completely different text here")
        results = idx.search("hello world foo bar")
        assert results[0].doc_id == "d1"
        assert results[0].score > 0.9

    def test_no_matching_terms(self):
        idx = SparseIndex(variant="tfidf")
        idx.add("d1", "hello world")
        results = idx.search("xyznotexist")
        assert results == []


# ---------------------------------------------------------------------------
# Metadata filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    def _build_index(self):
        idx = SparseIndex()
        idx.add("d1", "machine learning", metadata={"source": "arxiv", "year": 2024})
        idx.add("d2", "machine learning", metadata={"source": "blog", "year": 2023})
        idx.add("d3", "machine learning", metadata={"source": "arxiv", "year": 2023})
        return idx

    def test_exact_filter(self):
        idx = self._build_index()
        results = idx.search("machine learning", filters={"source": "arxiv"})
        doc_ids = {r.doc_id for r in results}
        assert doc_ids == {"d1", "d3"}

    def test_callable_filter(self):
        idx = self._build_index()
        results = idx.search("machine learning", filters={"year": lambda y: y >= 2024})
        assert len(results) == 1
        assert results[0].doc_id == "d1"

    def test_multiple_filters(self):
        idx = self._build_index()
        results = idx.search(
            "machine learning", filters={"source": "arxiv", "year": 2023}
        )
        assert len(results) == 1
        assert results[0].doc_id == "d3"

    def test_no_metadata_excluded(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")  # no metadata
        idx.add("d2", "hello world", metadata={"tag": "test"})
        results = idx.search("hello", filters={"tag": "test"})
        assert len(results) == 1
        assert results[0].doc_id == "d2"


# ---------------------------------------------------------------------------
# Persistence: JSON
# ---------------------------------------------------------------------------


class TestPersistenceJSON:
    def test_save_load_roundtrip(self, tmp_path):
        idx = SparseIndex(variant="bm25", k1=1.2, b=0.8, delta=0.5)
        idx.add("d1", "hello world", metadata={"tag": "test"})
        idx.add("d2", "foo bar baz")

        path = str(tmp_path / "index.json")
        idx.save(path)

        loaded = SparseIndex.load(path)
        assert loaded.variant == "bm25"
        assert loaded.k1 == 1.2
        assert loaded.b == 0.8
        assert loaded.delta == 0.5
        assert len(loaded) == 2
        assert "d1" in loaded
        assert "d2" in loaded

        results = loaded.search("hello")
        assert len(results) == 1
        assert results[0].doc_id == "d1"
        assert results[0].metadata == {"tag": "test"}

    def test_save_load_multifield(self, tmp_path):
        idx = SparseIndex(field_weights={"title": 2.0, "body": 1.0})
        idx.add("d1", {"title": "Python", "body": "A programming language"})

        path = str(tmp_path / "index.json")
        idx.save(path)

        loaded = SparseIndex.load(path)
        assert loaded.field_weights == {"title": 2.0, "body": 1.0}
        results = loaded.search("python")
        assert len(results) == 1

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            SparseIndex.load("/tmp/nonexistent_index_file.json")

    def test_explicit_format(self, tmp_path):
        idx = SparseIndex()
        idx.add("d1", "hello")
        path = str(tmp_path / "myindex.dat")
        idx.save(path, format="json")
        loaded = SparseIndex.load(path)
        assert len(loaded) == 1


# ---------------------------------------------------------------------------
# Persistence: SQLite
# ---------------------------------------------------------------------------


class TestPersistenceSQLite:
    def test_save_load_roundtrip(self, tmp_path):
        idx = SparseIndex(variant="bm25l", k1=1.8, b=0.6, delta=0.3)
        idx.add("d1", "hello world", metadata={"year": 2024})
        idx.add("d2", "foo bar baz")

        path = str(tmp_path / "index.db")
        idx.save(path)

        loaded = SparseIndex.load(path)
        assert loaded.variant == "bm25l"
        assert loaded.k1 == 1.8
        assert loaded.b == 0.6
        assert loaded.delta == 0.3
        assert len(loaded) == 2

        results = loaded.search("hello")
        assert len(results) == 1
        assert results[0].doc_id == "d1"
        assert results[0].metadata == {"year": 2024}

    def test_explicit_sqlite_format(self, tmp_path):
        idx = SparseIndex()
        idx.add("d1", "test content")
        path = str(tmp_path / "index.custom")
        idx.save(path, format="sqlite")
        loaded = SparseIndex.load(path)
        assert len(loaded) == 1

    def test_overwrite_existing(self, tmp_path):
        idx = SparseIndex()
        idx.add("d1", "hello")
        path = str(tmp_path / "index.db")
        idx.save(path)

        idx2 = SparseIndex()
        idx2.add("d2", "world")
        idx2.save(path)

        loaded = SparseIndex.load(path)
        assert len(loaded) == 1
        assert "d2" in loaded

    def test_invalid_format_raises(self, tmp_path):
        idx = SparseIndex()
        with pytest.raises(ValueError, match="Unknown format"):
            idx.save(str(tmp_path / "x"), format="xml")


# ---------------------------------------------------------------------------
# Dynamic operations
# ---------------------------------------------------------------------------


class TestDynamicOperations:
    def test_add_remove_add(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        idx.remove("d1")
        idx.add("d1", "foo bar")
        results = idx.search("foo")
        assert len(results) == 1
        assert results[0].doc_id == "d1"

    def test_remove_updates_df(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        idx.add("d2", "hello there")
        assert idx._df["hello"] == 2
        idx.remove("d1")
        assert idx._df["hello"] == 1

    def test_remove_cleans_empty_terms(self):
        idx = SparseIndex()
        idx.add("d1", "unique_term_xyz")
        assert "unique_term_xyz" in idx._index
        idx.remove("d1")
        assert "unique_term_xyz" not in idx._index
        assert "unique_term_xyz" not in idx._df

    def test_update_preserves_metadata(self):
        idx = SparseIndex()
        idx.add("d1", "old text", metadata={"v": 1})
        idx.update("d1", "new text", metadata={"v": 2})
        results = idx.search("new")
        assert results[0].metadata == {"v": 2}

    def test_scores_consistent_after_mutations(self):
        """Scores should be consistent regardless of insertion order."""
        idx1 = SparseIndex()
        idx1.add("d1", "alpha beta gamma")
        idx1.add("d2", "beta gamma delta")

        idx2 = SparseIndex()
        idx2.add("d2", "beta gamma delta")
        idx2.add("d1", "alpha beta gamma")

        r1 = idx1.search("beta gamma")
        r2 = idx2.search("beta gamma")

        scores1 = {r.doc_id: r.score for r in r1}
        scores2 = {r.doc_id: r.score for r in r2}

        assert scores1 == pytest.approx(scores2)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_doc(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        results = idx.search("hello")
        assert len(results) == 1

    def test_single_word_doc(self):
        idx = SparseIndex()
        idx.add("d1", "hello")
        results = idx.search("hello")
        assert len(results) == 1

    def test_repeated_terms_in_query(self):
        idx = SparseIndex()
        idx.add("d1", "hello world")
        results = idx.search("hello hello hello")
        assert len(results) == 1

    def test_large_top_k(self):
        idx = SparseIndex()
        idx.add("d1", "test")
        results = idx.search("test", top_k=1000)
        assert len(results) == 1

    def test_unicode_content(self):
        idx = SparseIndex()
        idx.add("d1", "café résumé naïve")
        results = idx.search("café")
        assert len(results) == 1

    def test_numeric_tokens(self):
        idx = SparseIndex()
        idx.add("d1", "version 42 release")
        results = idx.search("42")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Bayesian BM25 calibration
# ---------------------------------------------------------------------------


class TestBayesianCalibration:
    """Tests for Bayesian BM25 probabilistic calibration."""

    def _build_index(self) -> SparseIndex:
        idx = SparseIndex()
        idx.add("d1", "the quick brown fox jumps over the lazy dog")
        idx.add("d2", "the quick brown fox")
        idx.add("d3", "the lazy dog sleeps all day long")
        idx.add("d4", "a fast red car drives on the highway")
        idx.add("d5", "python programming language is great for data science")
        idx.add("d6", "machine learning and artificial intelligence")
        idx.add("d7", "the brown fox is quick and clever")
        idx.add("d8", "dogs and cats are popular pets worldwide")
        idx.add("d9", "natural language processing with transformers")
        idx.add("d10", "search engines use inverted indexes for retrieval")
        return idx

    def test_sigmoid_logit_inverse(self):
        for p in [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
            assert abs(_sigmoid(_logit(p)) - p) < 1e-9

    def test_sigmoid_extremes(self):
        assert abs(_sigmoid(0.0) - 0.5) < 1e-9
        assert _sigmoid(100.0) > 0.999
        assert _sigmoid(-100.0) < 0.001

    def test_calibrated_scores_bounded(self):
        idx = self._build_index()
        idx.calibrate()
        results = idx.search("quick brown fox", top_k=20)
        assert len(results) > 0
        for r in results:
            assert 0.0 <= r.score <= 1.0, f"Score {r.score} out of [0,1]"

    def test_calibrated_preserves_ranking(self):
        idx = self._build_index()
        raw_results = idx.search("quick brown fox", top_k=20)
        raw_order = [r.doc_id for r in raw_results]

        idx.calibrate()
        cal_results = idx.search("quick brown fox", top_k=20)
        cal_order = [r.doc_id for r in cal_results]

        assert raw_order == cal_order

    def test_auto_calibrate(self):
        idx = self._build_index()
        idx.calibrate()
        assert idx.calibrated is True
        assert idx._alpha is not None
        assert idx._beta is not None
        assert idx._alpha > 0
        assert idx._beta > 0

    def test_manual_calibrate(self):
        idx = self._build_index()
        idx.calibrate(alpha=2.0, beta=3.0)
        assert idx._alpha == 2.0
        assert idx._beta == 3.0
        assert idx.calibrated is True

    def test_base_rate_effect(self):
        idx = self._build_index()
        idx.calibrate(alpha=1.0, beta=2.0)
        results_no_br = idx.search("quick fox", top_k=5)

        idx.calibrate(alpha=1.0, beta=2.0, base_rate=0.05)
        results_br = idx.search("quick fox", top_k=5)

        # base_rate < 0.5 should pull probabilities down
        for r_no, r_br in zip(results_no_br, results_br):
            assert r_br.score <= r_no.score

    def test_prob_or_basic(self):
        assert abs(_prob_or([0.5, 0.5]) - 0.75) < 1e-9
        assert abs(_prob_or([0.0]) - 0.0) < 1e-6
        assert abs(_prob_or([1.0]) - 1.0) < 1e-6

    def test_log_odds_conjunction(self):
        result = _log_odds_conjunction([0.5, 0.5, 0.5])
        assert abs(result - 0.5) < 0.2
        result_high = _log_odds_conjunction([0.9, 0.9])
        assert result_high > 0.5

    def test_save_load_calibrated_json(self, tmp_path):
        idx = self._build_index()
        idx.calibrate(alpha=1.5, beta=2.5, base_rate=0.1)

        path = str(tmp_path / "idx.json")
        idx.save(path)
        loaded = SparseIndex.load(path)

        assert loaded.calibrated is True
        assert loaded._alpha == 1.5
        assert loaded._beta == 2.5
        assert loaded._base_rate == 0.1
        results = loaded.search("quick fox")
        for r in results:
            assert 0.0 <= r.score <= 1.0

    def test_save_load_calibrated_sqlite(self, tmp_path):
        idx = self._build_index()
        idx.calibrate(alpha=1.5, beta=2.5, base_rate=0.1)

        path = str(tmp_path / "idx.db")
        idx.save(path)
        loaded = SparseIndex.load(path)

        assert loaded.calibrated is True
        assert loaded._alpha == 1.5
        assert loaded._beta == 2.5
        assert loaded._base_rate == 0.1

    def test_uncalibrated_default(self):
        idx = self._build_index()
        assert idx.calibrated is False
        results = idx.search("quick fox", top_k=5)
        for r in results:
            assert r.score > 0

    def test_calibrate_empty_index_raises(self):
        idx = SparseIndex()
        with pytest.raises(RuntimeError, match="empty index"):
            idx.calibrate()


# ---------------------------------------------------------------------------
# Jaccard similarity
# ---------------------------------------------------------------------------


class TestJaccardSimilarity:
    def test_identical_sets(self):
        assert jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets(self):
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        # {a, b, c} & {b, c, d} = {b, c}, union = {a, b, c, d}
        assert jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(
            2 / 4
        )

    def test_both_empty(self):
        assert jaccard_similarity(set(), set()) == 0.0

    def test_one_empty(self):
        assert jaccard_similarity({"a"}, set()) == 0.0
        assert jaccard_similarity(set(), {"a"}) == 0.0

    def test_subset(self):
        # {a} & {a, b} = {a}, union = {a, b}
        assert jaccard_similarity({"a"}, {"a", "b"}) == pytest.approx(1 / 2)


# ---------------------------------------------------------------------------
# RRF (Reciprocal Rank Fusion)
# ---------------------------------------------------------------------------


class TestRRF:
    def test_basic_two_lists(self):
        list_a = [Result("d1", 10.0), Result("d2", 5.0)]
        list_b = [Result("d2", 0.9), Result("d3", 0.8)]
        fused = rrf(list_a, list_b, k=60)
        # d1: rank 1 in list_a only → 1/(60+1)
        # d2: rank 2 in list_a + rank 1 in list_b → 1/(60+2) + 1/(60+1)
        # d3: rank 2 in list_b only → 1/(60+2)
        scores = {r.doc_id: r.score for r in fused}
        assert scores["d2"] == pytest.approx(1.0 / 62 + 1.0 / 61)
        assert scores["d1"] == pytest.approx(1.0 / 61)
        assert scores["d3"] == pytest.approx(1.0 / 62)
        # d2 should rank first
        assert fused[0].doc_id == "d2"

    def test_single_list(self):
        results = [Result("d1", 5.0), Result("d2", 3.0)]
        fused = rrf(results, k=60)
        assert len(fused) == 2
        assert fused[0].doc_id == "d1"
        assert fused[0].score == pytest.approx(1.0 / 61)
        assert fused[1].score == pytest.approx(1.0 / 62)

    def test_disjoint_lists(self):
        list_a = [Result("d1", 1.0)]
        list_b = [Result("d2", 1.0)]
        fused = rrf(list_a, list_b)
        doc_ids = {r.doc_id for r in fused}
        assert doc_ids == {"d1", "d2"}

    def test_weights(self):
        list_a = [Result("d1", 1.0)]
        list_b = [Result("d1", 1.0)]
        fused_equal = rrf(list_a, list_b, k=60)
        fused_weighted = rrf(list_a, list_b, k=60, weights=[2.0, 1.0])
        # With weights=[2,1], d1 score = 2/(60+1) + 1/(60+1) = 3/61
        assert fused_weighted[0].score == pytest.approx(3.0 / 61)
        # With equal weights, d1 score = 1/(60+1) + 1/(60+1) = 2/61
        assert fused_equal[0].score == pytest.approx(2.0 / 61)

    def test_top_k(self):
        results = [Result(f"d{i}", float(10 - i)) for i in range(10)]
        fused = rrf(results, top_k=3)
        assert len(fused) == 3

    def test_metadata_from_best_score(self):
        list_a = [Result("d1", 10.0, metadata={"src": "a"})]
        list_b = [Result("d1", 20.0, metadata={"src": "b"})]
        fused = rrf(list_a, list_b)
        # d1 has higher score in list_b, so metadata should come from there
        assert fused[0].metadata == {"src": "b"}

    def test_all_empty_lists(self):
        fused = rrf([], [])
        assert fused == []

    def test_no_lists_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            rrf()

    def test_weights_mismatch_raises(self):
        with pytest.raises(ValueError, match="weights length"):
            rrf([Result("d1", 1.0)], weights=[1.0, 2.0])

    def test_k_zero_raises(self):
        with pytest.raises(ValueError, match="k must be positive"):
            rrf([Result("d1", 1.0)], k=0)

    def test_duplicate_doc_in_same_list(self):
        # Only the first occurrence should count
        results = [Result("d1", 10.0), Result("d1", 5.0)]
        fused = rrf(results, k=60)
        assert len(fused) == 1
        assert fused[0].score == pytest.approx(1.0 / 61)

    def test_composable_with_sparse_index(self):
        idx1 = SparseIndex()
        idx1.add("d1", "quick brown fox")
        idx1.add("d2", "lazy dog")

        idx2 = SparseIndex(variant="tfidf")
        idx2.add("d1", "quick brown fox")
        idx2.add("d2", "lazy dog")

        r1 = idx1.search("quick fox")
        r2 = idx2.search("quick fox")
        fused = rrf(r1, r2)
        assert len(fused) >= 1
        assert all(isinstance(r, Result) for r in fused)

    def test_three_lists(self):
        a = [Result("d1", 3.0), Result("d2", 2.0)]
        b = [Result("d2", 3.0), Result("d3", 2.0)]
        c = [Result("d3", 3.0), Result("d1", 2.0)]
        fused = rrf(a, b, c, k=60)
        # Each doc appears twice: at rank 1 and rank 2 in different lists
        scores = {r.doc_id: r.score for r in fused}
        # All three docs should have equal scores
        assert scores["d1"] == pytest.approx(scores["d2"])
        assert scores["d2"] == pytest.approx(scores["d3"])


# ---------------------------------------------------------------------------
# MMR (Maximal Marginal Relevance)
# ---------------------------------------------------------------------------


class TestMMR:
    @staticmethod
    def _const_sim(a: Result, b: Result) -> float:
        """Constant similarity for testing."""
        return 0.5

    @staticmethod
    def _id_sim(a: Result, b: Result) -> float:
        """High similarity for same-prefix docs, zero otherwise."""
        return 1.0 if a.doc_id[:-1] == b.doc_id[:-1] else 0.0

    def test_basic_diversity(self):
        # Cluster A: d_a1 (high rel), d_a2 (medium rel) — similar to each other
        # Cluster B: d_b1 (medium rel) — different from A
        results = [
            Result("a1", 10.0),
            Result("a2", 9.0),
            Result("b1", 8.0),
        ]

        def sim(a: Result, b: Result) -> float:
            same_cluster = a.doc_id[0] == b.doc_id[0]
            return 0.9 if same_cluster else 0.1

        diverse = mmr(results, sim, lambda_=0.5, top_k=2)
        # Should pick a1 first (highest relevance), then b1 (more diverse)
        assert diverse[0].doc_id == "a1"
        assert diverse[1].doc_id == "b1"

    def test_lambda_one_preserves_order(self):
        results = [
            Result("d1", 10.0),
            Result("d2", 8.0),
            Result("d3", 5.0),
        ]
        reranked = mmr(results, self._const_sim, lambda_=1.0)
        assert [r.doc_id for r in reranked] == ["d1", "d2", "d3"]

    def test_lambda_zero_max_diversity(self):
        # With lambda=0, only diversity matters (minimize max similarity to selected)
        results = [
            Result("d1", 10.0),
            Result("d2", 9.0),
            Result("d3", 1.0),
        ]

        def sim(a: Result, b: Result) -> float:
            # d1 and d2 are very similar, d3 is different
            if {a.doc_id, b.doc_id} == {"d1", "d2"}:
                return 0.95
            return 0.1

        diverse = mmr(results, sim, lambda_=0.0)
        # First pick: all have max_sim=0 initially, so best_mmr = 0 for all;
        # among ties, first encountered wins → d1
        # Second pick: d2 sim to d1=0.95, d3 sim to d1=0.1 → d3 preferred
        assert diverse[0].doc_id == "d1"
        assert diverse[1].doc_id == "d3"

    def test_top_k(self):
        results = [Result(f"d{i}", float(10 - i)) for i in range(10)]
        reranked = mmr(results, self._const_sim, top_k=3)
        assert len(reranked) == 3

    def test_single_result(self):
        results = [Result("d1", 5.0)]
        reranked = mmr(results, self._const_sim)
        assert len(reranked) == 1
        assert reranked[0].doc_id == "d1"

    def test_empty_results(self):
        assert mmr([], self._const_sim) == []

    def test_invalid_lambda_raises(self):
        with pytest.raises(ValueError, match="lambda_"):
            mmr([Result("d1", 1.0)], self._const_sim, lambda_=-0.1)
        with pytest.raises(ValueError, match="lambda_"):
            mmr([Result("d1", 1.0)], self._const_sim, lambda_=1.1)

    def test_scores_are_mmr_values(self):
        results = [Result("d1", 10.0), Result("d2", 5.0)]
        reranked = mmr(results, self._const_sim, lambda_=0.5)
        # MMR score for d1 (first picked): lambda*1.0 - 0 = 0.5 (normalized score=1.0)
        assert reranked[0].score == pytest.approx(0.5)

    def test_metadata_preserved(self):
        results = [Result("d1", 5.0, metadata={"k": "v"})]
        reranked = mmr(results, self._const_sim)
        assert reranked[0].metadata == {"k": "v"}

    def test_all_identical_scores(self):
        results = [Result(f"d{i}", 5.0) for i in range(5)]
        reranked = mmr(results, self._const_sim, lambda_=0.5)
        assert len(reranked) == 5

    def test_composable_with_sparse_index(self):
        idx = SparseIndex()
        idx.add("d1", "quick brown fox")
        idx.add("d2", "lazy brown dog")
        idx.add("d3", "fast red car")

        search_results = idx.search("brown", top_k=10)
        tokens = {
            "d1": {"quick", "brown", "fox"},
            "d2": {"lazy", "brown", "dog"},
            "d3": {"fast", "red", "car"},
        }

        def sim(a, b):
            return jaccard_similarity(
                tokens.get(a.doc_id, set()), tokens.get(b.doc_id, set())
            )

        diverse = mmr(search_results, sim, lambda_=0.7, top_k=2)
        assert len(diverse) <= 2
        assert all(isinstance(r, Result) for r in diverse)

    def test_zero_score_normalization(self):
        """All scores zero should not cause division by zero."""
        results = [Result("d1", 0.0), Result("d2", 0.0)]
        reranked = mmr(results, self._const_sim, lambda_=0.5)
        assert len(reranked) == 2
