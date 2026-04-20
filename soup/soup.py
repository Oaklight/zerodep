# /// zerodep
# version = "0.4.0"
# deps = []
# tier = "medium"
# category = "data"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""HTML parser with BeautifulSoup-like API — zero-dep, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides a lightweight DOM tree built on top of ``html.parser.HTMLParser``.
Supports ``find``, ``find_all``, ``select``, ``select_one``, ``get_text``,
``decompose``, and ``find_parent`` — the subset of BeautifulSoup used by
the vast majority of real-world scraping scripts.

Does NOT implement: ``.prettify()``, ``.stripped_strings``, ``.descendants``
iterator, ``.next_sibling`` / ``.previous_sibling``, ``NavigableString`` class,
multiple parser backends, CSS pseudo-selectors.

Example::

    soup = Soup("<html><body><p class='msg'>Hello</p></body></html>")
    print(soup.find("p", class_="msg").text)
    # Hello
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

__all__ = [
    "SELF_CLOSING_TAGS",
    "Tag",
    "Soup",
]

# ── Constants ─────────────────────────────────────────────────────────────────

SELF_CLOSING_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

# ── Tag ───────────────────────────────────────────────────────────────────────


class Tag:
    """A single HTML element node.

    Attributes:
        name: Tag name (e.g. ``"div"``).
        attrs: Dictionary of attribute name to value.  The ``class`` attribute
            is stored as a **list** of class names; all others as ``str``.
        children: Ordered child nodes — either ``Tag`` or plain ``str``.
        parent: Parent ``Tag``, or ``None`` for the root document.
    """

    __slots__ = ("name", "attrs", "children", "parent")

    def __init__(
        self,
        name: str,
        attrs: dict[str, str | list[str]] | None = None,
        parent: Tag | None = None,
    ) -> None:
        self.name: str = name
        self.attrs: dict[str, str | list[str]] = attrs if attrs is not None else {}
        self.children: list[Tag | str] = []
        self.parent: Tag | None = parent

    # ── Attribute access ──────────────────────────────────────────────────

    def get(self, attr: str, default: Any = None) -> Any:
        """Return attribute value, or *default* if not present."""
        return self.attrs.get(attr, default)

    def __getitem__(self, attr: str) -> Any:
        """Return attribute value; raise ``KeyError`` if missing."""
        return self.attrs[attr]

    def __contains__(self, attr: str) -> bool:
        return attr in self.attrs

    def __setitem__(self, attr: str, value: Any) -> None:
        """Set an attribute value (e.g. ``tag['id'] = 'main'``)."""
        self.attrs[attr] = value

    def __delitem__(self, attr: str) -> None:
        """Delete an attribute (e.g. ``del tag['id']``)."""
        del self.attrs[attr]

    # ── Text helpers ──────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        """Concatenated text content of this element and all descendants."""
        return self.get_text()

    @property
    def string(self) -> str | None:
        """If this element has exactly one text child (possibly nested), return it.

        Returns ``None`` when the element has no children, multiple children,
        or a mix of text and tags.
        """
        # Direct single-text child
        if len(self.children) == 1:
            child = self.children[0]
            if isinstance(child, str):
                return child
            return child.string
        # No children or multiple children -> None
        return None

    def get_text(self, separator: str = "", strip: bool = False) -> str:
        """Return all text under this element concatenated.

        Args:
            separator: Inserted between text fragments.
            strip: If ``True`` each fragment is whitespace-stripped and empty
                fragments are dropped.

        Returns:
            The combined text.
        """
        parts: list[str] = []
        self._collect_text(parts)
        if strip:
            parts = [p.strip() for p in parts]
            parts = [p for p in parts if p]
        return separator.join(parts)

    def _collect_text(self, acc: list[str]) -> None:
        for child in self.children:
            if isinstance(child, str):
                acc.append(child)
            else:
                child._collect_text(acc)

    # ── Tree modification ─────────────────────────────────────────────────

    def append(self, child: Tag | str) -> None:
        """Append *child* to this element's children.

        If *child* is a ``Tag`` already attached to a parent, it is first
        detached from its old position.

        Args:
            child: A ``Tag`` or plain text string to append.
        """
        if isinstance(child, Tag):
            if child.parent is not None:
                try:
                    child.parent.children.remove(child)
                except ValueError:
                    pass
            child.parent = self
        self.children.append(child)

    def insert(self, index: int, child: Tag | str) -> None:
        """Insert *child* at *index* in this element's children.

        Args:
            index: Position to insert at (same semantics as ``list.insert``).
            child: A ``Tag`` or plain text string to insert.
        """
        if isinstance(child, Tag):
            if child.parent is not None:
                try:
                    child.parent.children.remove(child)
                except ValueError:
                    pass
            child.parent = self
        self.children.insert(index, child)

    def extract(self) -> Tag:
        """Remove this element from its parent but keep its content intact.

        Unlike ``decompose``, the element and its subtree remain usable
        after extraction.

        Returns:
            This element (now detached).
        """
        if self.parent is not None:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
            self.parent = None
        return self

    def replace_with(self, new_node: Tag | str) -> Tag:
        """Replace this element with *new_node* in the parent's children.

        Args:
            new_node: The replacement ``Tag`` or text string.

        Returns:
            This element (now detached).

        Raises:
            ValueError: If the element has no parent.
        """
        if self.parent is None:
            raise ValueError("Cannot replace a detached element")
        parent = self.parent
        for i, child in enumerate(parent.children):
            if child is self:
                parent.children[i] = new_node
                if isinstance(new_node, Tag):
                    if new_node.parent is not None:
                        try:
                            new_node.parent.children.remove(new_node)
                        except ValueError:
                            pass
                    new_node.parent = parent
                self.parent = None
                return self
        raise ValueError("Element not found in parent's children")  # pragma: no cover

    def unwrap(self) -> None:
        """Remove this tag but keep its children (re-parent them).

        The children are spliced into the parent's children list at the
        position formerly occupied by this element.
        """
        if self.parent is None:
            return
        parent = self.parent
        idx = next(i for i, c in enumerate(parent.children) if c is self)
        # Splice children into parent at the position of this element.
        for child in self.children:
            if isinstance(child, Tag):
                child.parent = parent
        parent.children[idx : idx + 1] = self.children
        self.children = []
        self.parent = None

    def decompose(self) -> None:
        """Remove this element from its parent and discard its content."""
        if self.parent is not None:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
            self.parent = None
        self.children.clear()

    # ── Searching ─────────────────────────────────────────────────────────

    def find(
        self,
        name: str | list[str] | None = None,
        attrs: dict[str, str | bool] | None = None,
        *,
        class_: str | None = None,
        **kwargs: str | bool,
    ) -> Tag | None:
        """Return the first descendant matching the criteria, or ``None``.

        Args:
            name: Tag name(s) to match. ``None`` matches any tag.
            attrs: Dict of attribute filters.
            class_: Shorthand for ``attrs={"class": value}``.
            **kwargs: Extra attribute filters (``href=True`` means *has* href).

        Returns:
            The first matching ``Tag``, or ``None``.
        """
        results = self.find_all(name, attrs, class_=class_, limit=1, **kwargs)
        return results[0] if results else None

    def find_all(
        self,
        name: str | list[str] | None = None,
        attrs: dict[str, str | bool] | None = None,
        *,
        class_: str | None = None,
        limit: int | None = None,
        **kwargs: str | bool,
    ) -> list[Tag]:
        """Return all descendants matching the criteria.

        Args:
            name: Tag name(s) to match.
            attrs: Dict of attribute filters.
            class_: Shorthand for ``attrs={"class": value}``.
            limit: Stop after finding this many results.
            **kwargs: Extra attribute filters.

        Returns:
            A list of matching ``Tag`` objects.
        """
        merged = dict(attrs) if attrs else {}
        if class_ is not None:
            merged["class"] = class_
        merged.update(kwargs)

        # Fast path: name-only search with no attribute filters.
        if not merged:
            if isinstance(name, str):
                results: list[Tag] = []
                self._search_by_single_name(name, results, limit)
                return results
            if isinstance(name, list):
                name_set: frozenset[str] = frozenset(name)
                results = []
                self._search_by_name_set(name_set, results, limit)
                return results

        if isinstance(name, list):
            name_set = frozenset(name)
        else:
            name_set = None  # type: ignore[assignment]

        results = []
        self._search(name, name_set, merged, results, limit)
        return results

    def __call__(self, *args: Any, **kwargs: Any) -> list[Tag]:
        """Calling a tag is equivalent to ``find_all``."""
        return self.find_all(*args, **kwargs)

    def _search(
        self,
        name: str | list[str] | None,
        name_set: frozenset[str] | None,
        attr_filters: dict[str, str | bool],
        results: list[Tag],
        limit: int | None,
    ) -> None:
        for child in self.children:
            if limit is not None and len(results) >= limit:
                return
            if isinstance(child, Tag):
                if _matches(child, name, name_set, attr_filters):
                    results.append(child)
                    if limit is not None and len(results) >= limit:
                        return
                child._search(name, name_set, attr_filters, results, limit)

    def _search_by_name_set(
        self,
        name_set: frozenset[str],
        results: list[Tag],
        limit: int | None,
    ) -> None:
        """Fast path for searching by a set of tag names with no attr filters."""
        for child in self.children:
            if limit is not None and len(results) >= limit:
                return
            if isinstance(child, Tag):
                if child.name in name_set:
                    results.append(child)
                    if limit is not None and len(results) >= limit:
                        return
                child._search_by_name_set(name_set, results, limit)

    def _search_by_single_name(
        self,
        name: str,
        results: list[Tag],
        limit: int | None,
    ) -> None:
        """Fast path for searching by a single tag name with no attr filters."""
        for child in self.children:
            if limit is not None and len(results) >= limit:
                return
            if isinstance(child, Tag):
                if child.name == name:
                    results.append(child)
                    if limit is not None and len(results) >= limit:
                        return
                child._search_by_single_name(name, results, limit)

    # ── find_parent ───────────────────────────────────────────────────────

    def find_parent(self, name: str | None = None) -> Tag | None:
        """Walk up the tree and return the first ancestor matching *name*.

        Args:
            name: Tag name to match. ``None`` returns the immediate parent.

        Returns:
            The matching ancestor ``Tag``, or ``None``.
        """
        node = self.parent
        if name is None:
            return node
        while node is not None:
            if node.name == name:
                return node
            node = node.parent
        return None

    # ── CSS selectors ─────────────────────────────────────────────────────

    def select(self, css_selector: str) -> list[Tag]:
        """Return all descendants matching a CSS selector (simple subset).

        Supported patterns: ``tag``, ``.class``, ``#id``, ``[attr]``,
        ``[attr="value"]``, descendant (``a b``), child (``a > b``),
        compound (``div.cls#id``), multiple classes (``div.a.b``).

        Args:
            css_selector: The CSS selector string.

        Returns:
            A list of matching ``Tag`` objects.
        """
        parts = _parse_selector(css_selector)
        candidates: list[Tag] = self._all_descendants()
        return [tag for tag in candidates if _selector_matches(tag, parts)]

    def select_one(self, css_selector: str) -> Tag | None:
        """Like ``select``, but return only the first match (or ``None``).

        Args:
            css_selector: The CSS selector string.

        Returns:
            The first matching ``Tag``, or ``None``.
        """
        parts = _parse_selector(css_selector)
        for tag in self._all_descendants():
            if _selector_matches(tag, parts):
                return tag
        return None

    def _all_descendants(self) -> list[Tag]:
        """Collect all descendant Tag nodes in document order."""
        result: list[Tag] = []
        self._collect_descendants(result)
        return result

    def _collect_descendants(self, acc: list[Tag]) -> None:
        for child in self.children:
            if isinstance(child, Tag):
                acc.append(child)
                child._collect_descendants(acc)

    # ── Serialization ────────────────────────────────────────────────────

    def to_html(self) -> str:
        """Serialize this element and its descendants back to an HTML string.

        Returns:
            The HTML markup for this subtree.
        """
        parts: list[str] = []
        self._serialize(parts)
        return "".join(parts)

    def _serialize(self, acc: list[str]) -> None:
        """Recursively build HTML string pieces into *acc*."""
        # Build opening tag
        attr_parts: list[str] = []
        for k, v in self.attrs.items():
            if isinstance(v, list):
                attr_parts.append(f'{k}="{" ".join(v)}"')
            elif v == "":
                attr_parts.append(k)
            else:
                attr_parts.append(f'{k}="{v}"')
        attrs_str = (" " + " ".join(attr_parts)) if attr_parts else ""

        if self.name.lower() in SELF_CLOSING_TAGS:
            acc.append(f"<{self.name}{attrs_str}>")
            return

        acc.append(f"<{self.name}{attrs_str}>")
        for child in self.children:
            if isinstance(child, str):
                acc.append(child)
            else:
                child._serialize(acc)
        acc.append(f"</{self.name}>")

    def __str__(self) -> str:
        """Return the HTML serialization of this element."""
        return self.to_html()

    # ── Repr ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        attrs_str = ""
        if self.attrs:
            parts = []
            for k, v in self.attrs.items():
                if isinstance(v, list):
                    parts.append(f'{k}="{" ".join(v)}"')
                else:
                    parts.append(f'{k}="{v}"')
            attrs_str = " " + " ".join(parts)
        return f"<{self.name}{attrs_str}>"


