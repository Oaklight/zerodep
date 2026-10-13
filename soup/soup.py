# /// zerodep
# version = "0.9.0"
# deps = []
# tier = "medium"
# category = "text"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""HTML parser with BeautifulSoup-like API — zero-dep, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides a lightweight DOM tree built on top of ``html.parser.HTMLParser``.
Supports ``find``, ``find_all``, ``select``, ``select_one``, ``get_text``,
``decompose``, and ``find_parent`` — the subset of BeautifulSoup used by
the vast majority of real-world scraping scripts.

Supports CSS pseudo-selectors: ``:first-child``, ``:last-child``,
``:only-child``, and ``:not(selector)``.  ``:not()`` takes a comma-separated
list of simple selectors, a compound selector carries at most one type or
universal token and it must come first, and an empty selector raises
``ValueError``.

Syntax this parser cannot read raises ``ValueError`` instead of being
skipped, so an unreadable selector never changes the match silently.  This is
not a claim to parse every selector the reference accepts: ``select`` lists
the supported subset, and forms outside it such as escapes, namespace
attribute selectors, sibling combinators and ``:is()``/``:where()``/``:has()``
raise here even where the reference accepts them.

Attribute selectors accept the Selectors L4 case-sensitivity flags
``[a=v i]`` (force ASCII case-insensitive) and ``[a=v s]`` (force
case-sensitive).  Without a flag, values of the HTML Standard's legacy
attribute set match ASCII case-insensitively; soupsieve 2.10 folds only
``type``, so the two intentionally diverge on the rest of that set.  Tag names
are matched case-sensitively as well, so ``P`` does not match ``<p>`` where
the reference does.

Does NOT implement: ``.prettify()``, ``.stripped_strings``, ``.descendants``
iterator, ``.next_sibling`` / ``.previous_sibling``, ``NavigableString`` class,
multiple parser backends.

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

