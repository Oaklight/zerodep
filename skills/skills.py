# /// zerodep
# version = "0.4.0"
# deps = ["frontmatter", "sparse_search"]
# tier = "medium"
# category = "data"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""Agent Skills runtime — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Parse, discover, manage, and select Agent Skills per the agentskills.io
specification.  A *skill* is a folder with a ``SKILL.md`` file containing
YAML frontmatter (properties) and Markdown body (instructions).  This module
provides:

* Parsing and validation of ``SKILL.md`` files.
* Directory discovery of skills.
* A registry for managing multiple skills.
* Pluggable query-based skill selection (pre-filter to save tokens).
* System-prompt generation (catalog XML and activation XML).

Basic usage::

    from skills import Skill, SkillRegistry

    # Parse a single skill
    skill = Skill.load("path/to/my-skill")
    print(skill.name, skill.description)

    # Discover and register skills
    registry = SkillRegistry()
    registry.discover("~/.agents/skills", ".agents/skills")

    # Pre-select relevant skills for a query, then generate catalog
    matches = registry.select("convert this PDF to markdown", top_k=5)
    catalog = to_catalog([m.skill for m in matches])

    # Generate full activation prompt for a skill
    prompt = matches[0].skill.to_prompt()

Requires Python 3.10+.
"""

from __future__ import annotations

import builtins
import html
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Protocol, runtime_checkable

__all__ = [
    # Exceptions
    "SkillError",
    "ParseError",
    "ValidationError",
    # Data classes
    "SkillProperties",
    "Skill",
    "SelectionResult",
    # Selector protocol and implementations
    "Selector",
    "KeywordSelector",
    "BM25Selector",
    # Registry
    "SkillRegistry",
    # Public API functions
    "validate",
    "to_catalog",
    "compose",
    "load",
    "loads",
    "discover",
    "filter_compatible",
]

# ---------------------------------------------------------------------------
# Sibling imports (guarded)
# ---------------------------------------------------------------------------


def _ensure_sibling_path(name: str) -> str:
    """Return the sibling module directory and prepend it to ``sys.path``."""
    sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


def _load_frontmatter():
    """Load sibling ``frontmatter`` helpers on demand."""
    _ensure_sibling_path("frontmatter")
    sys.modules.pop("frontmatter", None)
    try:
        from frontmatter import Document as FmDocument
        from frontmatter import dumps as fm_dumps
        from frontmatter import load as fm_load
        from frontmatter import loads as fm_loads

        return fm_load, fm_loads, fm_dumps, FmDocument
    except ImportError as exc:
        raise ImportError(
            "Skills module requires the sibling frontmatter module. "
            "Copy frontmatter/frontmatter.py into your project."
        ) from exc


_HAS_SEARCH = False

try:
    _ensure_sibling_path("sparse_search")
    sys.modules.pop("sparse_search", None)
    from sparse_search import Result as _SearchResult  # noqa: F401
    from sparse_search import SparseIndex as _SparseIndex

    _HAS_SEARCH = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_NAME_LENGTH = 64
_MAX_DESCRIPTION_LENGTH = 1024
_MAX_COMPATIBILITY_LENGTH = 500

_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

_ALLOWED_FIELDS = frozenset(
    {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
)

_SKILL_MD_NAMES = ("SKILL.md", "skill.md")

_RESOURCE_DIRS = ("scripts", "references", "assets")

_WORD_RE = re.compile(r"[\w]+", re.UNICODE)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SkillError(Exception):
    """Base exception for skill operations."""


class ParseError(SkillError):
    """Raised when SKILL.md parsing fails."""


class ValidationError(SkillError):
    """Raised when a skill fails spec validation."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SkillProperties:
    """SKILL.md frontmatter metadata per the Agent Skills spec.

    Attributes:
        name: Skill identifier — kebab-case, max 64 chars.
        description: What the skill does and when to use it, max 1024 chars.
        license: Optional license string (e.g. ``"MIT"``).
        compatibility: Optional compatibility notes, max 500 chars.
        allowed_tools: Optional tool patterns the skill requires (experimental).
        metadata: Arbitrary key-value pairs for client-specific properties.
    """

    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    allowed_tools: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a spec-conformant dictionary.

        Only includes optional fields when they have values.  The
        ``allowed_tools`` key is emitted as ``allowed-tools`` to match the
        YAML frontmatter convention.
        """
        d: dict[str, Any] = {"name": self.name, "description": self.description}
        if self.license is not None:
            d["license"] = self.license
        if self.compatibility is not None:
            d["compatibility"] = self.compatibility
        if self.allowed_tools is not None:
            d["allowed-tools"] = self.allowed_tools
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SkillProperties:
        """Create ``SkillProperties`` from a spec-conformant dictionary.

        Accepts both ``allowed_tools`` and ``allowed-tools`` key forms.

        Args:
            d: Dictionary with at least ``name`` and ``description``.

        Returns:
            A ``SkillProperties`` instance.

        Raises:
            KeyError: If required fields are missing.
        """
        allowed = d.get("allowed-tools", d.get("allowed_tools"))
        return cls(
            name=d["name"],
            description=d["description"],
            license=d.get("license"),
            compatibility=d.get("compatibility"),
            allowed_tools=str(allowed) if allowed is not None else None,
            metadata={str(k): str(v) for k, v in d["metadata"].items()}
            if d.get("metadata")
            else {},
        )


class Skill:
    """A parsed Agent Skill.

    A skill consists of frontmatter *properties* (name, description, …),
    Markdown *instructions* (the body of ``SKILL.md``), and optional
    resource directories (``scripts/``, ``references/``, ``assets/``).

    Use the :meth:`load` and :meth:`loads` factory methods to create
    instances.
    """

    __slots__ = ("_path", "_properties", "_instructions")

    def __init__(
        self,
        properties: SkillProperties,
        instructions: str,
        *,
        path: Path | None = None,
    ) -> None:
        self._path = path
        self._properties = properties
        self._instructions = instructions

    # -- convenience proxies ------------------------------------------------

    @property
    def path(self) -> Path | None:
        """Skill directory path, or ``None`` if parsed from text."""
        return self._path

    @property
    def properties(self) -> SkillProperties:
        """Frontmatter metadata."""
        return self._properties

    @property
    def instructions(self) -> str:
        """Markdown body (agent instructions)."""
        return self._instructions

    @property
    def name(self) -> str:
        """Skill name (kebab-case identifier)."""
        return self._properties.name

    @property
    def description(self) -> str:
        """One-line description of the skill."""
        return self._properties.description

    # -- resource discovery (lazy) ------------------------------------------

    def _list_resource_dir(self, dirname: str) -> list[Path]:
        if self._path is None:
            return []
        d = self._path / dirname
        if not d.is_dir():
            return []
        return sorted(p for p in d.iterdir() if p.is_file())

    @property
    def scripts(self) -> list[Path]:
        """Executable scripts in the ``scripts/`` directory."""
        return self._list_resource_dir("scripts")

    @property
    def references(self) -> list[Path]:
        """Reference documents in the ``references/`` directory."""
        return self._list_resource_dir("references")

    @property
    def assets(self) -> list[Path]:
        """Asset files in the ``assets/`` directory."""
        return self._list_resource_dir("assets")

    # -- factory methods ----------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> Skill:
        """Load a skill from a directory containing ``SKILL.md``.

        Args:
            path: Path to the skill directory (or directly to a ``SKILL.md``
                file).

        Returns:
            A parsed ``Skill`` instance.

        Raises:
            ParseError: If ``SKILL.md`` is not found or cannot be parsed.
        """
        path = Path(path).expanduser().resolve()

        if path.is_file():
            skill_md = path
            skill_dir = path.parent
        else:
            skill_md = _find_skill_md(path)
            skill_dir = path

        text = skill_md.read_text(encoding="utf-8")
        skill = cls.loads(text)
        # Attach directory path
        skill._path = skill_dir
        return skill

    @classmethod
    def loads(cls, text: str) -> Skill:
        """Parse a skill from ``SKILL.md`` text content.

        Args:
            text: Full content of a ``SKILL.md`` file.

        Returns:
            A parsed ``Skill`` instance (with ``path`` set to ``None``).

        Raises:
            ParseError: If the text cannot be parsed.
        """
        _fm_load, fm_loads, _fm_dumps, _FmDocument = _load_frontmatter()
        try:
            doc = fm_loads(text, handler="yaml")
        except Exception as exc:
            raise ParseError(f"Failed to parse SKILL.md: {exc}") from exc

        if not doc.metadata:
            raise ParseError(
                "SKILL.md must contain YAML frontmatter "
                "with at least 'name' and 'description'"
            )

        props = _build_properties(doc.metadata)
        return cls(properties=props, instructions=doc.content, path=None)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Skill:
        """Create a ``Skill`` from a dictionary.

        The dictionary should contain at least ``name``, ``description``,
        and ``instructions`` keys.  Optional keys: ``license``,
        ``compatibility``, ``allowed-tools``/``allowed_tools``,
        ``metadata``, ``path``.

        Args:
            d: Skill dictionary (e.g. from :meth:`to_dict`).

        Returns:
            A ``Skill`` instance.
        """
        props_keys = {k: v for k, v in d.items() if k not in ("instructions", "path")}
        props = SkillProperties.from_dict(props_keys)
        instructions = d.get("instructions", "")
        path = Path(d["path"]) if d.get("path") else None
        return cls(properties=props, instructions=instructions, path=path)

    # -- output -------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary with properties and instructions."""
        d = self._properties.to_dict()
        d["instructions"] = self._instructions
        if self._path is not None:
            d["path"] = str(self._path)
        return d

    def to_markdown(self) -> str:
        """Serialize the skill back to ``SKILL.md`` format.

        Generates a valid ``SKILL.md`` string with YAML frontmatter and
        the Markdown instruction body.  Round-trip safe::

            original = Skill.loads(text)
            rebuilt = Skill.loads(original.to_markdown())
            assert original.name == rebuilt.name

        Returns:
            A complete ``SKILL.md`` file content string.
        """
        _fm_load, _fm_loads, fm_dumps, FmDocument = _load_frontmatter()
        doc = FmDocument(self._properties.to_dict(), self._instructions)
        return fm_dumps(doc, handler="yaml")

    def describe(self) -> str:
        """Return a short catalog-level description (name + description)."""
        return f"{self.name}: {self.description}"

    def to_prompt(
        self,
        *,
        inline_resources: bool = False,
        max_inline_bytes: int = 64 * 1024,
    ) -> str:
        """Generate the full activation prompt (Level 2 progressive disclosure).

        Returns XML-wrapped skill content suitable for injection into an
        agent's system prompt.

        Args:
            inline_resources: If ``True``, include the actual file
                contents of resources (scripts, references, assets)
                inside the XML output.  When ``False`` (default), only
                file names are listed.
            max_inline_bytes: Maximum file size (bytes) to inline.
                Files larger than this are listed by name only.
                Defaults to 64 KiB.
        """
        parts = [f'<skill_content name="{html.escape(self.name)}">']
        parts.append(self._instructions)

        resource_entries: list[tuple[str, Path]] = []
        for dirname in _RESOURCE_DIRS:
            for p in self._list_resource_dir(dirname):
                resource_entries.append((f"{dirname}/{p.name}", p))

        if resource_entries:
            parts.append("<skill_resources>")
            for rel, full in resource_entries:
                escaped = html.escape(rel)
                if inline_resources:
                    content = _read_resource(full, max_inline_bytes)
                    if content is not None:
                        parts.append(
                            f'<file name="{escaped}">\n{html.escape(content)}\n</file>'
                        )
                    else:
                        parts.append(f"<file>{escaped}</file>")
                else:
                    parts.append(f"<file>{escaped}</file>")
            parts.append("</skill_resources>")

        parts.append("</skill_content>")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, path={self._path})"


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


