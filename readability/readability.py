# /// zerodep
# version = "0.2.0"
# deps = ["soup"]
# tier = "medium"
# category = "text"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""HTML readability content extractor — zero-dep, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Extracts the main article content from arbitrary web pages using a scoring
algorithm inspired by Mozilla's Readability.js (Firefox Reader View).  Built
on top of ``zerodep/soup`` for HTML parsing; no external dependencies.

Algorithm overview:

1. Pre-clean the DOM (remove scripts, styles, etc.)
2. Extract metadata (JSON-LD, ``<meta>`` tags, ``<title>``)
3. Remove unlikely candidate nodes (sidebars, footers, ads …)
4. Transform mis-used ``<div>`` elements into ``<p>`` paragraphs
5. Score every ``<p>``/``<pre>``/``<td>`` node based on comma count,
   text length and class/id weight; propagate scores to parent &
   grandparent
6. Pick the highest-scoring container and include qualifying siblings
7. Sanitize the extracted article (remove forms, low-quality headers …)
8. If the result is too short, retry with relaxed heuristics

Example::

    from readability import extract, is_probably_readable

    html = open("article.html").read()
    if is_probably_readable(html):
        result = extract(html)
        print(result.title)
        print(result.text[:200])

References:
    - Mozilla Readability.js: https://github.com/mozilla/readability
    - python-readability: https://github.com/buriy/python-readability
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import sys
from dataclasses import dataclass
from html import unescape
from typing import Any

__all__ = [
    "ReadabilityResult",
    "extract",
    "is_probably_readable",
]

log = logging.getLogger(__name__)

# ── Lazy soup import ─────────────────────────────────────────────────────────


def _ensure_sibling_path(name: str) -> str:
    """Add a sibling module directory to ``sys.path`` if not present."""
    sibling_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", name))
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


def _load_soup():
    _ensure_sibling_path("soup")
    try:
        from soup import Soup, Tag  # type: ignore[import-untyped]
    except ImportError as exc:
        raise NotImplementedError(
            "readability requires the 'soup' zerodep module — "
            "place soup/soup.py alongside readability/"
        ) from exc
    return Soup, Tag


# ── Constants & regex patterns ───────────────────────────────────────────────

MIN_PARAGRAPH_LENGTH = 25
RETRY_LENGTH = 250
DEFAULT_CHAR_THRESHOLD = 500

UNLIKELY_CANDIDATES_RE = re.compile(
    r"combx|comment|community|disqus|extra|foot|header|menu|remark|rss|"
    r"shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|"
    r"tweet|twitter|widget|breadcrumb|social|share|related|banner|"
    r"cookie|consent|modal|overlay|nav\b",
    re.I,
)

OK_MAYBE_CANDIDATE_RE = re.compile(
    r"and|article|body|column|main|shadow|content",
    re.I,
)

POSITIVE_RE = re.compile(
    r"article|body|content|entry|hentry|h-entry|main|page|pagination|"
    r"post|text|blog|story",
    re.I,
)

NEGATIVE_RE = re.compile(
    r"-ad-|hidden|^hid$| hid$| hid |^hid |banner|combx|comment|com-|"
    r"contact|footer|gdpr|masthead|media|meta|outbrain|promo|related|"
    r"scroll|share|shoutbox|sidebar|skyscraper|sponsor|shopping|tags|"
    r"tool|widget",
    re.I,
)

BLOCK_LEVEL_TAGS = frozenset(
    {
        "a",
        "blockquote",
        "dl",
        "div",
        "img",
        "ol",
        "p",
        "pre",
        "table",
        "ul",
        "section",
        "figure",
        "header",
        "footer",
        "nav",
        "aside",
        "details",
        "fieldset",
        "form",
        "hr",
        "noscript",
        "video",
        "audio",
    }
)

TAGS_TO_SCORE = frozenset({"p", "pre", "td"})