# Legacy attributes whose values an HTML attribute selector matches ASCII
# case-insensitively.  Source: the HTML Standard, "Case-sensitivity of
# selectors" --
# https://html.spec.whatwg.org/multipage/semantics-other.html#case-sensitivity-of-selectors
# The names are stored ASCII-lowercased, and a selector's attribute name is
# folded the same way before the membership test.  Every other attribute
# value, and every attribute name, is matched case-sensitively.
_ASCII_CASE_INSENSITIVE_ATTRS = frozenset(
    {
        "accept",
        "accept-charset",
        "align",
        "alink",
        "axis",
        "bgcolor",
        "charset",
        "checked",
        "clear",
        "codetype",
        "color",
        "compact",
        "declare",
        "defer",
        "dir",
        "direction",
        "disabled",
        "enctype",
        "face",
        "frame",
        "hreflang",
        "http-equiv",
        "lang",
        "language",
        "link",
        "media",
        "method",
        "multiple",
        "nohref",
        "noresize",
        "noshade",
        "nowrap",
        "readonly",
        "rel",
        "rev",
        "rules",
        "scope",
        "scrolling",
        "selected",
        "shape",
        "target",
        "text",
        "type",
        "valign",
        "valuetype",
        "vlink",
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
        ``[attr=value]`` and the other attribute operators (``~=``, ``|=``,
        ``^=``, ``$=``, ``*=``), descendant (``a b``), child (``a > b``),
        compound (``div.cls#id``), multiple classes (``div.a.b``) and
        multiple ids (``#a#b``, which requires both and so matches nothing), the
        pseudo-classes ``:first-child``, ``:last-child``, ``:only-child`` and
        ``:not(...)``, and selector lists (``a, b``).  ``:not()`` takes a
        comma-separated list of simple selectors, so ``:not(.x, .y)`` means
        "neither".  A comma separates list groups only when it is outside a
        quoted value, outside brackets and outside parentheses, so
        ``[title="a,b"], [title="c"]`` is the union of two groups and not a
        descendant selector.

        Attribute selectors accept the Selectors L4 case-sensitivity flags
        ``[a=v i]`` (force ASCII case-insensitive) and ``[a=v s]`` (force
        case-sensitive).  Without a flag, values of the legacy HTML attribute
        set (``type``, ``lang``, ``dir``, ``rel``, ``method`` and the rest of
        the HTML Standard's list; see ``_ASCII_CASE_INSENSITIVE_ATTRS``) match
        ASCII case-insensitively and every other value stays case-sensitive.
        Only ASCII case is folded; attribute names and tag names stay
        case-sensitive, so ``[TYPE=a]`` and ``P`` miss where the reference
        matches.

        Syntax the parser cannot read raises ``ValueError`` instead of being
        skipped, which is the compatibility boundary for a vendoring caller:
        an empty or whitespace-only selector raises (it used to match every
        element), and an unreadable character such as ``!`` raises (a bare
        ``!`` used to match every element).  It is a boundary, not parity:
        forms outside the supported subset raise here even where the
        reference accepts them, so a caller migrating in should read this
        list rather than assume the reference's grammar.

        Args:
            css_selector: The CSS selector string.

        Returns:
            A list of matching ``Tag`` objects.

        Raises:
            ValueError: On any selector this parser cannot read.  The set is:

                - An empty or whitespace-only selector, and an empty group in
                  a selector list such as a trailing comma.
                - An unreadable character, such as the ``!`` in ``a!``.
                - Attribute syntax it cannot read: the namespace forms
                  ``[svg|use]``, ``[*|href]`` and ``[|href]``, the
                  jQuery-style ``[attr!="x"]``, more than one case flag, an
                  unquoted value that is not a CSS ident (``[href=/x]``,
                  ``[tabindex=1]``, ``[class=2col]``), a ``]`` inside a quoted
                  value as in ``[title="a]b"]``, ``[=x]``, unterminated quotes
                  such as ``[title="unterminated]``, and ``[xlink:href]``.
                - A compound selector with more than one type or universal
                  token, or a type or universal token after a subclass
                  (``**``, ``*a``, ``:not(p)span``, ``a:not(p)b``).
                - A malformed or unsupported ``:not()``: an empty argument or
                  empty list member, an unterminated ``:not(``, or a
                  combinator inside it such as ``:not(a b)``.
                - A pseudo-element such as ``::before``, and any pseudo-class
                  other than the four above.  The reference rejects
                  pseudo-elements with ``NotImplementedError``; both used to
                  make ``select`` return a plausible non-empty result.
        """
        groups = _parse_selector_list(css_selector)
        candidates: list[Tag] = self._all_descendants()
        return [
            tag
            for tag in candidates
            if any(_selector_matches(tag, parts) for parts in groups)
        ]

    def select_one(self, css_selector: str) -> Tag | None:
        """Like ``select``, but return only the first match (or ``None``).

        Args:
            css_selector: The CSS selector string.

        Returns:
            The first matching ``Tag``, or ``None``.
        """
        groups = _parse_selector_list(css_selector)
        for tag in self._all_descendants():
            if any(_selector_matches(tag, parts) for parts in groups):
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
# dummy).  A simple selector is a dict with optional keys ``tag``, ``ids``,
# ``classes``, ``attrs``, ``pseudos`` and ``nots``.  ``ids`` is a list like
# ``classes``: a compound may name more than one id, and every one of them
# must be present, which is how ``#a#b`` correctly matches nothing.

_SIMPLE_RE = re.compile(
    r"""
    (?P<tag>[a-zA-Z][a-zA-Z0-9-]*)     # tag name
    |(?P<universal>\*)                 # * universal selector
    |(?P<cls>\.[a-zA-Z_-][a-zA-Z0-9_-]*)  # .class
    |(?P<id>\#[a-zA-Z_-][a-zA-Z0-9_-]*)   # #id
    |(?P<attr>\[[^\]]+\])              # [attr] or [attr="val"]
    |(?P<pseudo>:(?:first-child|last-child|only-child))  # structural pseudo
    |(?P<not>:not\()                   # :not( — argument parsed separately
    """,
    re.VERBOSE,
)

_ATTR_RE = re.compile(
    r"""
    \[
    \s*(?P<name>[a-zA-Z_-][a-zA-Z0-9_-]*)
    (?:
        \s*(?P<op>[~|^$*]?=)\s*
        # An unquoted value is a CSS ident-token: a letter, ``_``, a non-ASCII
        # code point or one or two ``-`` to start, then letters, digits, ``-``,
        # ``_`` or non-ASCII.  Reserved characters such as ``=``, ``@``, ``~``,
        # ``,``, ``(`` and ``<`` are not part of an ident, so ``[a==b]`` and
        # ``[class=x=y]`` raise like the reference instead of swallowing the
        # character into the value.  A quoted value keeps its own grammar and
        # may contain any of them.  The ident grammar also keeps ``[a=]``
        # empty-invalid and ``[type=a i]`` a value plus a flag.
        (?P<value>"[^"]*"|'[^']*'|-{0,2}(?:[a-zA-Z_]|[^\x00-\x7f])(?:[a-zA-Z0-9_-]|[^\x00-\x7f])*)
        (?:\s+(?P<flag>[iIsS])\s*)?
    )?
    \s*\]
    """,
    re.VERBOSE,
)

# CSS attribute operators: ``=`` exact (against the serialised attribute),
# ``~=`` whitespace-separated list, ``|=`` exact or hyphen-prefixed,
# ``^=``/``$=``/``*=`` substring forms.  ``_attr_operator_matches`` is the one
# place that dispatches on them, and it rejects an operator the regex has no
# branch for.

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


def _unquote(value: str) -> str:
    """Strip one pair of matching surrounding quotes from *value*."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_attr_token(token: str) -> tuple[str, str | None, str, str | None] | None:
    """Parse an ``[attr]`` / ``[attr op value]`` selector token.

    Args:
        token: The raw ``[...]`` text as matched by ``_SIMPLE_RE``.

    Returns:
        ``(name, operator, value, flag)``.  ``operator`` is ``None`` for a
        bare ``[attr]`` presence test, and then ``flag`` is ``None`` too.  The
        flag is ``"i"`` or ``"s"`` for the Selectors L4 case-sensitivity
        flags, lowercased, and ``None`` when the selector has no flag.
        ``None`` is returned when the token uses syntax this parser does not
        implement, which lets the caller fail loudly rather than drop the
        constraint and widen the match.
    """
    m = _ATTR_RE.fullmatch(token)
    if m is None:
        return None
    op = m.group("op")
    if op is None:
        return (m.group("name"), None, "", None)
    flag = m.group("flag")
    return (
        m.group("name"),
        op,
        _unquote(m.group("value")),
        flag.lower() if flag else None,
    )


def _apply_regex_match(m: re.Match[str], compound: dict[str, Any]) -> None:
    """Populate *compound* dict from a single ``_SIMPLE_RE`` match."""
    if m.group("tag"):
        compound["tag"] = m.group("tag")
    elif m.group("universal"):
        pass  # ``*`` matches any tag; it constrains nothing on its own
    elif m.group("cls"):
        compound.setdefault("classes", []).append(m.group("cls")[1:])
    elif m.group("id"):
        compound.setdefault("ids", []).append(m.group("id")[1:])
    elif m.group("attr"):
        attr = _parse_attr_token(m.group("attr"))
        if attr is None:
            raise ValueError(
                f"unsupported attribute selector: {m.group('attr')} "
                "(supported: [attr] and [attr<op>value] with =, ~=, |=, ^=, "
                "$=, *=, optionally followed by the Selectors L4 flags i or s; "
                "the namespace forms and != are not implemented, more than "
                "one flag is rejected, and a ] inside a quoted value cannot "
                "be tokenised)"
            )
        compound.setdefault("attrs", []).append(attr)
    elif m.group("pseudo"):
        compound.setdefault("pseudos", []).append(m.group("pseudo")[1:])


def _parse_not_list(selector: str, pos: int) -> tuple[list[dict[str, Any]], int]:
    """Parse the argument of ``:not(...)`` as a list of simple selectors.

    *pos* points right after the opening ``(``.  The argument is a
    comma-separated list of compound simple selectors, and *new_pos* points
    past the closing ``)``.  The list comes back flattened, because
    ``:not(a, b)`` and ``:not(a):not(b)`` both mean "matches neither", which
    is exactly how multiple entries in a compound's ``nots`` are read.

    Args:
        selector: The full selector string.
        pos: Index just past the ``(`` of ``:not(``.

    Returns:
        ``(alternatives, new_pos)`` with one compound dict per comma-separated
        argument.

    Raises:
        ValueError: If the argument is empty, has an empty member, is
            unterminated, or contains anything that is not a simple selector.
            All of these previously parsed as something plausible instead.
    """
    alternatives: list[dict[str, Any]] = []
    pos = _skip_whitespace(selector, pos)
    if pos >= len(selector) or selector[pos] == ")":
        raise ValueError("empty :not() selector: :not() needs an argument")
    while True:
        compound, pos = _parse_compound(selector, pos)
        if compound is None:
            raise ValueError(
                f"unsupported selector inside :not(): {selector[pos:]!r} "
                "(only simple selectors and commas are supported inside "
                ":not(); combinators and nested groups are not)"
            )
        alternatives.append(compound)
        pos = _skip_whitespace(selector, pos)
        if pos >= len(selector):
            raise ValueError("unterminated :not(): missing closing parenthesis")
        ch = selector[pos]
        if ch == ")":
            return alternatives, pos + 1
        if ch == ",":
            pos = _skip_whitespace(selector, pos + 1)
            if pos >= len(selector) or selector[pos] in ",)":
                raise ValueError(
                    "empty selector list member in :not(): :not() cannot "
                    "contain an empty argument"
                )
            continue
        raise ValueError(
            f"unexpected {ch!r} in :not( at position {pos}: only simple "
            "selectors and commas are supported"
        )


def _parse_compound(selector: str, pos: int) -> tuple[dict[str, Any] | None, int]:
    """Parse a compound simple selector starting at *pos*.

    Returns ``(compound_dict_or_None, new_pos)``.
    """
    compound: dict[str, Any] = {}
    matched_any = False
    type_seen = False
    subclass_seen = False
    while pos < len(selector):
        m = _SIMPLE_RE.match(selector, pos)
        if m is None:
            break
        matched_any = True
        if m.group("not"):
            # :not( matched — parse the argument list and closing paren.  The
            # alternatives are appended flat: matching rejects the tag when it
            # matches any of them, which is the meaning of a :not() list.
            pos = m.end()
            alternatives, pos = _parse_not_list(selector, pos)
            compound.setdefault("nots", []).extend(alternatives)
            subclass_seen = True
            continue
        if m.group("tag") or m.group("universal"):
            # A compound selector carries at most one type or universal token
            # and it must come first.  Writing a second one used to overwrite
            # the first, so ``**`` matched every element; the reference rejects
            # it with "Tag name found at position N instead of at the start".
            if type_seen or subclass_seen:
                raise ValueError(
                    f"type selector at position {m.start()} must be the first "
                    "and only type or universal token in a compound selector"
                )
            type_seen = True
        else:
            subclass_seen = True
        _apply_regex_match(m, compound)
        pos = m.end()
    return (compound if matched_any else None), pos


def _tokens_to_steps(tokens: list[str | dict[str, Any]]) -> list[SelectorStep]:
    """Convert a flat token list into ``(combinator, simple)`` step list.

    Raises:
        ValueError: If a combinator has no compound on one side, as in ``>``,
            ``a >`` or ``> a``.  A dangling combinator used to be dropped, so
            a bare ``>`` matched every element; the reference rejects it.
    """
    steps: list[SelectorStep] = []
    combinator = "descendant"
    need_compound = True  # a combinator must be followed by a compound
    for tok in tokens:
        if tok == " ":
            combinator = "descendant"
        elif tok == ">":
            combinator = "child"
        else:
            assert isinstance(tok, dict)
            steps.append((combinator, tok))
            combinator = "descendant"
            need_compound = False
            continue
        if need_compound:
            raise ValueError(
                f"dangling combinator {tok!r} in selector: a combinator needs "
                "a simple selector on both sides"
            )
        need_compound = True
    if need_compound:
        last = tokens[-1] if tokens else None
        raise ValueError(
            f"dangling combinator {last!r} in selector: a combinator needs "
            "a simple selector on both sides"
        )
    return steps


def _parse_selector(selector: str) -> list[SelectorStep]:
    """Parse one selector group into a list of ``(combinator, simple)`` steps.

    Supported simple selectors: ``tag``, ``.class``, ``#id``, attribute
    selectors (``[attr]``, ``[attr<op>value]``, with the Selectors L4 ``i``
    and ``s`` flags), and the pseudo-classes ``:first-child``,
    ``:last-child``, ``:only-child`` and ``:not(...)``.  ``:not()`` takes a
    comma-separated list of simple selectors.  Combinators are descendant
    (whitespace) and child (``>``).

    Args:
        selector: One selector group, already split off any selector list.

    Returns:
        The parsed steps.

    An empty or whitespace-only selector never reaches this function: it is
    rejected by :func:`_parse_selector_list`, so a stripped group here is
    non-empty.

    Raises:
        ValueError: If the group contains a character this parser cannot
            read, a ``::pseudo-element``, or a malformed ``:not()``.  An
            unreadable character used to be skipped, which made a bare
            unknown character match every element.
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
            continue

        if selector.startswith("::", pos):
            raise ValueError(
                f"unsupported pseudo-element: {selector[pos:]!r} "
                "(pseudo-elements are not implemented; only the pseudo-classes "
                ":first-child, :last-child, :only-child and :not() are "
                "supported)"
            )
        raise ValueError(
            f"unreadable character {selector[pos]!r} in selector at position "
            f"{pos}: {selector!r} is not supported syntax"
        )

    return _tokens_to_steps(tokens)


def _split_selector_list(selector: str) -> list[str]:
    """Split a selector list on top-level commas.

    A comma separates two groups only when it is outside a quoted string,
    outside square brackets and outside parentheses.  A backslash escapes the
    next character inside a quoted string, so ``\\"`` does not close it.

    Args:
        selector: The raw selector string, e.g. ``'[title="a,b"], [title="c"]'``.

    Returns:
        The group strings, in order.  A selector with no top-level comma comes
        back as a single-element list, so callers keep the single-selector
        behaviour for free.
    """
    groups: list[str] = []
    start = 0
    bracket_depth = 0
    paren_depth = 0
    quote = ""
    i = 0
    n = len(selector)
    while i < n:
        ch = selector[i]
        if quote:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            if bracket_depth:
                bracket_depth -= 1
        elif ch == "(":
            paren_depth += 1
        elif ch == ")":
            if paren_depth:
                paren_depth -= 1
        elif ch == "," and not bracket_depth and not paren_depth:
            groups.append(selector[start:i])
            start = i + 1
        i += 1
    groups.append(selector[start:])
    return groups


def _parse_selector_list(selector: str) -> list[list[SelectorStep]]:
    """Parse a selector list into one step list per comma-separated group.

    The caller treats the groups as a union, which is how the reference reads
    a selector list: a tag matches when *any* group matches it.

    Args:
        selector: The raw selector string.

    Returns:
        A list with one parsed step list per group.

    Raises:
        ValueError: If the selector is empty or whitespace-only, or if a
            non-empty selector list contains an empty group such as a
            trailing comma.  Both parse to the match-all selector, so they
            would silently widen the match; the reference rejects them, and
            this module raises instead.
    """
    if not selector.strip():
        raise ValueError("empty selector: an empty selector would match every element")
    groups = _split_selector_list(selector)
    for group in groups:
        if not group.strip():
            raise ValueError(
                "empty selector group: a selector list cannot contain "
                "an empty group, which would match every element"
            )
    return [_parse_selector(group) for group in groups]


def _classes_match(tag: Tag, required_classes: list[str]) -> bool:
    """Return True if *tag* has all *required_classes*."""
    tag_classes = tag.attrs.get("class")
    if tag_classes is None:
        return False
    if isinstance(tag_classes, str):
        tag_classes = [tag_classes]
    return all(cls in tag_classes for cls in required_classes)


_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _ascii_lower(value: str) -> str:
    """Lowercase the ASCII letters in *value* and leave every other character.

    The HTML Standard defines selector case-insensitivity as *ASCII*
    case-insensitivity, so a non-ASCII letter such as ``É`` is not folded.
    """
    return value.translate(_ASCII_LOWER)


def _attr_text(actual: str | list[str]) -> str:
    """Return an attribute value as one string for substring matching.

    ``class`` is stored as a list, so it is joined with spaces, which is how
    the attribute appears in the source document.
    """
    return " ".join(actual) if isinstance(actual, list) else actual


def _attr_operator_matches(
    actual: str | list[str],
    op: str,
    expected: str,
    *,
    case_insensitive: bool = False,
) -> bool:
    """Return True if *actual* satisfies the CSS attribute operator *op*.

    Args:
        actual: The tag's attribute value; a list for ``class``.
        op: One of ``=``, ``~=``, ``|=``, ``^=``, ``$=``, ``*=``.
        expected: The value written in the selector, unquoted.
        case_insensitive: Fold ASCII case in both sides before comparing.
            Set for the legacy HTML attributes whose values selectors match
            ASCII case-insensitively (``_ASCII_CASE_INSENSITIVE_ATTRS``).

    Returns:
        Whether the attribute satisfies the operator.  The empty-value cases
        follow Selectors Level 4: the empty-string exclusion applies to
        ``~=``, ``^=``, ``$=`` and ``*=` (sections 6.1 and 6.2), so they never
        match an empty *expected*.  ``=`` has no exclusion and matches a value
        that is exactly empty.  ``|=`` has none either, so an empty *expected*
        matches a value that is exactly empty or begins with ``-`` (U+002D).
    """
    text = _attr_text(actual)
    if case_insensitive:
        text = _ascii_lower(text)
        expected = _ascii_lower(expected)
    if op == "=":
        # Compare the serialised attribute, as the reference does.  For the
        # list-valued ``class`` that makes ``[class="btn primary"]`` match and
        # ``[class="btn"]`` not match: the single-token form is ``~=``.
        return text == expected
    if op == "~=":
        return bool(expected) and expected in text.split()
    if op == "|=":
        # No bool(expected) guard here: Selectors 6.1 defines ``|=`` as
        # "exactly val, or beginning with val immediately followed by '-'"
        # and gives it no empty-string exclusion, so ``[attr|=""]`` matches
        # an exactly-empty value *and* one beginning with ``-``.  The guard
        # belongs on ``~=``/``^=``/``$=``/``*=`` only.
        return text == expected or text.startswith(expected + "-")
    if op == "^=":
        return bool(expected) and text.startswith(expected)
    if op == "$=":
        return bool(expected) and text.endswith(expected)
    if op == "*=":
        return bool(expected) and expected in text
    raise ValueError(f"unsupported attribute operator: {op}")  # pragma: no cover


def _selector_attrs_match(
    tag: Tag, attrs: list[tuple[str, str | None, str, str | None]]
) -> bool:
    """Return True if *tag* satisfies all attribute constraints from a selector.

    The case-sensitivity of a value comparison is chosen here: the ``i`` flag
    forces ASCII case-insensitive matching, the ``s`` flag forces
    case-sensitive matching, and with no flag a name in the HTML Standard's
    legacy set folds and every other name stays case-sensitive.
    """
    for attr_name, op, attr_val, flag in attrs:
        actual = tag.attrs.get(attr_name)
        if actual is None:
            return False
        if op is None:
            continue
        if flag == "i":
            case_insensitive = True
        elif flag == "s":
            case_insensitive = False
        else:
            case_insensitive = _ascii_lower(attr_name) in _ASCII_CASE_INSENSITIVE_ATTRS
        if not _attr_operator_matches(
            actual, op, attr_val, case_insensitive=case_insensitive
        ):
            return False
    return True


def _element_siblings(tag: Tag) -> list[Tag]:
    """Return element (non-text) children of *tag*'s parent."""
    if tag.parent is None:
        return [tag]
    return [c for c in tag.parent.children if isinstance(c, Tag)]


def _pseudo_matches(tag: Tag, pseudo: str) -> bool:
    """Return True if *tag* satisfies the structural pseudo-class *pseudo*."""
    siblings = _element_siblings(tag)
    if pseudo == "first-child":
        return siblings[0] is tag
    if pseudo == "last-child":
        return siblings[-1] is tag
    if pseudo == "only-child":
        return len(siblings) == 1
    return False  # pragma: no cover


def _simple_matches(tag: Tag, simple: dict[str, Any]) -> bool:
    """Check if *tag* matches a single compound simple selector."""
    if "tag" in simple and tag.name != simple["tag"]:
        return False
    if "ids" in simple:
        actual_id = tag.attrs.get("id")
        if any(actual_id != required for required in simple["ids"]):
            return False
    if "classes" in simple and not _classes_match(tag, simple["classes"]):
        return False
    if "attrs" in simple and not _selector_attrs_match(tag, simple["attrs"]):
        return False
    if "pseudos" in simple:
        for pseudo in simple["pseudos"]:
            if not _pseudo_matches(tag, pseudo):
                return False
    if "nots" in simple:
        for inner in simple["nots"]:
            if _simple_matches(tag, inner):
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