@dataclass
class SelectionResult:
    """Result of skill selection.

    Attributes:
        skill: The matched skill.
        score: Relevance score (higher is better, scale depends on selector).
    """

    skill: Skill
    score: float


@runtime_checkable
class Selector(Protocol):
    """Protocol for skill selection strategies.

    Implement this protocol to create custom selectors (e.g. embedding-based,
    reranker, or lightweight-LLM selectors).  Any object with a matching
    ``select`` method can be passed to :meth:`SkillRegistry.select`.
    """

    def select(
        self, query: str, skills: list[Skill], top_k: int
    ) -> list[SelectionResult]: ...


class KeywordSelector:
    """Keyword overlap selector using token intersection.

    Scores skills by the proportion of query tokens that appear in the
    skill's name and description.  No external dependencies.
    """

    def select(
        self, query: str, skills: list[Skill], top_k: int
    ) -> list[SelectionResult]:
        """Select skills by keyword overlap.

        Args:
            query: User query string.
            skills: Candidate skills to rank.
            top_k: Maximum number of results.

        Returns:
            Top-k skills sorted by descending relevance score.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_set = set(query_tokens)
        results: list[SelectionResult] = []

        for skill in skills:
            text = f"{skill.name.replace('-', ' ')} {skill.description}"
            skill_tokens = set(_tokenize(text))
            if not skill_tokens:
                continue
            overlap = len(query_set & skill_tokens)
            if overlap > 0:
                score = overlap / len(query_set)
                results.append(SelectionResult(skill=skill, score=score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]


class BM25Selector:
    """BM25-based selector using the sibling ``search`` module.

    Indexes skills by their name, description, and instructions, then
    ranks them using BM25 scoring.

    Raises:
        ImportError: If the sibling ``search`` module is not available.
    """

    def __init__(self) -> None:
        if not _HAS_SEARCH:
            raise ImportError(
                "BM25Selector requires the sibling search module. "
                "Copy sparse_search/sparse_search.py into your project."
            )
        self._index: _SparseIndex | None = None
        self._skill_map: dict[str, Skill] = {}
        self._cache_key: tuple[str, ...] | None = None

    def _build_index(self, skills: list[Skill]) -> None:
        key = tuple(sorted(s.name for s in skills))
        if key == self._cache_key and self._index is not None:
            return
        self._index = _SparseIndex(variant="bm25")
        self._skill_map.clear()
        for skill in skills:
            name_text = skill.name.replace("-", " ")
            content = f"{name_text} {skill.description} {skill.instructions}"
            self._index.add(skill.name, content)
            self._skill_map[skill.name] = skill
        self._cache_key = key

    def select(
        self, query: str, skills: list[Skill], top_k: int
    ) -> list[SelectionResult]:
        """Select skills using BM25 ranking.

        Args:
            query: User query string.
            skills: Candidate skills to rank.
            top_k: Maximum number of results.

        Returns:
            Top-k skills sorted by descending BM25 score.
        """
        self._build_index(skills)
        assert self._index is not None
        hits = self._index.search(query, top_k=top_k)
        results: list[SelectionResult] = []
        for hit in hits:
            skill = self._skill_map.get(hit.doc_id)
            if skill is not None:
                results.append(SelectionResult(skill=skill, score=hit.score))
        return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class SkillRegistry:
    """Registry for discovering, managing, and selecting skills.

    Example::

        registry = SkillRegistry()
        registry.discover("~/.agents/skills", ".agents/skills")

        # Pre-filter and generate catalog
        matches = registry.select("convert PDF", top_k=5)
        catalog = registry.to_catalog([m.skill for m in matches])
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    # -- management ---------------------------------------------------------

    def register(self, skill: Skill, *, override: bool = False) -> None:
        """Register a skill.

        Args:
            skill: The skill to register.
            override: If ``True``, silently replace any existing skill
                with the same name.

        Raises:
            ValueError: If a skill with the same name is already registered
                and *override* is ``False``.
        """
        if skill.name in self._skills and not override:
            raise ValueError(
                f"Skill {skill.name!r} already registered; "
                "unregister it first or use a different name"
            )
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """Remove a skill by name.

        Args:
            name: Skill name to remove.

        Raises:
            KeyError: If the skill is not registered.
        """
        if name not in self._skills:
            raise KeyError(f"Skill {name!r} not registered")
        del self._skills[name]

    def get(self, name: str) -> Skill:
        """Get a skill by name.

        Args:
            name: Skill name.

        Returns:
            The registered skill.

        Raises:
            KeyError: If the skill is not registered.
        """
        if name not in self._skills:
            raise KeyError(f"Skill {name!r} not registered")
        return self._skills[name]

    def list(self) -> builtins.list[Skill]:
        """Return all registered skills."""
        return builtins.list(self._skills.values())

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __iter__(self) -> Iterator[Skill]:
        return iter(self._skills.values())

    # -- discovery ----------------------------------------------------------

    def discover(
        self,
        *paths: str | Path,
        recursive: bool = False,
        override: bool = False,
    ) -> builtins.list[Skill]:
        """Scan directories for skills and register them.

        Each path is scanned for subdirectories containing a ``SKILL.md``
        file.  Discovered skills are automatically registered.

        Args:
            *paths: Directories to scan.
            recursive: If ``True``, walk the full directory tree instead
                of scanning only immediate children.  Useful for
                hierarchical skill layouts like
                ``~/.agents/skills/category/my-skill/``.
            override: If ``True``, a newly discovered skill replaces any
                previously registered skill with the same name.  Useful
                for implementing precedence (e.g. project overrides
                user overrides system).

        Returns:
            List of newly discovered and registered skills.
        """
        found: builtins.list[Skill] = []
        for p in paths:
            resolved = Path(p).expanduser().resolve()
            if not resolved.is_dir():
                continue
            candidates = (
                _walk_skill_dirs(resolved) if recursive else _iter_child_dirs(resolved)
            )
            for child in candidates:
                try:
                    _find_skill_md(child)
                except ParseError:
                    continue
                try:
                    skill = Skill.load(child)
                except (ParseError, ValidationError):
                    continue
                if skill.name in self._skills and not override:
                    continue
                self._skills[skill.name] = skill
                found.append(skill)
        return found

    # -- selection ----------------------------------------------------------

    def select(
        self,
        query: str,
        *,
        top_k: int = 5,
        min_score: float = 0.0,
        available_tools: Iterable[str] | None = None,
        selector: Selector | None = None,
    ) -> builtins.list[SelectionResult]:
        """Pre-filter skills by relevance to a query.

        This is a harness-side pre-selection to reduce the number of skills
        injected into the system prompt (saving tokens).  The LLM then makes
        the final activation decision from the filtered catalog.

        Args:
            query: User query or task description.
            top_k: Maximum number of skills to return.
            min_score: Minimum relevance score.  Results below this
                threshold are discarded before applying ``top_k``.
            available_tools: If provided, only skills whose
                ``allowed_tools`` are satisfied by this set are
                considered.  Skills without ``allowed_tools`` always
                pass.  Tool names are matched case-insensitively; a
                pattern like ``Bash(git:*)`` is matched by its base
                name ``bash``.
            selector: Selection strategy.  Defaults to
                :class:`KeywordSelector`.

        Returns:
            Top-k skills sorted by descending relevance, all scoring
            at or above *min_score*.
        """
        if selector is None:
            selector = KeywordSelector()
        skills = self.list()
        if available_tools is not None:
            skills = filter_compatible(skills, available_tools)
        if not skills:
            return []
        results = selector.select(query, skills, top_k)
        if min_score > 0.0:
            results = [r for r in results if r.score >= min_score]
        return results

    # -- prompt generation --------------------------------------------------

    def to_catalog(self, skills: Iterable[Skill] | None = None) -> str:
        """Generate ``<available_skills>`` XML for a system prompt.

        Args:
            skills: Subset of skills to include.  If ``None``, includes all
                registered skills.

        Returns:
            XML string listing skill names, descriptions, and locations.
        """
        if skills is None:
            skills = self.list()
        return to_catalog(skills)

    def __repr__(self) -> str:
        names = ", ".join(sorted(self._skills))
        return f"SkillRegistry([{names}])"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(path: str | Path) -> list[str]:
    """Validate a skill directory per the Agent Skills spec.

    Args:
        path: Path to a skill directory.

    Returns:
        List of problems found (empty means valid).

    Example::

        problems = validate("my-skill")
        if problems:
            for p in problems:
                print(f"  - {p}")
    """
    problems: list[str] = []
    path = Path(path).expanduser().resolve()

    if not path.is_dir():
        problems.append(f"Not a directory: {path}")
        return problems

    # Check SKILL.md exists
    try:
        skill_md = _find_skill_md(path)
    except ParseError:
        problems.append("SKILL.md not found in directory")
        return problems

    # Parse frontmatter
    try:
        text = skill_md.read_text(encoding="utf-8")
        _fm_load, fm_loads, _fm_dumps, _FmDocument = _load_frontmatter()
        doc = fm_loads(text, handler="yaml")
    except Exception as exc:
        problems.append(f"Failed to parse YAML frontmatter: {exc}")
        return problems

    if not doc.metadata:
        problems.append("SKILL.md has no YAML frontmatter")
        return problems

    meta = doc.metadata

    # Check for unknown fields
    for key in meta:
        if key not in _ALLOWED_FIELDS:
            problems.append(f"Unknown frontmatter field: {key!r}")

    # name — required
    name = meta.get("name")
    if not name:
        problems.append("Missing required field: 'name'")
    elif not isinstance(name, str):
        problems.append(f"'name' must be a string, got {type(name).__name__}")
    else:
        if len(name) > _MAX_NAME_LENGTH:
            problems.append(
                f"'name' exceeds {_MAX_NAME_LENGTH} characters ({len(name)})"
            )
        if not _NAME_RE.match(name):
            problems.append(
                f"'name' must be lowercase kebab-case matching "
                f"{_NAME_RE.pattern!r}, got {name!r}"
            )
        # Check name matches directory
        dir_name = unicodedata.normalize("NFKC", path.name)
        skill_name = unicodedata.normalize("NFKC", name)
        if dir_name != skill_name:
            problems.append(
                f"'name' ({name!r}) does not match directory name ({path.name!r})"
            )

    # description — required
    desc = meta.get("description")
    if not desc:
        problems.append("Missing required field: 'description'")
    elif not isinstance(desc, str):
        problems.append(f"'description' must be a string, got {type(desc).__name__}")
    elif len(desc) > _MAX_DESCRIPTION_LENGTH:
        problems.append(
            f"'description' exceeds {_MAX_DESCRIPTION_LENGTH} characters ({len(desc)})"
        )

    # compatibility — optional, max length
    compat = meta.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            problems.append(
                f"'compatibility' must be a string, got {type(compat).__name__}"
            )
        elif len(compat) > _MAX_COMPATIBILITY_LENGTH:
            problems.append(
                f"'compatibility' exceeds {_MAX_COMPATIBILITY_LENGTH} "
                f"characters ({len(compat)})"
            )

    # metadata — optional, must be mapping with string values
    md = meta.get("metadata")
    if md is not None:
        if not isinstance(md, dict):
            problems.append(f"'metadata' must be a mapping, got {type(md).__name__}")

    return problems


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------