TAG_WEIGHTS: dict[str, int] = {
    "div": 5,
    "article": 5,
    "pre": 3,
    "td": 3,
    "blockquote": 3,
    "address": -3,
    "ol": -3,
    "ul": -3,
    "dl": -3,
    "dd": -3,
    "dt": -3,
    "li": -3,
    "form": -3,
    "aside": -3,
    "h1": -5,
    "h2": -5,
    "h3": -5,
    "h4": -5,
    "h5": -5,
    "h6": -5,
    "th": -5,
    "header": -5,
    "footer": -5,
    "nav": -5,
}

CLEAN_CONDITIONALLY_TAGS = frozenset(
    {"table", "ul", "div", "aside", "header", "footer", "section"}
)

REMOVE_TAGS = frozenset({"form", "textarea", "input", "button", "select"})

TITLE_SEPARATORS_RE = re.compile(r"\s+[\|\-–—\\/>»]\s+")

# JSON-LD Article types (Schema.org)
JSONLD_ARTICLE_TYPES = frozenset(
    {
        "Article",
        "AdvertiserContentArticle",
        "NewsArticle",
        "AnalysisNewsArticle",
        "AskPublicNewsArticle",
        "BackgroundNewsArticle",
        "OpinionNewsArticle",
        "ReportageNewsArticle",
        "ReviewNewsArticle",
        "Report",
        "SatiricalArticle",
        "ScholarlyArticle",
        "MedicalScholarlyArticle",
        "SocialMediaPosting",
        "BlogPosting",
        "LiveBlogPosting",
        "DiscussionForumPosting",
        "TechArticle",
        "APIReference",
    }
)

# Multi-language commas for scoring
COMMAS_RE = re.compile(r"[\u002C\u060C\uFE50\uFE10\uFE11\u2E41\u2E34\u2E32\uFF0C]")


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReadabilityResult:
    """Container for extracted article data.

    Attributes:
        title: Article title (refined from ``<title>`` or headings).
        content: Cleaned HTML of the main content.
        text: Plain-text rendering of the main content.
        author: Author name, or ``None``.
        excerpt: Article excerpt / description, or ``None``.
        site_name: Site name (e.g. from ``og:site_name``), or ``None``.
        published_time: Publication timestamp string, or ``None``.
        lang: Language code from ``<html lang="...">``, or ``None``.
        dir: Text direction (``"ltr"`` / ``"rtl"``), or ``None``.
        length: Character count of *text*.
        score: Readability score of the best candidate container.  Higher
            values indicate stronger confidence that the extracted content
            is a real article rather than navigation / boilerplate.  Zero
            when no scored candidate was found (body fallback).
    """

    title: str
    content: str
    text: str
    author: str | None = None
    excerpt: str | None = None
    site_name: str | None = None
    published_time: str | None = None
    lang: str | None = None
    dir: str | None = None
    length: int = 0
    score: float = 0.0


# ── Public API ───────────────────────────────────────────────────────────────


def extract(html: str, url: str | None = None) -> ReadabilityResult:
    """Extract the main article content from an HTML string.

    Args:
        html: The full HTML document as a decoded string.
        url: Optional base URL (currently unused; reserved for future
            link absolutisation).

    Returns:
        A ``ReadabilityResult`` with the extracted content and metadata.
    """
    Soup, _Tag = _load_soup()
    reader = _Readability(html, Soup, _Tag)
    return reader.parse()