# ── Match helpers ─────────────────────────────────────────────────────────────


def _check_name_match(
    tag: Tag,
    name: str | list[str] | None,
    name_set: frozenset[str] | None = None,
) -> bool:
    """Return True if *tag* satisfies the *name* filter."""
    if name is None:
        return True
    if name_set is not None:
        return tag.name in name_set
    if isinstance(name, list):
        return tag.name in name
    return tag.name == name


def _check_attr_filter(tag: Tag, key: str, expected: str | bool) -> bool:
    """Return True if *tag* satisfies a single attribute filter."""
    actual = tag.attrs.get(key)
    if expected is True:
        return actual is not None
    if expected is False:
        return actual is None
    # Value comparison
    if key == "class":
        return _class_matches(actual, expected)
    if actual is None:
        return False
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def _matches(
    tag: Tag,
    name: str | list[str] | None,
    name_set: frozenset[str] | None,
    attr_filters: dict[str, str | bool],
) -> bool:
    """Check whether *tag* satisfies *name* and *attr_filters*."""
    if not _check_name_match(tag, name, name_set):
        return False
    return all(_check_attr_filter(tag, k, v) for k, v in attr_filters.items())


def _class_matches(actual: str | list[str] | None, expected: str) -> bool:
    """Return True if *expected* class is present in *actual*.

    *actual* may be a list (``["a", "b"]``) or ``None``.
    *expected* is a single class name string.
    """
    if actual is None:
        return False
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