def to_catalog(skills: Iterable[Skill]) -> str:
    """Generate ``<available_skills>`` XML for a system prompt.

    This is the Level-1 progressive disclosure format — skill names,
    descriptions, and locations suitable for an agent's catalog view.

    Args:
        skills: Skills to include.

    Returns:
        XML string.
    """
    parts = ["<available_skills>"]
    for skill in skills:
        parts.append("<skill>")
        parts.append(f"<name>{html.escape(skill.name)}</name>")
        parts.append(f"<description>{html.escape(skill.description)}</description>")
        if skill.path is not None:
            skill_md = _find_skill_md_quiet(skill.path)
            loc = str(skill_md) if skill_md else str(skill.path)
            parts.append(f"<location>{html.escape(loc)}</location>")
        parts.append("</skill>")
    parts.append("</available_skills>")
    return "\n".join(parts)


def compose(*skills: Skill) -> str:
    """Compose multiple skills into a combined prompt.

    Concatenates the activation prompts of all given skills, suitable for
    injecting into a system prompt when multiple skills are active
    simultaneously.

    Args:
        *skills: Skills to compose.

    Returns:
        Combined prompt string.
    """
    return "\n\n".join(skill.to_prompt() for skill in skills)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def load(path: str | Path) -> Skill:
    """Load a skill from a directory or ``SKILL.md`` file.

    Args:
        path: Path to the skill directory or file.

    Returns:
        A parsed ``Skill`` instance.
    """
    return Skill.load(path)