def is_probably_readable(
    html: str,
    min_score: float = 20.0,
    min_content_length: int = 140,
) -> bool:
    """Quick heuristic check whether *html* likely contains a readable article.

    Uses the same approach as Mozilla's ``isProbablyReaderable``: accumulate
    ``sqrt(textLen - threshold)`` over qualifying ``<p>``/``<pre>``/``<article>``
    nodes and return ``True`` once the score exceeds *min_score*.

    Args:
        html: The HTML document string.
        min_score: Minimum cumulative score to consider readable.
        min_content_length: Minimum text length for a node to contribute.

    Returns:
        ``True`` if the page is probably an article.
    """
    Soup, _Tag = _load_soup()
    soup = Soup(html)

    score = 0.0
    for tag in soup.find_all(["p", "pre", "article"]):
        # Skip unlikely candidates
        class_id = _get_class_id_string(tag)
        if len(class_id) > 1:
            is_unlikely = UNLIKELY_CANDIDATES_RE.search(class_id)
            is_ok = OK_MAYBE_CANDIDATE_RE.search(class_id)
            if is_unlikely and not is_ok:
                continue

        text = tag.get_text(strip=True)
        text_len = len(text)
        if text_len < min_content_length:
            continue

        score += math.sqrt(text_len - min_content_length)
        if score >= min_score:
            return True

    return False


# ── Internal helpers ─────────────────────────────────────────────────────────


def _get_class_id_string(tag: Any) -> str:
    """Return concatenated class and id for regex matching."""
    cls = tag.get("class", [])
    if isinstance(cls, list):
        cls = " ".join(cls)
    tag_id = tag.get("id", "")
    return f"{cls} {tag_id}"


def _normalize_spaces(s: str) -> str:
    """Collapse all whitespace to single spaces and strip."""
    return " ".join(s.split())


def _text_length(tag: Any) -> int:
    """Return the length of the whitespace-normalised text content."""
    return len(_normalize_spaces(tag.get_text()))


# ── Readability engine ───────────────────────────────────────────────────────


