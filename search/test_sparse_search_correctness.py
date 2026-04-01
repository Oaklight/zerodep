"""Correctness tests: zerodep sparse_search."""

from __future__ import annotations

import pytest
from sparse_search import SparseIndex, _default_tokenize

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