def loads(text: str) -> Skill:
    """Parse a skill from ``SKILL.md`` text content.

    Args:
        text: Full content of a ``SKILL.md`` file.

    Returns:
        A parsed ``Skill`` instance.
    """
    return Skill.loads(text)


def discover(*paths: str | Path, recursive: bool = False) -> list[Skill]:
    """Discover skills in directories (convenience wrapper).

    Creates a temporary registry, discovers skills, and returns them.

    Args:
        *paths: Directories to scan.
        recursive: If ``True``, walk the full directory tree.

    Returns:
        List of discovered skills.
    """
    registry = SkillRegistry()
    return registry.discover(*paths, recursive=recursive)


def filter_compatible(
    skills: Iterable[Skill],
    available_tools: Iterable[str],
) -> list[Skill]:
    """Filter skills by tool compatibility.

    A skill passes if it has no ``allowed_tools`` requirement, or if
    every tool base name in its ``allowed_tools`` string is present in
    *available_tools*.

    Tool patterns like ``Bash(git:*)`` are matched by their base name
    (``bash``).  Matching is case-insensitive.

    Args:
        skills: Skills to filter.
        available_tools: Tool names available in the current environment
            (e.g. ``["Bash", "Read", "Write"]``).

    Returns:
        Skills whose tool requirements are satisfied.

    Example::

        compatible = filter_compatible(
            registry.list(),
            available_tools=["Bash", "Read", "Write", "Glob"],
        )
    """
    tool_set = {t.lower() for t in available_tools}
    result: list[Skill] = []
    for skill in skills:
        allowed = skill.properties.allowed_tools
        if allowed is None:
            result.append(skill)
            continue
        required = _parse_tool_names(allowed)
        if required <= tool_set:
            result.append(skill)
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _iter_child_dirs(root: Path) -> Iterator[Path]:
    """Yield sorted immediate child directories."""
    yield from sorted(d for d in root.iterdir() if d.is_dir())