# ── CSS selector parser ───────────────────────────────────────────────────────

# A parsed selector is a list of *steps*.  Each step is
# ``(combinator, simple_selector_list)`` where combinator is one of
# ``"descendant"`` or ``"child"`` (the first step has ``"descendant"`` as a
# dummy).  A simple selector is a dict with optional keys ``tag``, ``id``,
# ``classes``, ``attrs``.

_SIMPLE_RE = re.compile(
    r"""
    (?P<tag>[a-zA-Z][a-zA-Z0-9-]*)     # tag name
    |(?P<cls>\.[a-zA-Z_-][a-zA-Z0-9_-]*)  # .class
    |(?P<id>\#[a-zA-Z_-][a-zA-Z0-9_-]*)   # #id
    |(?P<attr>\[[^\]]+\])              # [attr] or [attr="val"]
    """,
    re.VERBOSE,
)

_ATTR_RE = re.compile(
    r"""
    \[
    \s*(?P<name>[a-zA-Z_-][a-zA-Z0-9_-]*)
    (?:\s*=\s*["']?(?P<value>[^"'\]]*)["']?)?
    \s*\]
    """,
    re.VERBOSE,
)

SelectorStep = tuple[str, dict[str, Any]]


_WS = frozenset(" \t\n")


def _skip_whitespace(selector: str, pos: int) -> int:
    """Advance *pos* past any whitespace characters."""
    while pos < len(selector) and selector[pos] in _WS:
        pos += 1
    return pos


