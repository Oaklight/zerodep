# /// zerodep
# version = "0.2.2"
# deps = []
# tier = "medium"
# category = "utility"
# ///
"""Zero-dependency sparse text search with BM25 family and TF-IDF ranking.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Full-text search engine with inverted index, supporting BM25/BM25+/BM25L/BM25F
and TF-IDF+Cosine similarity ranking. Designed for use in LLM/Agent/RAG pipelines.

Basic usage::

    index = SparseIndex()
    index.add("doc1", "the quick brown fox")
    index.add("doc2", "the lazy dog")
    results = index.search("quick fox")

Multi-field (BM25F) usage::

    index = SparseIndex(field_weights={"title": 2.0, "body": 1.0})
    index.add("doc1", {"title": "Python Guide", "body": "Learn Python basics"})
    results = index.search("python")

Custom tokenizer::

    import jieba
    index = SparseIndex(tokenize=jieba.lcut)

Persistence::

    index.save("index.json")
    index = SparseIndex.load("index.json")
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "Result",
    "SparseIndex",
]

_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Default tokenizer
# ---------------------------------------------------------------------------

_SPLIT_RE = re.compile(r"[\w]+", re.UNICODE)


def _default_tokenize(text: str) -> list[str]:
    """Simple whitespace/punctuation tokenizer with lowercasing.

    Splits on non-word characters and lowercases all tokens.
    For better results (stemming, stop-word removal, CJK segmentation),
    pass a custom tokenizer to SparseIndex.
    """
    return [tok.lower() for tok in _SPLIT_RE.findall(text)]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class Result:
    """A single search result."""

    doc_id: str
    score: float
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Internal document record
# ---------------------------------------------------------------------------


@dataclass
class _DocRecord:
    """Internal storage for a single document."""

    doc_id: str
    field_lengths: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# SparseIndex
# ---------------------------------------------------------------------------


class SparseIndex:
    """Sparse text search index with BM25 family and TF-IDF ranking.

    Args:
        variant: Ranking algorithm. One of "bm25", "bm25l", "tfidf".
        k1: BM25 term-frequency saturation parameter (ignored for tfidf).
        b: BM25 document-length normalization parameter (ignored for tfidf).
        delta: BM25+ lower-bound correction. Set to 0 for classic BM25.
        field_weights: Per-field boost weights for BM25F multi-field search.
            When ``None``, documents are treated as single-field text.
        tokenize: Tokenization function ``str -> list[str]``.
            Defaults to a simple Unicode word splitter with lowercasing.
    """

    _SQLITE_MAGIC = b"SQLite format 3\x00"

    def __init__(
        self,
        variant: str = "bm25",
        k1: float = 1.5,
        b: float = 0.75,
        delta: float = 1.0,
        field_weights: dict[str, float] | None = None,
        tokenize: Callable[[str], list[str]] | None = None,
    ) -> None:
        if variant not in ("bm25", "bm25l", "tfidf"):
            raise ValueError(
                f"Unknown variant {variant!r}, expected 'bm25', 'bm25l', or 'tfidf'"
            )

        self.variant = variant
        self.k1 = k1
        self.b = b
        self.delta = delta
        self.field_weights = field_weights
        self._tokenize = tokenize or _default_tokenize

        # Document storage: doc_id -> _DocRecord
        self._docs: dict[str, _DocRecord] = {}

        # Inverted index: term -> {doc_id -> {field -> term_freq}}
        self._index: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

        # Document frequency: term -> number of documents containing it
        self._df: dict[str, int] = defaultdict(int)

        # Total field lengths for average calculation
        self._total_field_lengths: dict[str, float] = defaultdict(float)

        # Reverse index: doc_id -> set of terms (for fast delete)
        self._doc_terms: dict[str, set[str]] = defaultdict(set)

    # -- properties ----------------------------------------------------------

    def __len__(self) -> int:
        return len(self._docs)

    def __contains__(self, doc_id: str) -> bool:
        return doc_id in self._docs

    @property
    def doc_count(self) -> int:
        """Number of documents in the index."""
        return len(self._docs)

    @property
    def vocab_size(self) -> int:
        """Number of unique terms in the index."""
        return len(self._index)

    # -- document management -------------------------------------------------

    def add(
        self,
        doc_id: str,
        content: str | dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a document to the index.

        Args:
            doc_id: Unique document identifier.
            content: Document text (single-field) or ``{field: text}`` dict
                (multi-field for BM25F).
            metadata: Arbitrary JSON-serializable metadata attached to the doc.

        Raises:
            ValueError: If ``doc_id`` already exists (use ``update`` instead).
        """
        if doc_id in self._docs:
            raise ValueError(
                f"Document {doc_id!r} already exists, use update() instead"
            )
        self._insert(doc_id, content, metadata)

    def remove(self, doc_id: str) -> None:
        """Remove a document from the index.

        Args:
            doc_id: Document identifier to remove.

        Raises:
            KeyError: If ``doc_id`` does not exist.
        """
        if doc_id not in self._docs:
            raise KeyError(f"Document {doc_id!r} not found")
        self._delete(doc_id)

    def update(
        self,
        doc_id: str,
        content: str | dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update (replace) a document in the index.

        Args:
            doc_id: Document identifier to update.
            content: New document text or ``{field: text}`` dict.
            metadata: New metadata (replaces old metadata entirely).

        Raises:
            KeyError: If ``doc_id`` does not exist (use ``add`` instead).
        """
        if doc_id not in self._docs:
            raise KeyError(f"Document {doc_id!r} not found, use add() instead")
        self._delete(doc_id)
        self._insert(doc_id, content, metadata)

    # -- search --------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[Result]:
        """Search for documents matching the query.

        Args:
            query: Search query string.
            top_k: Maximum number of results to return.
            filters: Metadata filters. Each key-value pair must match exactly
                in the document's metadata. Use a callable value for custom
                filter logic (e.g. ``{"year": lambda y: y > 2023}``).

        Returns:
            List of :class:`Result` objects sorted by descending score.
        """
        if not self._docs:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        if self.variant == "tfidf":
            scores = self._score_tfidf(query_tokens)
        else:
            scores = self._score_bm25(query_tokens)

        # Apply metadata filters
        if filters:
            scores = {
                doc_id: score
                for doc_id, score in scores.items()
                if self._match_filters(doc_id, filters)
            }

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        return [
            Result(
                doc_id=doc_id,
                score=score,
                metadata=self._docs[doc_id].metadata,
            )
            for doc_id, score in ranked
            if score > 0
        ]

    # -- persistence ---------------------------------------------------------

    def save(self, path: str, format: str | None = None) -> None:
        """Save the index to disk.

        Args:
            path: File path to save to.
            format: ``"json"`` or ``"sqlite"``. If ``None``, inferred from
                file extension (``.db`` -> sqlite, otherwise json).
        """
        fmt = self._resolve_format(path, format)
        if fmt == "json":
            self._save_json(path)
        else:
            self._save_sqlite(path)

    @classmethod
    def load(cls, path: str) -> SparseIndex:
        """Load an index from disk.

        Auto-detects format by inspecting the file header.

        Args:
            path: File path to load from.

        Returns:
            A new :class:`SparseIndex` instance with restored state.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        with open(p, "rb") as f:
            header = f.read(16)

        if header.startswith(cls._SQLITE_MAGIC):
            return cls._load_sqlite(path)
        return cls._load_json(path)

    # -- internal: insert / delete -------------------------------------------

    def _normalize_content(self, content: str | dict[str, str]) -> dict[str, str]:
        """Convert content to {field: text} dict."""
        if isinstance(content, str):
            return {"_default": content}
        return dict(content)

    def _insert(
        self,
        doc_id: str,
        content: str | dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        fields = self._normalize_content(content)
        field_lengths: dict[str, int] = {}
        seen_terms: set[str] = set()

        for field_name, text in fields.items():
            tokens = self._tokenize(text)
            field_lengths[field_name] = len(tokens)
            self._total_field_lengths[field_name] += len(tokens)

            for token in tokens:
                self._index[token][doc_id][field_name] += 1
                seen_terms.add(token)

        for term in seen_terms:
            self._df[term] += 1

        self._doc_terms[doc_id] = seen_terms

        self._docs[doc_id] = _DocRecord(
            doc_id=doc_id,
            field_lengths=field_lengths,
            metadata=metadata,
        )

    def _delete(self, doc_id: str) -> None:
        doc = self._docs[doc_id]

        # Update total field lengths
        for field_name, length in doc.field_lengths.items():
            self._total_field_lengths[field_name] -= length

        # Remove from inverted index using reverse index (O(terms_in_doc)
        # instead of O(vocab_size))
        empty_terms: list[str] = []
        for term in self._doc_terms[doc_id]:
            postings = self._index.get(term)
            if postings is not None and doc_id in postings:
                del postings[doc_id]
                self._df[term] -= 1
                if self._df[term] <= 0:
                    empty_terms.append(term)

        # Clean up empty terms
        for term in empty_terms:
            del self._index[term]
            del self._df[term]

        del self._doc_terms[doc_id]
        del self._docs[doc_id]

    # -- internal: BM25 scoring ----------------------------------------------

    def _avg_field_length(self, field_name: str) -> float:
        n = len(self._docs)
        if n == 0:
            return 0.0
        return self._total_field_lengths[field_name] / n

    def _idf(self, term: str) -> float:
        """Compute IDF for a term using the standard BM25 IDF formula."""
        n = len(self._docs)
        df = self._df.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((n - df + 0.5) / (df + 0.5) + 1.0)

    def _score_bm25(self, query_tokens: list[str]) -> dict[str, float]:
        """Score documents using BM25 / BM25+ / BM25L / BM25F."""
        scores: dict[str, float] = defaultdict(float)
        k1 = self.k1
        b = self.b
        delta = self.delta
        field_weights = self.field_weights or {"_default": 1.0}
        is_bm25l = self.variant == "bm25l"

        for token in query_tokens:
            if token not in self._index:
                continue

            idf = self._idf(token)
            postings = self._index[token]

            for doc_id, field_tfs in postings.items():
                # BM25F: weighted pseudo term frequency and document length
                weighted_tf = 0.0
                weighted_dl = 0.0

                doc = self._docs[doc_id]
                for field_name, tf in field_tfs.items():
                    w = field_weights.get(field_name, 1.0)
                    weighted_tf += w * tf
                    weighted_dl += w * doc.field_lengths.get(field_name, 0)

                # Weighted average document length
                weighted_avgdl = 0.0
                for field_name, w in field_weights.items():
                    weighted_avgdl += w * self._avg_field_length(field_name)

                if weighted_avgdl == 0:
                    weighted_avgdl = 1.0

                if is_bm25l:
                    # BM25L: adjusted TF normalization
                    ctf = weighted_tf / (1.0 - b + b * weighted_dl / weighted_avgdl)
                    tf_norm = ((k1 + 1.0) * (ctf + delta)) / (k1 + ctf + delta)
                else:
                    # BM25 / BM25+
                    tf_norm = (weighted_tf * (k1 + 1.0)) / (
                        weighted_tf + k1 * (1.0 - b + b * weighted_dl / weighted_avgdl)
                    )
                    tf_norm += delta

                scores[doc_id] += idf * tf_norm

        return dict(scores)

    # -- internal: TF-IDF scoring --------------------------------------------

    def _score_tfidf(self, query_tokens: list[str]) -> dict[str, float]:
        """Score documents using TF-IDF with cosine similarity."""
        n = len(self._docs)
        if n == 0:
            return {}

        field_weights = self.field_weights or {"_default": 1.0}

        # Build query TF-IDF vector (term -> weight)
        query_tf: dict[str, int] = defaultdict(int)
        for token in query_tokens:
            query_tf[token] += 1

        query_vec: dict[str, float] = {}
        for term, tf in query_tf.items():
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(n / df) + 1.0  # smoothed IDF
            query_vec[term] = (1.0 + math.log(tf)) * idf

        if not query_vec:
            return {}

        query_norm = math.sqrt(sum(v * v for v in query_vec.values()))

        # Score each candidate document
        scores: dict[str, float] = {}
        candidates: set[str] = set()
        for term in query_vec:
            if term in self._index:
                candidates.update(self._index[term].keys())

        for doc_id in candidates:
            dot_product = 0.0
            doc_norm_sq = 0.0

            # Collect all terms in this document for norm calculation
            doc_terms: dict[str, float] = {}
            for term in self._index:
                if doc_id not in self._index[term]:
                    continue

                field_tfs = self._index[term][doc_id]
                weighted_tf = sum(
                    field_weights.get(fn, 1.0) * tf for fn, tf in field_tfs.items()
                )
                if weighted_tf <= 0:
                    continue

                df = self._df.get(term, 1)
                idf = math.log(n / df) + 1.0
                tfidf = (1.0 + math.log(weighted_tf)) * idf
                doc_terms[term] = tfidf

            for term, tfidf in doc_terms.items():
                doc_norm_sq += tfidf * tfidf
                if term in query_vec:
                    dot_product += tfidf * query_vec[term]

            if doc_norm_sq > 0 and dot_product > 0:
                scores[doc_id] = dot_product / (query_norm * math.sqrt(doc_norm_sq))

        return scores

    # -- internal: metadata filtering ----------------------------------------

    def _match_filters(self, doc_id: str, filters: dict[str, Any]) -> bool:
        """Check if a document's metadata matches all filters."""
        doc = self._docs[doc_id]
        if doc.metadata is None:
            return False

        for key, expected in filters.items():
            actual = doc.metadata.get(key)
            if callable(expected):
                if not expected(actual):
                    return False
            elif actual != expected:
                return False

        return True

    # -- internal: persistence (JSON) ----------------------------------------

    def _to_dict(self) -> dict[str, Any]:
        """Serialize index state to a JSON-compatible dict."""
        # Convert inverted index: nested defaultdicts -> plain dicts
        index_data: dict[str, dict[str, dict[str, int]]] = {}
        for term, postings in self._index.items():
            index_data[term] = {}
            for doc_id, field_tfs in postings.items():
                index_data[term][doc_id] = dict(field_tfs)

        docs_data: dict[str, dict[str, Any]] = {}
        for doc_id, doc in self._docs.items():
            docs_data[doc_id] = asdict(doc)

        doc_terms_data: dict[str, list[str]] = {
            doc_id: sorted(terms) for doc_id, terms in self._doc_terms.items()
        }

        return {
            "version": _VERSION,
            "config": {
                "variant": self.variant,
                "k1": self.k1,
                "b": self.b,
                "delta": self.delta,
                "field_weights": self.field_weights,
            },
            "docs": docs_data,
            "index": index_data,
            "df": dict(self._df),
            "total_field_lengths": dict(self._total_field_lengths),
            "doc_terms": doc_terms_data,
        }

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> SparseIndex:
        """Restore index state from a deserialized dict."""
        config = data["config"]
        instance = cls(
            variant=config["variant"],
            k1=config["k1"],
            b=config["b"],
            delta=config["delta"],
            field_weights=config.get("field_weights"),
        )

        # Restore docs
        for doc_id, doc_data in data["docs"].items():
            instance._docs[doc_id] = _DocRecord(
                doc_id=doc_data["doc_id"],
                field_lengths=doc_data["field_lengths"],
                metadata=doc_data.get("metadata"),
            )

        # Restore inverted index as nested defaultdicts
        for term, postings in data["index"].items():
            for doc_id, field_tfs in postings.items():
                for field_name, tf in field_tfs.items():
                    instance._index[term][doc_id][field_name] = tf

        # Restore df
        for term, count in data["df"].items():
            instance._df[term] = count

        # Restore total field lengths
        for field_name, total in data["total_field_lengths"].items():
            instance._total_field_lengths[field_name] = total

        # Restore reverse index
        if "doc_terms" in data:
            for doc_id, terms in data["doc_terms"].items():
                instance._doc_terms[doc_id] = set(terms)
        else:
            # Rebuild from inverted index if loading old format
            for term, postings in instance._index.items():
                for doc_id in postings:
                    instance._doc_terms[doc_id].add(term)

        return instance

    def _save_json(self, path: str) -> None:
        data = self._to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def _load_json(cls, path: str) -> SparseIndex:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls._from_dict(data)

    # -- internal: persistence (SQLite) --------------------------------------

    def _save_sqlite(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()

        conn = sqlite3.connect(path)
        try:
            cur = conn.cursor()
            cur.executescript("""
                CREATE TABLE config (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE docs (
                    doc_id        TEXT PRIMARY KEY,
                    field_lengths TEXT NOT NULL,
                    metadata      TEXT
                );
                CREATE TABLE inverted_index (
                    term     TEXT NOT NULL,
                    doc_id   TEXT NOT NULL,
                    field_tfs TEXT NOT NULL,
                    PRIMARY KEY (term, doc_id)
                );
                CREATE TABLE df (
                    term  TEXT PRIMARY KEY,
                    count INTEGER NOT NULL
                );
                CREATE TABLE field_lengths_total (
                    field_name TEXT PRIMARY KEY,
                    total      REAL NOT NULL
                );
            """)

            # Config
            config = {
                "version": _VERSION,
                "variant": self.variant,
                "k1": self.k1,
                "b": self.b,
                "delta": self.delta,
                "field_weights": self.field_weights,
            }
            for key, value in config.items():
                cur.execute(
                    "INSERT INTO config (key, value) VALUES (?, ?)",
                    (key, json.dumps(value)),
                )

            # Docs
            for doc_id, doc in self._docs.items():
                cur.execute(
                    "INSERT INTO docs (doc_id, field_lengths, metadata)"
                    " VALUES (?, ?, ?)",
                    (
                        doc_id,
                        json.dumps(doc.field_lengths),
                        json.dumps(doc.metadata) if doc.metadata is not None else None,
                    ),
                )

            # Inverted index
            for term, postings in self._index.items():
                for doc_id, field_tfs in postings.items():
                    cur.execute(
                        "INSERT INTO inverted_index"
                        " (term, doc_id, field_tfs)"
                        " VALUES (?, ?, ?)",
                        (term, doc_id, json.dumps(dict(field_tfs))),
                    )

            # DF
            for term, count in self._df.items():
                cur.execute(
                    "INSERT INTO df (term, count) VALUES (?, ?)",
                    (term, count),
                )

            # Total field lengths
            for field_name, total in self._total_field_lengths.items():
                cur.execute(
                    "INSERT INTO field_lengths_total (field_name, total) VALUES (?, ?)",
                    (field_name, total),
                )

            conn.commit()
        finally:
            conn.close()

    @classmethod
    def _load_sqlite(cls, path: str) -> SparseIndex:
        conn = sqlite3.connect(path)
        try:
            cur = conn.cursor()

            # Load config
            config: dict[str, Any] = {}
            for key, value in cur.execute("SELECT key, value FROM config"):
                config[key] = json.loads(value)

            instance = cls(
                variant=config["variant"],
                k1=config["k1"],
                b=config["b"],
                delta=config["delta"],
                field_weights=config.get("field_weights"),
            )

            # Load docs
            for doc_id, field_lengths_json, metadata_json in cur.execute(
                "SELECT doc_id, field_lengths, metadata FROM docs"
            ):
                instance._docs[doc_id] = _DocRecord(
                    doc_id=doc_id,
                    field_lengths=json.loads(field_lengths_json),
                    metadata=json.loads(metadata_json)
                    if metadata_json is not None
                    else None,
                )

            # Load inverted index and rebuild reverse index
            for term, doc_id, field_tfs_json in cur.execute(
                "SELECT term, doc_id, field_tfs FROM inverted_index"
            ):
                field_tfs = json.loads(field_tfs_json)
                for field_name, tf in field_tfs.items():
                    instance._index[term][doc_id][field_name] = tf
                instance._doc_terms[doc_id].add(term)

            # Load df
            for term, count in cur.execute("SELECT term, count FROM df"):
                instance._df[term] = count

            # Load total field lengths
            for field_name, total in cur.execute(
                "SELECT field_name, total FROM field_lengths_total"
            ):
                instance._total_field_lengths[field_name] = total

            return instance
        finally:
            conn.close()

    # -- internal: format resolution -----------------------------------------

    @staticmethod
    def _resolve_format(path: str, format: str | None) -> str:
        """Determine save format from explicit arg or file extension."""
        if format is not None:
            if format not in ("json", "sqlite"):
                raise ValueError(
                    f"Unknown format {format!r}, expected 'json' or 'sqlite'"
                )
            return format
        if Path(path).suffix in (".db", ".sqlite", ".sqlite3"):
            return "sqlite"
        return "json"