def _walk_skill_dirs(root: Path) -> Iterator[Path]:
    """Walk the directory tree yielding dirs that contain a SKILL.md."""
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        if p == root:
            continue
        low = {f.lower() for f in filenames}
        if "skill.md" in low:
            yield p
            # Don't recurse into a skill directory's subdirectories
            dirnames.clear()
    return


def _find_skill_md(path: Path) -> Path:
    """Find ``SKILL.md`` in a directory.

    Args:
        path: Directory to search.

    Returns:
        Path to the ``SKILL.md`` file.

    Raises:
        ParseError: If no ``SKILL.md`` is found.
    """
    for name in _SKILL_MD_NAMES:
        candidate = path / name
        if candidate.is_file():
            return candidate
    raise ParseError(f"SKILL.md not found in {path}")


def _find_skill_md_quiet(path: Path) -> Path | None:
    """Find ``SKILL.md`` without raising."""
    for name in _SKILL_MD_NAMES:
        candidate = path / name
        if candidate.is_file():
            return candidate
    return None


def _build_properties(metadata: dict[str, Any]) -> SkillProperties:
    """Build ``SkillProperties`` from parsed frontmatter metadata.

    Args:
        metadata: Parsed YAML frontmatter dictionary.

    Returns:
        A ``SkillProperties`` instance.

    Raises:
        ParseError: If required fields are missing or invalid.
    """
    name = metadata.get("name")
    if not name or not isinstance(name, str):
        raise ParseError("SKILL.md frontmatter must contain a 'name' string field")

    description = metadata.get("description")
    if not description or not isinstance(description, str):
        raise ParseError(
            "SKILL.md frontmatter must contain a 'description' string field"
        )

    # Optional fields
    license_val = metadata.get("license")
    compatibility = metadata.get("compatibility")
    allowed_tools = metadata.get("allowed-tools")

    # Metadata: coerce values to strings
    raw_metadata = metadata.get("metadata")
    skill_metadata: dict[str, str] = {}
    if isinstance(raw_metadata, dict):
        for k, v in raw_metadata.items():
            skill_metadata[str(k)] = str(v)

    return SkillProperties(
        name=name,
        description=description,
        license=str(license_val) if license_val is not None else None,
        compatibility=str(compatibility) if compatibility is not None else None,
        allowed_tools=str(allowed_tools) if allowed_tools is not None else None,
        metadata=skill_metadata,
    )


_TOOL_ENTRY_RE = re.compile(r"([A-Za-z]\w*)(?:\([^)]*\))?")


def _parse_tool_names(allowed_tools: str) -> set[str]:
    """Extract lowercase base tool names from an ``allowed-tools`` string.

    ``"Bash(git:*) Read"`` → ``{"bash", "read"}``.
    Parenthesized parameters are skipped.
    """
    return {m.group(1).lower() for m in _TOOL_ENTRY_RE.finditer(allowed_tools)}


def _read_resource(path: Path, max_bytes: int) -> str | None:
    """Read a resource file if it fits within *max_bytes*.

    Returns ``None`` for binary files, files that exceed the size limit,
    or files that cannot be read.
    """
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer with lowercasing."""
    return [tok.lower() for tok in _WORD_RE.findall(text)]