def _tokenize_whitespace(
    selector: str, pos: int, tokens: list[str | dict[str, Any]]
) -> int:
    """Handle whitespace at *pos*, emitting a combinator token if needed.

    Returns the updated position.
    """
    rest = selector[pos:].lstrip()
    if rest.startswith(">"):
        tokens.append(">")
        pos = selector.index(">", pos) + 1
        return _skip_whitespace(selector, pos)
    # Space combinator only if the previous token is not already a combinator
    if tokens and tokens[-1] not in (" ", ">"):
        tokens.append(" ")
    return pos + 1


def _apply_regex_match(m: re.Match[str], compound: dict[str, Any]) -> None:
    """Populate *compound* dict from a single ``_SIMPLE_RE`` match."""
    if m.group("tag"):
        compound["tag"] = m.group("tag")
    elif m.group("cls"):
        compound.setdefault("classes", []).append(m.group("cls")[1:])
    elif m.group("id"):
        compound["id"] = m.group("id")[1:]
    elif m.group("attr"):
        am = _ATTR_RE.match(m.group("attr"))
        if am:
            compound.setdefault("attrs", []).append(
                (am.group("name"), am.group("value"))
            )


def _parse_compound(selector: str, pos: int) -> tuple[dict[str, Any] | None, int]:
    """Parse a compound simple selector starting at *pos*.

    Returns ``(compound_dict_or_None, new_pos)``.
    """
    compound: dict[str, Any] = {}
    matched_any = False
    while pos < len(selector):
        m = _SIMPLE_RE.match(selector, pos)
        if m is None:
            break
        matched_any = True
        _apply_regex_match(m, compound)
        pos = m.end()
    return (compound if matched_any else None), pos


