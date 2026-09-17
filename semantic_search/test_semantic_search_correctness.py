"""Correctness tests: zerodep semantic_search."""

from __future__ import annotations

import array
import hashlib
import math
import random

import pytest

from semantic_search import (
    Result,
    SemanticIndex,
    _cosine_distance,
    _dequantize_sq8_single,
    _euclidean_distance,
    _inner_product_distance,
    _normalize,
    _quantize_sq8,
    cosine_similarity,
    detect_zh_en,
    mmr,
    rrf,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic mock embedder: hash text to a fixed-dim vector."""
    dim = 8
    result = []
    for t in texts:
        h = hashlib.md5(t.encode()).digest()
        vec = [b / 255.0 for b in h[:dim]]
        norm = math.sqrt(sum(v * v for v in vec))
        result.append([v / norm for v in vec] if norm > 0 else vec)
    return result


def _make_vectors(n: int, dim: int, seed: int = 42) -> list[list[float]]:
    rng = random.Random(seed)
    return [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(n)]


# ---------------------------------------------------------------------------
# Distance Metrics
# ---------------------------------------------------------------------------


class TestDistanceMetrics:
    def test_cosine_identical(self):
        v = array.array("f", [1.0, 0.0, 0.0])
        q = [1.0, 0.0, 0.0]
        assert _cosine_distance(v, q, 3, 0) == pytest.approx(0.0, abs=1e-6)

    def test_cosine_orthogonal(self):
        v = array.array("f", [1.0, 0.0])
        q = [0.0, 1.0]
        assert _cosine_distance(v, q, 2, 0) == pytest.approx(1.0, abs=1e-6)

    def test_cosine_opposite(self):
        v = array.array("f", [1.0, 0.0])
        q = [-1.0, 0.0]
        assert _cosine_distance(v, q, 2, 0) == pytest.approx(2.0, abs=1e-6)

    def test_euclidean_identical(self):
        v = array.array("f", [1.0, 2.0, 3.0])
        q = [1.0, 2.0, 3.0]
        assert _euclidean_distance(v, q, 3, 0) == pytest.approx(0.0, abs=1e-6)

    def test_euclidean_known(self):
        v = array.array("f", [0.0, 0.0])
        q = [3.0, 4.0]
        assert _euclidean_distance(v, q, 2, 0) == pytest.approx(5.0, abs=1e-6)

    def test_inner_product_positive(self):
        v = array.array("f", [1.0, 2.0])
        q = [3.0, 4.0]
        d = _inner_product_distance(v, q, 2, 0)
        assert d == pytest.approx(-11.0, abs=1e-6)

    def test_offset_access(self):
        v = array.array("f", [0.0, 0.0, 1.0, 0.0])
        q = [1.0, 0.0]
        d0 = _cosine_distance(v, q, 2, 0)
        d1 = _cosine_distance(v, q, 2, 2)
        assert d0 == pytest.approx(1.0, abs=1e-6)
        assert d1 == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Normalize
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_unit_vector(self):
        v = _normalize([1.0, 0.0, 0.0])
        assert v == pytest.approx([1.0, 0.0, 0.0])

    def test_scaling(self):
        v = _normalize([3.0, 4.0])
        assert v == pytest.approx([0.6, 0.8])

    def test_zero_vector(self):
        v = _normalize([0.0, 0.0])
        assert v == [0.0, 0.0]


# ---------------------------------------------------------------------------
# SQ8 Quantization
# ---------------------------------------------------------------------------


class TestQuantizationSQ8:
    def test_roundtrip_accuracy(self):
        rng = random.Random(42)
        dim = 4
        n = 10
        vectors = array.array("f", [rng.gauss(0, 1) for _ in range(n * dim)])
        data, mins, steps = _quantize_sq8(vectors, dim, n)

        for i in range(n):
            restored = _dequantize_sq8_single(data, mins, steps, dim, i)
            for d in range(dim):
                original = vectors[i * dim + d]
                assert abs(restored[d] - original) < steps[d] + 1e-6

    def test_all_identical(self):
        dim = 3
        n = 5
        vectors = array.array("f", [1.0] * (n * dim))
        data, mins, steps = _quantize_sq8(vectors, dim, n)
        restored = _dequantize_sq8_single(data, mins, steps, dim, 0)
        assert restored == pytest.approx([1.0, 1.0, 1.0], abs=1e-5)


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------


class TestDetectZhEn:
    def test_pure_english(self):
        assert detect_zh_en("hello world") == "en"

    def test_pure_chinese(self):
        assert detect_zh_en("你好世界") == "zh"

    def test_mixed_mostly_chinese(self):
        assert detect_zh_en("使用Python进行数据分析") == "zh"

    def test_mixed_mostly_english(self):
        assert detect_zh_en("The character 中 means middle") == "en"

    def test_japanese_kana_pure(self):
        assert detect_zh_en("こんにちは") == "en"

    def test_japanese_kana_mixed_with_chinese(self):
        assert detect_zh_en("这是一段中文テスト") == "zh"

    def test_korean_hangul(self):
        assert detect_zh_en("한국어 텍스트") == "en"

    def test_empty_string(self):
        assert detect_zh_en("") == "en"

    def test_numbers_only(self):
        assert detect_zh_en("12345") == "en"

    def test_custom_threshold(self):
        assert detect_zh_en("ABC中", threshold=0.1) == "zh"
        assert detect_zh_en("ABC中", threshold=0.5) == "en"


# ---------------------------------------------------------------------------
# SemanticIndex Basics
# ---------------------------------------------------------------------------


class TestSemanticIndexBasics:
    def test_create_empty(self):
        idx = SemanticIndex(dim=4)
        assert len(idx) == 0
        assert idx.doc_count == 0
        assert idx.dim == 4

    def test_invalid_metric(self):
        with pytest.raises(ValueError, match="Unknown metric"):
            SemanticIndex(dim=4, metric="hamming")

    def test_invalid_index_type(self):
        with pytest.raises(ValueError, match="Unknown index_type"):
            SemanticIndex(dim=4, index_type="hnsw")

    def test_invalid_dim(self):
        with pytest.raises(ValueError, match="dim must be positive"):
            SemanticIndex(dim=0)

    def test_contains(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        assert "d1" in idx
        assert "d2" not in idx


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------


class TestSemanticIndexCRUD:
    def test_add_single(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("d1", vector=[1.0, 2.0])
        assert len(idx) == 1

    def test_add_duplicate_raises(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        with pytest.raises(ValueError, match="already exists"):
            idx.add("d1", vector=[0.0, 1.0])

    def test_add_no_vector_no_text_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Provide either vector or text"):
            idx.add("d1")

    def test_add_text_no_embed_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="text requires an embedding function"):
            idx.add("d1", text="hello")

    def test_add_wrong_dim_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Expected vector of dimension"):
            idx.add("d1", vector=[1.0, 2.0, 3.0])

    def test_remove_existing(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("d1", vector=[1.0, 0.0])
        idx.add("d2", vector=[0.0, 1.0])
        idx.remove("d1")
        assert len(idx) == 1
        assert "d1" not in idx
        assert "d2" in idx

    def test_remove_nonexistent_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(KeyError, match="not found"):
            idx.remove("missing")

    def test_update_existing(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("d1", vector=[1.0, 0.0])
        idx.update("d1", vector=[0.0, 1.0])
        assert len(idx) == 1
        results = idx.search(vector=[0.0, 1.0], top_k=1)
        assert results[0].doc_id == "d1"

    def test_update_nonexistent_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(KeyError, match="not found, use add"):
            idx.update("missing", vector=[1.0, 0.0])

    def test_metadata_preserved(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0], metadata={"tag": "first"})
        results = idx.search(vector=[1.0, 0.0], top_k=1)
        assert results[0].metadata == {"tag": "first"}

    def test_metadata_replaced_on_update(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0], metadata={"old": True})
        idx.update("d1", vector=[1.0, 0.0], metadata={"new": True})
        results = idx.search(vector=[1.0, 0.0], top_k=1)
        assert results[0].metadata == {"new": True}


# ---------------------------------------------------------------------------
# Batch Add
# ---------------------------------------------------------------------------


class TestAddMany:
    def test_basic(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add_many(
            ["d1", "d2", "d3"],
            vectors=[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        )
        assert len(idx) == 3
        assert "d1" in idx and "d2" in idx and "d3" in idx

    def test_with_metadata(self):
        idx = SemanticIndex(dim=2)
        idx.add_many(
            ["d1", "d2"],
            vectors=[[1.0, 0.0], [0.0, 1.0]],
            metadatas=[{"a": 1}, {"b": 2}],
        )
        results = idx.search(vector=[1.0, 0.0], top_k=2)
        meta_by_id = {r.doc_id: r.metadata for r in results}
        assert meta_by_id["d1"] == {"a": 1}
        assert meta_by_id["d2"] == {"b": 2}

    def test_with_texts(self):
        def fake_embed(texts):
            return [[float(i), float(i + 1)] for i in range(len(texts))]

        idx = SemanticIndex(dim=2, metric="euclidean", embed=fake_embed)
        idx.add_many(["d1", "d2"], texts=["hello", "world"])
        assert len(idx) == 2

    def test_duplicate_raises(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        with pytest.raises(ValueError, match="already exists"):
            idx.add_many(["d1", "d2"], vectors=[[0.0, 1.0], [1.0, 1.0]])

    def test_both_vectors_and_texts_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Provide either"):
            idx.add_many(["d1"], vectors=[[1.0, 0.0]], texts=["hi"])

    def test_neither_vectors_nor_texts_raises(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Provide either"):
            idx.add_many(["d1"])

    def test_length_mismatch_vectors(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Length mismatch"):
            idx.add_many(["d1", "d2"], vectors=[[1.0, 0.0]])

    def test_length_mismatch_metadatas(self):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Length mismatch"):
            idx.add_many(
                ["d1", "d2"],
                vectors=[[1.0, 0.0], [0.0, 1.0]],
                metadatas=[{"a": 1}],
            )

    def test_search_after_add_many(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add_many(
            ["d1", "d2", "d3"],
            vectors=[[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]],
        )
        results = idx.search(vector=[1.0, 0.0], top_k=1)
        assert results[0].doc_id == "d1"


# ---------------------------------------------------------------------------
# Flat Search
# ---------------------------------------------------------------------------


class TestFlatSearch:
    def test_exact_nn(self):
        idx = SemanticIndex(dim=3)
        idx.add("a", vector=[1.0, 0.0, 0.0])
        idx.add("b", vector=[0.0, 1.0, 0.0])
        idx.add("c", vector=[0.9, 0.1, 0.0])
        results = idx.search(vector=[1.0, 0.0, 0.0], top_k=2)
        assert results[0].doc_id == "a"
        assert results[1].doc_id == "c"

    def test_top_k_truncation(self):
        idx = SemanticIndex(dim=2)
        for i in range(10):
            idx.add(f"d{i}", vector=[float(i), 0.0])
        results = idx.search(vector=[5.0, 0.0], top_k=3)
        assert len(results) == 3

    def test_empty_index(self):
        idx = SemanticIndex(dim=2)
        results = idx.search(vector=[1.0, 0.0])
        assert results == []

    def test_euclidean_metric(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("a", vector=[0.0, 0.0])
        idx.add("b", vector=[3.0, 4.0])
        results = idx.search(vector=[1.0, 0.0], top_k=2)
        assert results[0].doc_id == "a"

    def test_inner_product_metric(self):
        idx = SemanticIndex(dim=2, metric="inner_product")
        idx.add("a", vector=[1.0, 0.0])
        idx.add("b", vector=[10.0, 0.0])
        results = idx.search(vector=[1.0, 0.0], top_k=2)
        assert results[0].doc_id == "b"

    def test_filters_exact(self):
        idx = SemanticIndex(dim=2)
        idx.add("a", vector=[1.0, 0.0], metadata={"lang": "en"})
        idx.add("b", vector=[0.9, 0.1], metadata={"lang": "zh"})
        results = idx.search(vector=[1.0, 0.0], top_k=2, filters={"lang": "zh"})
        assert len(results) == 1
        assert results[0].doc_id == "b"

    def test_filters_callable(self):
        idx = SemanticIndex(dim=2)
        idx.add("a", vector=[1.0, 0.0], metadata={"year": 2023})
        idx.add("b", vector=[0.9, 0.1], metadata={"year": 2025})
        results = idx.search(
            vector=[1.0, 0.0], top_k=2, filters={"year": lambda y: y > 2024}
        )
        assert len(results) == 1
        assert results[0].doc_id == "b"


# ---------------------------------------------------------------------------
# IVF Index
# ---------------------------------------------------------------------------


class TestIVFIndex:
    def test_build_and_search(self):
        dim = 8
        idx = SemanticIndex(dim=dim, index_type="ivf", n_clusters=4, nprobe=2)
        vecs = _make_vectors(50, dim)
        for i, v in enumerate(vecs):
            idx.add(f"d{i}", vector=v)
        idx.build_index()
        results = idx.search(vector=vecs[0], top_k=5)
        assert len(results) > 0
        assert results[0].doc_id == "d0"

    def test_recall_vs_flat(self):
        dim = 16
        vecs = _make_vectors(200, dim, seed=123)
        flat_idx = SemanticIndex(dim=dim)
        ivf_idx = SemanticIndex(dim=dim, index_type="ivf", n_clusters=8, nprobe=4)
        for i, v in enumerate(vecs):
            flat_idx.add(f"d{i}", vector=v)
            ivf_idx.add(f"d{i}", vector=v)
        ivf_idx.build_index()

        rng = random.Random(99)
        hits = 0
        trials = 20
        for _ in range(trials):
            q = [rng.gauss(0, 1) for _ in range(dim)]
            flat_ids = {r.doc_id for r in flat_idx.search(vector=q, top_k=10)}
            ivf_ids = {r.doc_id for r in ivf_idx.search(vector=q, top_k=10)}
            hits += len(flat_ids & ivf_ids)
        recall = hits / (trials * 10)
        assert recall >= 0.7, f"IVF recall {recall:.2f} below 0.7"

    def test_auto_build(self):
        dim = 4
        idx = SemanticIndex(dim=dim, index_type="ivf", n_clusters=2, nprobe=1)
        for i in range(10):
            idx.add(f"d{i}", vector=_make_vectors(1, dim, seed=i)[0])
        results = idx.search(vector=[1.0, 0.0, 0.0, 0.0], top_k=3)
        assert len(results) > 0


# ---------------------------------------------------------------------------
# LSH Index
# ---------------------------------------------------------------------------


class TestLSHIndex:
    def test_build_and_search(self):
        dim = 8
        idx = SemanticIndex(dim=dim, index_type="lsh", n_tables=4, n_hash_funcs=6)
        vecs = _make_vectors(50, dim)
        for i, v in enumerate(vecs):
            idx.add(f"d{i}", vector=v)
        idx.build_index()
        results = idx.search(vector=vecs[0], top_k=5)
        assert len(results) > 0

    def test_recall_vs_flat(self):
        dim = 16
        vecs = _make_vectors(200, dim, seed=456)
        flat_idx = SemanticIndex(dim=dim)
        lsh_idx = SemanticIndex(dim=dim, index_type="lsh", n_tables=10, n_hash_funcs=8)
        for i, v in enumerate(vecs):
            flat_idx.add(f"d{i}", vector=v)
            lsh_idx.add(f"d{i}", vector=v)
        lsh_idx.build_index()

        rng = random.Random(99)
        hits = 0
        trials = 20
        for _ in range(trials):
            q = [rng.gauss(0, 1) for _ in range(dim)]
            flat_ids = {r.doc_id for r in flat_idx.search(vector=q, top_k=10)}
            lsh_ids = {r.doc_id for r in lsh_idx.search(vector=q, top_k=10)}
            hits += len(flat_ids & lsh_ids)
        recall = hits / (trials * 10)
        assert recall >= 0.3, f"LSH recall {recall:.2f} below 0.3"


# ---------------------------------------------------------------------------
# Text Embedding
# ---------------------------------------------------------------------------


class TestTextEmbedding:
    def test_add_with_text(self):
        idx = SemanticIndex(dim=8, embed=_mock_embed)
        idx.add("d1", text="hello world")
        assert len(idx) == 1

    def test_search_with_text(self):
        idx = SemanticIndex(dim=8, embed=_mock_embed)
        idx.add("d1", text="hello world")
        idx.add("d2", text="goodbye world")
        results = idx.search(text="hello world", top_k=1)
        assert results[0].doc_id == "d1"

    def test_embed_dim_mismatch(self):
        def bad_embed(texts):
            return [[1.0, 2.0, 3.0] for _ in texts]

        idx = SemanticIndex(dim=2, embed=bad_embed)
        with pytest.raises(ValueError, match="Expected vector of dimension"):
            idx.add("d1", text="test")


# ---------------------------------------------------------------------------
# Cosine Normalization
# ---------------------------------------------------------------------------


class TestCosineNormalization:
    def test_non_unit_input(self):
        idx = SemanticIndex(dim=2, metric="cosine")
        idx.add("d1", vector=[10.0, 0.0])
        idx.add("d2", vector=[0.0, 10.0])
        results = idx.search(vector=[5.0, 0.0], top_k=1)
        assert results[0].doc_id == "d1"
        assert results[0].score == pytest.approx(1.0, abs=1e-5)


# ---------------------------------------------------------------------------
# Persistence (JSON)
# ---------------------------------------------------------------------------


class TestPersistenceJSON:
    def test_roundtrip(self, tmp_path):
        path = str(tmp_path / "idx.json")
        idx = SemanticIndex(dim=3)
        idx.add("a", vector=[1.0, 0.0, 0.0], metadata={"k": "v"})
        idx.add("b", vector=[0.0, 1.0, 0.0])
        idx.save(path)

        loaded = SemanticIndex.load(path)
        assert loaded.doc_count == 2
        results = loaded.search(vector=[1.0, 0.0, 0.0], top_k=1)
        assert results[0].doc_id == "a"
        assert results[0].metadata == {"k": "v"}

    def test_ivf_roundtrip(self, tmp_path):
        path = str(tmp_path / "idx.json")
        dim = 8
        idx = SemanticIndex(dim=dim, index_type="ivf", n_clusters=3, nprobe=2)
        vecs = _make_vectors(30, dim)
        for i, v in enumerate(vecs):
            idx.add(f"d{i}", vector=v)
        idx.build_index()
        idx.save(path)

        loaded = SemanticIndex.load(path)
        r1 = idx.search(vector=vecs[0], top_k=3)
        r2 = loaded.search(vector=vecs[0], top_k=3)
        assert [r.doc_id for r in r1] == [r.doc_id for r in r2]

    def test_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            SemanticIndex.load("/nonexistent/path.json")

    def test_explicit_format(self, tmp_path):
        path = str(tmp_path / "idx.dat")
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        idx.save(path, fmt="json")
        loaded = SemanticIndex.load(path)
        assert loaded.doc_count == 1

    def test_invalid_format(self, tmp_path):
        idx = SemanticIndex(dim=2)
        with pytest.raises(ValueError, match="Unknown format"):
            idx.save(str(tmp_path / "x"), fmt="parquet")


# ---------------------------------------------------------------------------
# Persistence (SQLite)
# ---------------------------------------------------------------------------


class TestPersistenceSQLite:
    def test_roundtrip(self, tmp_path):
        path = str(tmp_path / "idx.db")
        idx = SemanticIndex(dim=3, metric="euclidean")
        idx.add("a", vector=[1.0, 2.0, 3.0], metadata={"x": 1})
        idx.add("b", vector=[4.0, 5.0, 6.0])
        idx.save(path)

        loaded = SemanticIndex.load(path)
        assert loaded.doc_count == 2
        results = loaded.search(vector=[1.0, 2.0, 3.0], top_k=1)
        assert results[0].doc_id == "a"
        assert results[0].metadata == {"x": 1}

    def test_overwrite(self, tmp_path):
        path = str(tmp_path / "idx.db")
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        idx.save(path)
        idx.add("d2", vector=[0.0, 1.0])
        idx.save(path)
        loaded = SemanticIndex.load(path)
        assert loaded.doc_count == 2

    def test_explicit_sqlite(self, tmp_path):
        path = str(tmp_path / "idx.txt")
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        idx.save(path, fmt="sqlite")
        loaded = SemanticIndex.load(path)
        assert loaded.doc_count == 1


# ---------------------------------------------------------------------------
# Persistence (Quantized)
# ---------------------------------------------------------------------------


class TestPersistenceQuantized:
    def test_json_roundtrip(self, tmp_path):
        path = str(tmp_path / "q.json")
        idx = SemanticIndex(dim=4, quantize=True)
        for i in range(10):
            idx.add(f"d{i}", vector=_make_vectors(1, 4, seed=i)[0])
        idx.build_index()
        idx.save(path)
        loaded = SemanticIndex.load(path)
        assert loaded._sq8_data is not None
        assert loaded.doc_count == 10


# ---------------------------------------------------------------------------
# Dynamic Operations
# ---------------------------------------------------------------------------


class TestDynamicOperations:
    def test_add_remove_readd(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        idx.remove("d1")
        idx.add("d1", vector=[0.0, 1.0])
        results = idx.search(vector=[0.0, 1.0], top_k=1)
        assert results[0].doc_id == "d1"

    def test_remove_middle_preserves_others(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("a", vector=[1.0, 0.0])
        idx.add("b", vector=[0.0, 1.0])
        idx.add("c", vector=[1.0, 1.0])
        idx.remove("b")
        assert len(idx) == 2
        results = idx.search(vector=[1.0, 1.0], top_k=1)
        assert results[0].doc_id == "c"

    def test_update_search_correctness(self):
        idx = SemanticIndex(dim=2, metric="euclidean")
        idx.add("d1", vector=[0.0, 0.0])
        idx.add("d2", vector=[10.0, 10.0])
        idx.update("d1", vector=[9.0, 9.0])
        results = idx.search(vector=[10.0, 10.0], top_k=1)
        assert results[0].doc_id == "d2"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_doc(self):
        idx = SemanticIndex(dim=2)
        idx.add("only", vector=[1.0, 0.0])
        results = idx.search(vector=[0.5, 0.5], top_k=5)
        assert len(results) == 1

    def test_top_k_larger_than_n(self):
        idx = SemanticIndex(dim=2)
        idx.add("d1", vector=[1.0, 0.0])
        results = idx.search(vector=[1.0, 0.0], top_k=100)
        assert len(results) == 1

    def test_high_dim(self):
        dim = 768
        idx = SemanticIndex(dim=dim)
        rng = random.Random(42)
        v1 = [rng.gauss(0, 1) for _ in range(dim)]
        v2 = [rng.gauss(0, 1) for _ in range(dim)]
        idx.add("d1", vector=v1)
        idx.add("d2", vector=v2)
        results = idx.search(vector=v1, top_k=1)
        assert results[0].doc_id == "d1"

    def test_all_identical_vectors(self):
        idx = SemanticIndex(dim=2)
        for i in range(5):
            idx.add(f"d{i}", vector=[1.0, 0.0])
        results = idx.search(vector=[1.0, 0.0], top_k=5)
        assert len(results) == 5
        assert all(r.score == pytest.approx(1.0, abs=1e-5) for r in results)


# ---------------------------------------------------------------------------
# Cosine Similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical(self):
        assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite(self):
        assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector(self):
        assert cosine_similarity([0, 0], [1, 0]) == 0.0

    def test_known_angle(self):
        s = cosine_similarity([1, 1], [1, 0])
        assert s == pytest.approx(math.sqrt(2) / 2, abs=1e-6)


# ---------------------------------------------------------------------------
# RRF
# ---------------------------------------------------------------------------


class TestRRF:
    def test_basic_two_lists(self):
        r1 = [Result("a", 0.9), Result("b", 0.8)]
        r2 = [Result("b", 0.95), Result("c", 0.85)]
        fused = rrf(r1, r2)
        doc_ids = [r.doc_id for r in fused]
        assert "b" in doc_ids
        assert "a" in doc_ids
        assert "c" in doc_ids

    def test_single_list(self):
        r1 = [Result("a", 0.9), Result("b", 0.8)]
        fused = rrf(r1)
        assert len(fused) == 2

    def test_weights(self):
        r1 = [Result("a", 0.9)]
        r2 = [Result("b", 0.9)]
        fused = rrf(r1, r2, weights=[10.0, 1.0])
        assert fused[0].doc_id == "a"

    def test_top_k(self):
        r1 = [Result("a", 0.9), Result("b", 0.8), Result("c", 0.7)]
        fused = rrf(r1, top_k=2)
        assert len(fused) == 2

    def test_no_lists_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            rrf()

    def test_k_zero_raises(self):
        with pytest.raises(ValueError, match="k must be positive"):
            rrf([Result("a", 0.9)], k=0)

    def test_weights_mismatch_raises(self):
        with pytest.raises(ValueError, match="weights length"):
            rrf([Result("a", 0.9)], [Result("b", 0.8)], weights=[1.0])

    def test_metadata_from_best_score(self):
        r1 = [Result("a", 0.5, metadata={"src": "sparse"})]
        r2 = [Result("a", 0.9, metadata={"src": "dense"})]
        fused = rrf(r1, r2)
        assert fused[0].metadata == {"src": "dense"}


# ---------------------------------------------------------------------------
# MMR
# ---------------------------------------------------------------------------


class TestMMR:
    def test_basic(self):
        results = [Result("a", 1.0), Result("b", 0.9), Result("c", 0.8)]
        reranked = mmr(results, lambda a, b: 0.5, top_k=2)
        assert len(reranked) == 2

    def test_lambda_one_preserves_order(self):
        results = [Result("a", 1.0), Result("b", 0.5), Result("c", 0.1)]
        reranked = mmr(results, lambda a, b: 1.0, lambda_=1.0)
        assert [r.doc_id for r in reranked] == ["a", "b", "c"]

    def test_empty(self):
        assert mmr([], lambda a, b: 0.0) == []

    def test_invalid_lambda(self):
        with pytest.raises(ValueError, match="lambda_"):
            mmr([Result("a", 1.0)], lambda a, b: 0.0, lambda_=1.5)

    def test_metadata_preserved(self):
        results = [Result("a", 1.0, metadata={"k": "v"})]
        reranked = mmr(results, lambda a, b: 0.0)
        assert reranked[0].metadata == {"k": "v"}