class _Readability:
    """Internal engine that implements the readability extraction algorithm."""

    # Tags to discard during article-extraction parsing.  These are never
    # part of the readable content and skipping them speeds up both tree
    # construction and subsequent traversals.
    _SKIP_TAGS = frozenset({"script", "style", "link", "noscript"})

    def __init__(self, html: str, Soup: type, Tag: type) -> None:
        self._raw_html = html
        self._Soup = Soup
        self._Tag = Tag
        self._soup: Any = None

    # ── Main entry point ─────────────────────────────────────────────────

    def parse(self) -> ReadabilityResult:
        """Run the full extraction pipeline and return a result."""
        # Parse once: extract metadata from the fresh DOM before mutations.
        self._soup = self._Soup(self._raw_html)
        metadata = self._extract_metadata(self._soup)
        lang = self._detect_lang(self._soup)
        direction = self._detect_dir(self._soup)

        # Grab article content.  The first iteration reuses self._soup
        # (removing non-content tags in-place); retries use a faster
        # parse that skips those tags during tree construction.
        article_html, article_text, article_score = self._grab_article()

        # If metadata title is empty, try to derive from article headings.
        title = metadata.get("title", "")
        if not title:
            title = self._get_title_from_headings(self._soup) or ""

        text = _normalize_spaces(article_text)
        return ReadabilityResult(
            title=title,
            content=article_html,
            text=text,
            author=metadata.get("author"),
            excerpt=metadata.get("excerpt"),
            site_name=metadata.get("site_name"),
            published_time=metadata.get("published_time"),
            lang=lang,
            dir=direction,
            length=len(text),
            score=article_score,
        )

    # ── Article grabbing (with retry) ────────────────────────────────────

    _PRE_CLEAN_TAGS = ["script", "style", "link", "noscript"]

    def _grab_article(self) -> tuple[str, str, float]:
        """Extract article content, retrying with relaxed rules if needed.

        Returns:
            ``(article_html, article_text, score)`` tuple.  *score* is the
            readability score of the best candidate (0.0 for body fallback).
        """
        ruthless = True

        for _attempt in range(2):
            if _attempt == 0:
                # First attempt: reuse the DOM already parsed by parse()
                # and strip non-content tags in-place.
                self._pre_clean()
            else:
                # Retry: fast re-parse that skips non-content tags at the
                # parser level (avoids building + decomposing subtrees).
                self._soup = self._Soup(self._raw_html, skip_tags=self._SKIP_TAGS)

            if ruthless:
                self._remove_unlikely_candidates()

            self._transform_divs_to_paragraphs()
            candidates = self._score_paragraphs()

            best = self._select_best_candidate(candidates)
            if best is not None:
                article_tag = self._get_article(best, candidates)
                self._sanitize(article_tag)
                article_html = article_tag.to_html()
                article_text = article_tag.get_text(separator=" ", strip=True)

                if len(article_text) >= RETRY_LENGTH or not ruthless:
                    return article_html, article_text, best["score"]

                # Too short — retry without ruthless filtering.
                log.debug(
                    "Article too short (%d chars), retrying without "
                    "ruthless candidate removal",
                    len(article_text),
                )
                ruthless = False
                continue
            else:
                if ruthless:
                    log.debug("No candidate found, retrying without ruthless")
                    ruthless = False
                    continue
                # Fall back to body content.
                break

        # Final fallback: return body content as-is.
        body = self._soup.find("body")
        if body is not None:
            return body.to_html(), body.get_text(separator=" ", strip=True), 0.0
        return "", "", 0.0

    # ── Pre-cleaning ─────────────────────────────────────────────────────

    def _pre_clean(self) -> None:
        """Remove script, style, link and other non-content tags."""
        for tag in list(self._soup.find_all(self._PRE_CLEAN_TAGS)):
            tag.decompose()

    # ── Metadata extraction ──────────────────────────────────────────────

    def _extract_metadata(self, soup: Any) -> dict[str, str | None]:
        """Extract article metadata from JSON-LD and ``<meta>`` tags.

        Args:
            soup: A parsed ``Soup`` instance (unmutated).

        Returns:
            Dict with keys: title, author, excerpt, site_name, published_time.
        """
        meta: dict[str, str | None] = {
            "title": None,
            "author": None,
            "excerpt": None,
            "site_name": None,
            "published_time": None,
        }

        # 1. Try JSON-LD first (highest priority).
        self._parse_jsonld(soup, meta)

        # 2. Parse <meta> tags.
        self._parse_meta_tags(soup, meta)

        # 3. Title from <title> element (if not yet found).
        if not meta["title"]:
            title_tag = soup.find("title")
            if title_tag:
                meta["title"] = _normalize_spaces(title_tag.get_text())

        # 4. Refine title by removing site name suffixes.
        if meta["title"]:
            meta["title"] = self._shorten_title(meta["title"])

        return meta

    def _parse_jsonld(self, soup: Any, meta: dict[str, str | None]) -> None:
        """Extract metadata from ``<script type="application/ld+json">``."""
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            text = script.get_text()
            if not text:
                continue
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                continue

            # Handle @graph arrays.
            if isinstance(data, dict) and "@graph" in data:
                graph = data["@graph"]
                if isinstance(graph, list):
                    for item in graph:
                        if self._is_article_jsonld(item):
                            data = item
                            break
                    else:
                        continue

            if not self._is_article_jsonld(data):
                continue

            if not meta["title"]:
                meta["title"] = _str_or_none(data.get("headline")) or _str_or_none(
                    data.get("name")
                )
            if not meta["author"]:
                meta["author"] = self._extract_jsonld_author(data)
            if not meta["excerpt"]:
                meta["excerpt"] = _str_or_none(data.get("description"))
            if not meta["published_time"]:
                meta["published_time"] = _str_or_none(data.get("datePublished"))
            if not meta["site_name"]:
                publisher = data.get("publisher")
                if isinstance(publisher, dict):
                    meta["site_name"] = _str_or_none(publisher.get("name"))

    @staticmethod
    def _is_article_jsonld(data: Any) -> bool:
        """Check if *data* is a Schema.org Article (or subtype)."""
        if not isinstance(data, dict):
            return False
        schema_type = data.get("@type", "")
        if isinstance(schema_type, list):
            return any(t in JSONLD_ARTICLE_TYPES for t in schema_type)
        return schema_type in JSONLD_ARTICLE_TYPES

    @staticmethod
    def _extract_jsonld_author(data: dict) -> str | None:
        """Extract author name from JSON-LD, handling various formats."""
        author = data.get("author")
        if author is None:
            return None
        if isinstance(author, str):
            return author
        if isinstance(author, dict):
            return _str_or_none(author.get("name"))
        if isinstance(author, list):
            names = []
            for a in author:
                if isinstance(a, str):
                    names.append(a)
                elif isinstance(a, dict) and "name" in a:
                    names.append(a["name"])
            return ", ".join(names) if names else None
        return None

    def _parse_meta_tags(self, soup: Any, meta: dict[str, str | None]) -> None:
        """Extract metadata from ``<meta>`` tags (OpenGraph, DC, etc.)."""
        # Mapping of meta property/name → target field + priority (lower wins).
        property_map: dict[str, str] = {
            "og:title": "title",
            "og:description": "excerpt",
            "og:site_name": "site_name",
            "article:author": "author",
            "article:published_time": "published_time",
            "dc:title": "title",
            "dc:creator": "author",
            "dc:description": "excerpt",
            "dcterm:title": "title",
            "dcterm:creator": "author",
            "dcterm:description": "excerpt",
            "twitter:title": "title",
            "twitter:description": "excerpt",
        }
        name_map: dict[str, str] = {
            "author": "author",
            "description": "excerpt",
            "parsely-author": "author",
            "parsely-pub-date": "published_time",
            "parsely-title": "title",
        }

        for tag in soup.find_all("meta"):
            content = tag.get("content", "")
            if not content:
                continue
            content = _normalize_spaces(unescape(content))

            prop = tag.get("property", "")
            name = tag.get("name", "")

            # Match by property attribute.
            field = property_map.get(prop) or property_map.get(prop.lower())
            if field and not meta[field]:
                meta[field] = content
                continue

            # Match by name attribute.
            field = name_map.get(name) or name_map.get(name.lower())
            if field and not meta[field]:
                meta[field] = content

    @staticmethod
    def _shorten_title(title: str) -> str:
        """Remove site name suffixes/prefixes from *title*.

        Handles patterns like ``"Article Title | Site Name"`` by
        splitting on common separators and picking the most likely
        article title part.
        """
        parts = TITLE_SEPARATORS_RE.split(title)
        if len(parts) > 1:
            # Heuristic: the longest part is usually the title, not
            # the site name.  But if the longest part is very short
            # (< 2 words) and it's not significantly longer than the
            # second-longest, keep the original.
            sorted_parts = sorted(parts, key=len, reverse=True)
            best = sorted_parts[0]
            second = sorted_parts[1] if len(sorted_parts) > 1 else ""
            # Use the longest part if it's meaningfully longer than
            # the second part, OR if the first/last part is clearly
            # the title (common patterns).
            if len(best) > len(second):
                return best.strip()
            # If parts are roughly equal length, use the first one
            # (title typically comes first).
            return parts[0].strip()

        # Try colon separator.
        if ": " in title:
            colon_parts = title.split(": ")
            # Use text after colon if before-colon is short.
            if len(colon_parts[0].split()) <= 5:
                return ": ".join(colon_parts[1:]).strip()

        return title.strip()

    # ── Language / direction detection ────────────────────────────────────

    @staticmethod
    def _detect_lang(soup: Any) -> str | None:
        """Detect language from ``<html lang="...">``."""
        html_tag = soup.find("html")
        if html_tag is not None:
            lang = html_tag.get("lang")
            if lang:
                return lang if isinstance(lang, str) else str(lang)
        return None

    @staticmethod
    def _detect_dir(soup: Any) -> str | None:
        """Detect text direction from ``dir`` attribute."""
        for tag_name in ("html", "body"):
            tag = soup.find(tag_name)
            if tag is not None:
                d = tag.get("dir")
                if d and isinstance(d, str) and d.lower() in ("ltr", "rtl"):
                    return d.lower()
        return None

    # ── Unlikely candidate removal ───────────────────────────────────────

    def _remove_unlikely_candidates(self) -> None:
        """Remove elements whose class/id suggests non-content."""
        for tag in list(self._soup._all_descendants()):
            if tag.name in ("html", "body"):
                continue
            class_id = _get_class_id_string(tag)
            if len(class_id) <= 1:
                continue
            if UNLIKELY_CANDIDATES_RE.search(
                class_id
            ) and not OK_MAYBE_CANDIDATE_RE.search(class_id):
                tag.decompose()

    # ── Div-to-P transformation ──────────────────────────────────────────

    def _transform_divs_to_paragraphs(self) -> None:
        """Convert ``<div>`` elements without block children into ``<p>``."""
        for div in list(self._soup.find_all("div")):
            has_block = any(
                isinstance(c, self._Tag) and c.name in BLOCK_LEVEL_TAGS
                for c in div.children
            )
            if not has_block:
                div.name = "p"

    # ── Scoring ──────────────────────────────────────────────────────────

    # Maximum ancestor levels for score propagation.  The original
    # algorithm only propagated to parent (1x) and grandparent (0.5x).
    # Modern SPA-rendered pages nest content 3-5 levels deep in wrapper
    # divs, so we extend propagation with diminishing weights.
    _ANCESTOR_WEIGHTS = [1.0, 0.5, 0.333, 0.25]

    def _score_paragraphs(self) -> dict[int, dict[str, Any]]:
        """Score paragraph-like nodes and propagate to ancestors.

        Returns:
            Dict mapping ``id(tag)`` -> ``{"tag": tag, "score": float}``.
        """
        candidates: dict[int, dict[str, Any]] = {}

        for tag in self._soup.find_all(list(TAGS_TO_SCORE)):
            inner_text = _normalize_spaces(tag.get_text())
            if len(inner_text) < MIN_PARAGRAPH_LENGTH:
                continue

            # Collect ancestors up to the propagation depth.
            ancestors: list[Any] = []
            cur = tag.parent
            for _ in range(len(self._ANCESTOR_WEIGHTS)):
                if cur is None or cur.name in ("html", "body", "[document]"):
                    break
                ancestors.append(cur)
                cur = cur.parent

            # Ensure each ancestor is initialised in the candidate map.
            for anc in ancestors:
                if id(anc) not in candidates:
                    candidates[id(anc)] = {
                        "tag": anc,
                        "score": self._init_score(anc),
                    }

            # Content score for this paragraph.
            inner_len = len(inner_text)
            content_score = 1.0
            content_score += len(COMMAS_RE.findall(inner_text))
            content_score += min(inner_len / 100.0, 3.0)

            # Propagate to ancestors with diminishing weights.
            for i, anc in enumerate(ancestors):
                weight = self._ANCESTOR_WEIGHTS[i]
                candidates[id(anc)]["score"] += content_score * weight

        # Scale scores by link density.
        for entry in candidates.values():
            ld = self._get_link_density(entry["tag"])
            entry["score"] *= 1.0 - ld

        return candidates

    def _init_score(self, tag: Any) -> float:
        """Compute initial score for a node based on tag name and class/id."""
        score = float(TAG_WEIGHTS.get(tag.name, 0))
        score += self._get_class_weight(tag)
        return score

    @staticmethod
    def _get_class_weight(tag: Any) -> float:
        """Return ±25 weight based on class and id attribute content."""
        weight = 0.0
        for attr in ("class", "id"):
            value = tag.get(attr, "")
            if isinstance(value, list):
                value = " ".join(value)
            if not value:
                continue
            if NEGATIVE_RE.search(value):
                weight -= 25.0
            if POSITIVE_RE.search(value):
                weight += 25.0
        return weight

    @staticmethod
    def _get_link_density(tag: Any) -> float:
        """Ratio of link text length to total text length."""
        total_len = _text_length(tag)
        if total_len == 0:
            return 0.0
        link_len = sum(_text_length(a) for a in tag.find_all("a"))
        return link_len / total_len

    # ── Candidate selection ──────────────────────────────────────────────

    @staticmethod
    def _select_best_candidate(
        candidates: dict[int, dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Return the candidate with the highest score, or ``None``."""
        if not candidates:
            return None
        return max(candidates.values(), key=lambda c: c["score"])

    # ── Article assembly ─────────────────────────────────────────────────

    def _get_article(
        self, best: dict[str, Any], candidates: dict[int, dict[str, Any]]
    ) -> Any:
        """Build the article container from the best candidate + siblings.

        Args:
            best: The highest-scoring candidate dict.
            candidates: All scored candidates.

        Returns:
            A new ``Tag`` containing the article content.
        """
        best_tag = best["tag"]
        parent = best_tag.parent

        # Create an article wrapper.
        article = self._Tag("div")
        sibling_threshold = max(10.0, best["score"] * 0.1)

        # If there's no parent, use the candidate itself.
        if parent is None:
            article.append(best_tag.extract())
            return article

        for sibling in list(parent.children):
            if isinstance(sibling, str):
                if sibling.strip():
                    article.append(sibling)
                continue

            should_include = False

            if sibling is best_tag:
                should_include = True
            elif id(sibling) in candidates:
                if candidates[id(sibling)]["score"] >= sibling_threshold:
                    should_include = True
            elif isinstance(sibling, self._Tag) and sibling.name == "p":
                link_density = self._get_link_density(sibling)
                text = _normalize_spaces(sibling.get_text())
                text_len = len(text)
                if text_len > 80 and link_density < 0.25:
                    should_include = True
                elif (
                    text_len <= 80 and link_density == 0 and re.search(r"\.\s*$", text)
                ):
                    should_include = True

            if should_include:
                article.append(sibling.extract())

        return article

    # ── Sanitization ─────────────────────────────────────────────────────

    _HEADING_TAGS_SET = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
    # Combined list of form-related + heading tags for single find_all pass.
    _REMOVE_AND_HEADING_TAGS = list(REMOVE_TAGS | _HEADING_TAGS_SET)

    def _sanitize(self, article: Any) -> None:
        """Clean the extracted article of low-quality elements."""
        # 1+2. Remove form-related elements and low-quality headings in
        # a single find_all pass instead of two separate traversals.
        for tag in list(article.find_all(self._REMOVE_AND_HEADING_TAGS)):
            if tag.name in REMOVE_TAGS:
                tag.decompose()
            else:
                # Heading tag — check quality.
                if self._get_class_weight(tag) < 0:
                    tag.decompose()
                elif self._get_link_density(tag) > 0.33:
                    tag.decompose()

        # 3. Conditional cleanup of tables, divs, lists, etc. — single
        # find_all with all candidate tags instead of per-tag-name loops.
        self._clean_conditionally_all(article)

        # 4. Remove empty tags.
        self._remove_empty_tags(article)

    _EMBED_TAGS = frozenset({"embed", "object", "iframe"})

    @staticmethod
    def _count_child_tags(tag: Any, embed_tags: frozenset[str]) -> tuple:
        """Count p, img, li, input, and embed descendant tags in one pass.

        Args:
            tag: The parent element to inspect.
            embed_tags: Frozenset of tag names considered "embed-like".

        Returns:
            ``(p_count, img_count, li_count, input_count, embed_count)``.
        """
        p_count = img_count = li_count = input_count = embed_count = 0
        for desc in tag._all_descendants():
            dname = desc.name
            if dname == "p":
                p_count += 1
            elif dname == "img":
                img_count += 1
            elif dname == "li":
                li_count += 1
            elif dname == "input":
                input_count += 1
            elif dname in embed_tags:
                embed_count += 1
        return p_count, img_count, li_count, input_count, embed_count

    @staticmethod
    def _should_remove_conditionally(
        tag_name: str,
        class_weight: float,
        content_len: int,
        link_density: float,
        p_count: int,
        img_count: int,
        li_count: int,
        input_count: int,
        embed_count: int,
    ) -> bool:
        """Decide whether a conditionally-cleaned element should be removed.

        Args:
            tag_name: The tag name being evaluated.
            class_weight: CSS class/id weight for the element.
            content_len: Length of normalised inner text.
            link_density: Ratio of link text to total text.
            p_count: Number of ``<p>`` descendants.
            img_count: Number of ``<img>`` descendants.
            li_count: Number of ``<li>`` descendants.
            input_count: Number of ``<input>`` descendants.
            embed_count: Number of embed-like descendants.

        Returns:
            ``True`` if the element should be removed.
        """
        if img_count > 1 and p_count > 0 and (p_count / img_count) < 0.5:
            return True
        if li_count > p_count and tag_name not in ("ol", "ul"):
            return True
        if input_count > p_count / 3:
            return True
        if content_len < MIN_PARAGRAPH_LENGTH and (img_count == 0 or img_count > 2):
            return True
        if class_weight < 25 and link_density > 0.2:
            return True
        if class_weight >= 25 and link_density > 0.5:
            return True
        if (embed_count == 1 and content_len < 75) or (
            embed_count > 1 and content_len < 200
        ):
            return True
        return False

    _CLEAN_COND_TAGS_LIST = list(CLEAN_CONDITIONALLY_TAGS)

    def _clean_conditionally_all(self, article: Any) -> None:
        """Remove conditionally-cleaned elements in a single find_all pass."""
        for tag in list(article.find_all(self._CLEAN_COND_TAGS_LIST)):
            class_weight = self._get_class_weight(tag)
            # Quick reject: very negative weight.
            if class_weight < -25:
                tag.decompose()
                continue

            inner_text = _normalize_spaces(tag.get_text())
            comma_count = len(COMMAS_RE.findall(inner_text))

            # Commas indicate content-rich nodes; keep them.
            if comma_count >= 10:
                continue

            counts = self._count_child_tags(tag, self._EMBED_TAGS)
            content_len = len(inner_text)
            link_density = self._get_link_density(tag)

            if self._should_remove_conditionally(
                tag.name, class_weight, content_len, link_density, *counts
            ):
                tag.decompose()

    @staticmethod
    def _remove_empty_tags(article: Any) -> None:
        """Remove tags that have no text content and no images/embeds."""
        keep_tags = frozenset(
            {"img", "br", "hr", "embed", "object", "iframe", "video", "audio"}
        )
        # Process in reverse document order (children before parents) so
        # that a single pass is sufficient.
        for tag in reversed(article._all_descendants()):
            if tag.name in keep_tags:
                continue
            if not tag.children:
                tag.decompose()
            elif not tag.get_text(strip=True) and not tag.find_all(list(keep_tags)):
                tag.decompose()

    # ── Title fallback from headings ─────────────────────────────────────

    @staticmethod
    def _get_title_from_headings(soup: Any) -> str | None:
        """Try to find a title from ``<h1>`` or ``<h2>`` headings."""
        for level in ("h1", "h2"):
            heading = soup.find(level)
            if heading is not None:
                text = _normalize_spaces(heading.get_text())
                if text:
                    return text
        return None


# ── Module-level helpers ─────────────────────────────────────────────────────


def _str_or_none(value: Any) -> str | None:
    """Return a non-empty stripped string or ``None``."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None