def _tokens_to_steps(tokens: list[str | dict[str, Any]]) -> list[SelectorStep]:
    """Convert a flat token list into ``(combinator, simple)`` step list."""
    steps: list[SelectorStep] = []
    combinator = "descendant"
    for tok in tokens:
        if tok == " ":
            combinator = "descendant"
        elif tok == ">":
            combinator = "child"
        else:
            assert isinstance(tok, dict)
            steps.append((combinator, tok))
            combinator = "descendant"
    return steps


def _parse_selector(selector: str) -> list[SelectorStep]:
    """Parse a simple CSS selector string into step list.

    Returns a list of ``(combinator, simple)`` tuples.
    """
    tokens: list[str | dict[str, Any]] = []
    pos = 0
    selector = selector.strip()

    while pos < len(selector):
        if selector[pos] in _WS:
            pos = _tokenize_whitespace(selector, pos, tokens)
            continue

        if selector[pos] == ">":
            tokens.append(">")
            pos = _skip_whitespace(selector, pos + 1)
            continue

        compound, pos = _parse_compound(selector, pos)
        if compound is not None:
            tokens.append(compound)
        else:
            pos += 1  # skip unknown character to avoid infinite loop

    return _tokens_to_steps(tokens)


def _classes_match(tag: Tag, required_classes: list[str]) -> bool:
    """Return True if *tag* has all *required_classes*."""
    tag_classes = tag.attrs.get("class")
    if tag_classes is None:
        return False
    if isinstance(tag_classes, str):
        tag_classes = [tag_classes]
    return all(cls in tag_classes for cls in required_classes)


def _attr_value_matches(actual: str | list[str], expected: str) -> bool:
    """Return True if *actual* attribute value equals *expected*."""
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def _selector_attrs_match(tag: Tag, attrs: list[tuple[str, str | None]]) -> bool:
    """Return True if *tag* satisfies all attribute constraints from a selector."""
    for attr_name, attr_val in attrs:
        actual = tag.attrs.get(attr_name)
        if actual is None:
            return False
        if attr_val is not None and not _attr_value_matches(actual, attr_val):
            return False
    return True


def _simple_matches(tag: Tag, simple: dict[str, Any]) -> bool:
    """Check if *tag* matches a single compound simple selector."""
    if "tag" in simple and tag.name != simple["tag"]:
        return False
    if "id" in simple and tag.attrs.get("id") != simple["id"]:
        return False
    if "classes" in simple and not _classes_match(tag, simple["classes"]):
        return False
    if "attrs" in simple and not _selector_attrs_match(tag, simple["attrs"]):
        return False
    return True


def _selector_matches(tag: Tag, steps: list[SelectorStep]) -> bool:
    """Return ``True`` if *tag* matches the full parsed selector."""
    if not steps:
        return True

    # The last step must match the tag itself.
    combinator, simple = steps[-1]
    if not _simple_matches(tag, simple):
        return False

    if len(steps) == 1:
        return True

    # Walk remaining steps backwards up the tree.
    remaining = steps[:-1]
    return _ancestor_matches(tag, remaining)


def _ancestor_matches(tag: Tag, steps: list[SelectorStep]) -> bool:
    """Verify that ancestors of *tag* satisfy the remaining selector steps."""
    if not steps:
        return True

    combinator, simple = steps[-1]
    rest = steps[:-1]

    if combinator == "child":
        parent = tag.parent
        if parent is None or not _simple_matches(parent, simple):
            return False
        return _ancestor_matches(parent, rest)
    else:
        # descendant — walk up until we find a match
        node = tag.parent
        while node is not None:
            if _simple_matches(node, simple):
                if _ancestor_matches(node, rest):
                    return True
            node = node.parent
        return False


# ── HTML parser ───────────────────────────────────────────────────────────────


class _TreeBuilder(HTMLParser):
    """Build a ``Tag`` tree from HTML markup.

    Args:
        skip_tags: Optional frozenset of tag names to omit from the tree.
            When a skipped tag is encountered, it and all its descendants
            (including text) are silently discarded.
    """

    def __init__(self, skip_tags: frozenset[str] | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Tag("[document]")
        self.current: Tag = self.root
        self._skip_tags: frozenset[str] = skip_tags or frozenset()
        # Depth counter for nested skipped tags (> 0 means discarding).
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # If we're inside a skipped subtree, track nesting depth only.
        if self._skip_depth > 0:
            if tag not in SELF_CLOSING_TAGS:
                self._skip_depth += 1
            return

        # Check if this tag should be skipped.
        if tag in self._skip_tags:
            if tag not in SELF_CLOSING_TAGS:
                self._skip_depth = 1
            return

        attr_dict: dict[str, str | list[str]] = {}
        for key, value in attrs:
            if value is None:
                value = ""
            if key == "class":
                attr_dict["class"] = value.split()
            else:
                attr_dict[key] = value

        node = Tag(tag, attr_dict, parent=self.current)
        self.current.children.append(node)

        if tag not in SELF_CLOSING_TAGS:
            self.current = node

    def handle_endtag(self, tag: str) -> None:
        # If we're inside a skipped subtree, decrement depth.
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        # Walk up to find the matching open tag (tolerates malformed HTML)
        node = self.current
        while node is not None and node.name != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self.current = node.parent
        # If no matching open tag found, do nothing (malformed HTML tolerance)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Explicit self-closing tag like <br/>
        if self._skip_depth > 0 or tag in self._skip_tags:
            return
        self.handle_starttag(tag, attrs)
        # Don't descend into it — it has no children.  If handle_starttag
        # pushed current down, pop back up.
        if self.current.name == tag:
            if self.current.parent is not None:
                self.current = self.current.parent

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        self.current.children.append(data)

    def handle_comment(self, data: str) -> None:
        # Comments are silently dropped (matching BS4 default).
        pass


# ── Soup (document root) ─────────────────────────────────────────────────────


class Soup(Tag):
    """Parse an HTML document and provide a BeautifulSoup-like API.

    Args:
        markup: The HTML string to parse.
        parser: Ignored (present only for API compatibility with BS4).
            Only ``"html.parser"`` is supported.
        skip_tags: Optional frozenset of tag names to omit during parsing.
            Skipped tags and all their descendants are silently discarded,
            which can significantly speed up parsing of pages with many
            ``<script>`` or ``<style>`` blocks.

    Example::

        soup = Soup("<p>Hello <b>world</b></p>")
        print(soup.find("b").text)
        # world
    """

    def __init__(
        self,
        markup: str,
        parser: str = "html.parser",
        skip_tags: frozenset[str] | None = None,
    ) -> None:
        super().__init__("[document]")
        builder = _TreeBuilder(skip_tags=skip_tags)
        builder.feed(markup)
        # Adopt the root's children as our own.
        self.children = builder.root.children
        for child in self.children:
            if isinstance(child, Tag):
                child.parent = self

    def new_tag(
        self, name: str, attrs: dict[str, str | list[str]] | None = None
    ) -> Tag:
        """Create a new detached ``Tag`` (not yet in the tree).

        Args:
            name: Tag name (e.g. ``"p"``).
            attrs: Optional attribute dictionary.

        Returns:
            A new ``Tag`` instance with no parent.
        """
        return Tag(name, attrs)

    def to_html(self) -> str:
        """Serialize the entire document back to an HTML string.

        Returns:
            The HTML markup for the whole document.
        """
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                child._serialize(parts)
        return "".join(parts)
