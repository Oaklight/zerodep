# /// zerodep
# version = "0.3.0"
# deps = []
# tier = "medium"
# category = "data"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""XML ↔ dict converter with fault-tolerant LLM tag extraction — zero-dep, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides xmltodict-compatible ``parse`` / ``unparse`` for bidirectional XML ↔
dict conversion, plus ``extract_tags`` for fault-tolerant extraction of XML-like
tags from LLM output (unclosed tags, malformed nesting, streaming truncation).

Standard layer (xmltodict-compatible)::

    d = parse('<root><name>Alice</name><age>30</age></root>')
    # {'root': {'name': 'Alice', 'age': '30'}}

    xml_str = unparse({'root': {'name': 'Alice', 'age': '30'}})
    # '<?xml version="1.0" encoding="utf-8"?>\\n<root><name>Alice</name><age>30</age></root>'

Lenient layer (LLM tag extraction)::

    tags = extract_tags('<answer>42</answer>', 'answer')
    # [ExtractedTag(tag='answer', content='42', attrs={}, is_closed=True)]

    tags = extract_tags('Here is my thinking <thinking>let me reason')
    # [ExtractedTag(tag='thinking', content='let me reason', attrs={}, is_closed=False)]
"""

from __future__ import annotations

# ── stdlib xml import workaround ──────────────────────────────────────────────
# Our module name "xml" shadows the stdlib xml package.  We temporarily clear
# our path entries and module cache so that ``from xml.…`` resolves to the real
# stdlib package, then restore everything afterwards.
import os.path as _osp
import sys as _sys

_this_dir = _osp.dirname(_osp.abspath(__file__))
_parent_dir = _osp.dirname(_this_dir)

# 1. Save our partially-loaded module (Python sets sys.modules["xml"] = us
#    before executing this file).
_self_ref = _sys.modules.pop("xml", None)

# 2. Save and clear any xml.* entries that might be our module's artifacts
_saved_xml_sub: dict[str, object] = {}
for _k in list(_sys.modules):
    if _k.startswith("xml."):
        _saved_xml_sub[_k] = _sys.modules.pop(_k)

# 3. Remove our directory (and project root) from sys.path
_saved_path = _sys.path[:]
_sys.path = [p for p in _sys.path if _osp.abspath(p) not in (_this_dir, _parent_dir)]

# 4. Import the real stdlib xml sub-modules
from xml.parsers import expat as _expat  # noqa: E402
from xml.sax.saxutils import XMLGenerator as _XMLGenerator  # noqa: E402
from xml.sax.xmlreader import AttributesImpl as _AttributesImpl  # noqa: E402

# 5. Restore sys.path
_sys.path = _saved_path

# 6. Clean up stdlib xml entries from sys.modules, then restore ours
for _k in list(_sys.modules):
    if _k == "xml" or _k.startswith("xml."):
        del _sys.modules[_k]
_sys.modules.update(_saved_xml_sub)
if _self_ref is not None:
    _sys.modules["xml"] = _self_ref

import dataclasses  # noqa: E402
import io  # noqa: E402
import re  # noqa: E402
from typing import IO, Any, Callable  # noqa: E402

__all__ = [
    # Exceptions
    "XMLError",
    "ParsingInterrupted",
    # Data classes
    "ExtractedTag",
    # Public API
    "parse",
    "unparse",
    "extract_tags",
]

# ── Exceptions ────────────────────────────────────────────────────────────────


class XMLError(Exception):
    """Raised when XML parsing or serialization fails."""


class ParsingInterrupted(Exception):
    """Raised to interrupt streaming parse (future use)."""


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True, slots=True)
class ExtractedTag:
    """A tag extracted from text (possibly malformed XML).

    Attributes:
        tag: Tag name (e.g. ``"answer"``).
        content: Text content between open and close tags.
        attrs: Dictionary of attributes on the opening tag.
        is_closed: True if a matching close tag was found.
    """

    tag: str
    content: str
    attrs: dict[str, str]
    is_closed: bool


# ── SAX handler for parse() ──────────────────────────────────────────────────


class _DictSAXHandler:
    """Expat SAX event handler that builds a Python dict from XML events."""

    def __init__(
        self,
        *,
        xml_attribs: bool = True,
        attr_prefix: str = "@",
        cdata_key: str = "#text",
        force_cdata: bool = False,
        cdata_separator: str = "",
        postprocessor: Callable | None = None,
        dict_constructor: type = dict,
        strip_whitespace: bool = True,
        namespace_separator: str = ":",
        namespaces: dict[str, str | None] | None = None,
        force_list: bool | tuple[str, ...] | Callable | None = None,
        comment_key: str = "#comment",
    ) -> None:
        self.path: list[tuple[str, dict]] = []
        self.stack: list[tuple[dict, Any]] = []
        self.data: list[str] = []
        self.item: Any = None
        self.xml_attribs = xml_attribs
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
        self.namespace_separator = namespace_separator
        self.namespaces = namespaces or {}
        self.force_list = force_list
        self.comment_key = comment_key
        self.namespace_declarations: dict[str, str] = {}

    def _build_name(self, full_name: str) -> str:
        if self.namespace_separator not in full_name:
            return full_name
        ns_sep = self.namespace_separator
        parts = full_name.split(ns_sep, 1)
        if len(parts) < 2:
            return full_name
        namespace, local = parts
        if namespace in self.namespaces:
            prefix = self.namespaces[namespace]
            if prefix is None:
                return local
            return f"{prefix}{ns_sep}{local}"
        return full_name

    def _should_force_list(self, key: str, value: Any) -> bool:
        if self.force_list is None:
            return False
        if self.force_list is True:
            return True
        if isinstance(self.force_list, tuple):
            return key in self.force_list
        if callable(self.force_list):
            return self.force_list(self.path, key, value)
        return False

    def start_element(self, full_name: str, attrs: dict[str, str]) -> None:
        name = self._build_name(full_name)
        attrs = self.dict_constructor(
            (self._build_name(k), v) for k, v in attrs.items()
        )
        attr_entries = self.dict_constructor()
        if self.xml_attribs:
            for key, val in attrs.items():
                attr_entries[f"{self.attr_prefix}{key}"] = val
        self.path.append((name, attr_entries))
        self.stack.append((self.item, self.data))
        self.item = self.dict_constructor()
        self.data = []
        if self.xml_attribs:
            self.item.update(attr_entries)

    def end_element(self, full_name: str) -> None:
        name = self._build_name(full_name)
        text = (
            self.cdata_separator.join(self.data).strip()
            if self.strip_whitespace
            else self.cdata_separator.join(self.data)
        )
        if not text:
            text = None

        # Determine the value of this element
        if self.item:
            # Element has children
            if text is not None:
                self.item[self.cdata_key] = text
            value: Any = self.item
        elif text is not None:
            # Element has only text content
            if self.force_cdata:
                value = self.dict_constructor()
                value[self.cdata_key] = text
            else:
                value = text
        else:
            # Empty element
            if self.xml_attribs and self.path and self.path[-1][1]:
                # Has attributes but no text/children
                value = self.item if self.item else self.dict_constructor()
                if not value:
                    # Merge attributes into empty dict
                    value.update(self.path[-1][1])
            else:
                value = None

        # Pop back to parent
        self.item, self.data = self.stack.pop()
        if self.item is None:
            self.item = self.dict_constructor()

        # Apply postprocessor
        if self.postprocessor is not None:
            result = self.postprocessor(self.path, name, value)
            if result is None:
                self.path.pop()
                return
            name, value = result

        # Force list if needed
        if self._should_force_list(name, value):
            if not isinstance(value, list):
                value = [value]

        # Merge into parent
        if name in self.item:
            existing = self.item[name]
            if isinstance(existing, list):
                existing.append(value)
            else:
                self.item[name] = [existing, value]
        else:
            self.item[name] = value

        self.path.pop()

    def characters(self, data: str) -> None:
        self.data.append(data)

    def comments(self, data: str) -> None:
        if self.strip_whitespace:
            data = data.strip()
        if self.item is None:
            self.item = self.dict_constructor()
        if self.comment_key in self.item:
            existing = self.item[self.comment_key]
            if isinstance(existing, list):
                existing.append(data)
            else:
                self.item[self.comment_key] = [existing, data]
        else:
            self.item[self.comment_key] = data

    def start_namespace_decl(self, prefix: str, uri: str) -> None:
        self.namespace_declarations[prefix] = uri


# ── parse() ───────────────────────────────────────────────────────────────────


def parse(
    xml_input: str | bytes | IO[bytes],
    *,
    encoding: str | None = None,
    process_namespaces: bool = False,
    namespace_separator: str = ":",
    disable_entities: bool = True,
    process_comments: bool = False,
    xml_attribs: bool = True,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    force_cdata: bool = False,
    cdata_separator: str = "",
    postprocessor: Callable | None = None,
    dict_constructor: type = dict,
    strip_whitespace: bool = True,
    force_list: bool | tuple[str, ...] | Callable | None = None,
    comment_key: str = "#comment",
) -> dict | None:
    """Parse an XML document into a Python dict.

    Compatible with ``xmltodict.parse()``.  Attributes are prefixed with
    *attr_prefix* (default ``"@"``), text content is stored under *cdata_key*
    (default ``"#text"``), and same-name siblings auto-coalesce into lists.

    Args:
        xml_input: XML string, bytes, or file-like object.
        encoding: Character encoding override.
        process_namespaces: Expand namespace URIs in element names.
        namespace_separator: Separator between namespace and local name.
        disable_entities: Block entity declarations for security (XXE).
        process_comments: Include XML comments in the output.
        xml_attribs: Include element attributes in the output.
        attr_prefix: Prefix for attribute keys in the output dict.
        cdata_key: Key for text content in the output dict.
        force_cdata: Always wrap text content in a dict with *cdata_key*.
        cdata_separator: Separator for joining multiple text nodes.
        postprocessor: Callable ``(path, key, value) -> (key, value)`` or None.
        dict_constructor: Dict class to use (default ``dict``).
        strip_whitespace: Strip whitespace from text nodes.
        force_list: Force list creation — bool, tuple of tag names, or callable.
        comment_key: Key for XML comments in the output dict.

    Returns:
        Parsed dict, or None for empty documents.

    Raises:
        XMLError: If the XML is malformed.
    """
    handler = _DictSAXHandler(
        xml_attribs=xml_attribs,
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        force_cdata=force_cdata,
        cdata_separator=cdata_separator,
        postprocessor=postprocessor,
        dict_constructor=dict_constructor,
        strip_whitespace=strip_whitespace,
        namespace_separator=namespace_separator,
        force_list=force_list,
        comment_key=comment_key,
    )

    if process_namespaces:
        handler.namespaces = {}  # will be populated by namespace decl events

    parser = _expat.ParserCreate(
        encoding,
        namespace_separator if process_namespaces else None,
    )

    if disable_entities:
        try:
            parser.UseForeignDTD(True)
        except AttributeError:
            pass

        def _entity_decl_handler(*_args: Any) -> None:
            raise ValueError(
                "Entities are disabled (disable_entities=True). "
                "Set disable_entities=False to allow entity declarations."
            )

        parser.EntityDeclHandler = _entity_decl_handler

        try:
            feature_external_ges = _expat.XML_PARAM_ENTITY_PARSING_NEVER  # type: ignore[attr-defined]
            parser.SetParamEntityParsing(feature_external_ges)
        except AttributeError:
            pass

    parser.StartElementHandler = handler.start_element
    parser.EndElementHandler = lambda name: handler.end_element(name)
    parser.CharacterDataHandler = handler.characters

    if process_namespaces:
        parser.StartNamespaceDeclHandler = handler.start_namespace_decl

    if process_comments:
        parser.CommentHandler = handler.comments

    try:
        if isinstance(xml_input, str):
            parser.Parse(xml_input, True)
        elif isinstance(xml_input, bytes):
            parser.Parse(xml_input, True)
        else:
            # File-like object — read in chunks
            while True:
                chunk = xml_input.read(65536)
                if not chunk:
                    parser.Parse(b"", True)
                    break
                parser.Parse(chunk, False)
    except _expat.ExpatError as exc:
        raise XMLError(str(exc)) from exc
    except ValueError as exc:
        raise XMLError(str(exc)) from exc

    return handler.item


# ── unparse() ─────────────────────────────────────────────────────────────────

_INVALID_NAME_CHARS = re.compile(r'[<>/"\'\s]')


def _validate_name(value: str, kind: str = "element") -> None:
    """Validate an element or attribute name."""
    if not value:
        raise XMLError(f"Empty {kind} name")
    if _INVALID_NAME_CHARS.search(value):
        raise XMLError(f"Invalid character in {kind} name: {value!r}")


class _XMLGen(_XMLGenerator):
    """XMLGenerator subclass that supports comments."""

    def __init__(
        self, out: IO[str], encoding: str = "utf-8", short_empty_elements: bool = False
    ) -> None:
        super().__init__(out, encoding, short_empty_elements)

    def comment(self, text: str) -> None:
        self._write(f"<!--{text}-->")


def _emit(
    key: str,
    value: Any,
    content_handler: _XMLGen,
    *,
    attr_prefix: str,
    cdata_key: str,
    depth: int,
    preprocessor: Callable | None,
    pretty: bool,
    newl: str,
    indent: str,
    namespace_separator: str,
    namespaces: dict[str, str] | None,
    full_document: bool,
    comment_key: str,
) -> None:
    """Recursively emit XML elements via SAX content handler."""
    if preprocessor is not None:
        result = preprocessor(key, value)
        if result is None:
            return
        key, value = result

    if not isinstance(value, list):
        value = [value]

    for v in value:
        if v is None:
            v = {}  # noqa: PLW2901
        if isinstance(v, dict):
            _validate_name(key)
            attrs = {}
            children = []
            text = None
            comments = []

            for k2, v2 in v.items():
                if k2 == cdata_key:
                    text = v2
                elif k2 == comment_key:
                    if isinstance(v2, list):
                        comments.extend(v2)
                    else:
                        comments.append(v2)
                elif k2.startswith(attr_prefix):
                    attr_name = k2[len(attr_prefix) :]
                    _validate_name(attr_name, "attribute")
                    attrs[attr_name] = str(v2)
                else:
                    children.append((k2, v2))

            if pretty and depth > 0:
                content_handler.ignorableWhitespace(indent * depth)

            # Handle namespace in element name for output
            if namespaces and namespace_separator in key:
                parts = key.split(namespace_separator, 1)
                if len(parts) == 2:
                    ns, local = parts
                    for uri, prefix in namespaces.items():
                        if prefix == ns:
                            attrs[f"xmlns:{ns}"] = uri
                            break

            content_handler.startElement(key, _AttributesImpl(attrs))

            if text is not None:
                content_handler.characters(str(text))

            for comment_text in comments:
                content_handler.comment(str(comment_text))

            if children:
                if pretty:
                    content_handler.ignorableWhitespace(newl)
                for child_key, child_value in children:
                    _emit(
                        child_key,
                        child_value,
                        content_handler,
                        attr_prefix=attr_prefix,
                        cdata_key=cdata_key,
                        depth=depth + 1,
                        preprocessor=preprocessor,
                        pretty=pretty,
                        newl=newl,
                        indent=indent,
                        namespace_separator=namespace_separator,
                        namespaces=namespaces,
                        full_document=full_document,
                        comment_key=comment_key,
                    )
                if pretty:
                    content_handler.ignorableWhitespace(indent * depth)

            content_handler.endElement(key)
            if pretty:
                content_handler.ignorableWhitespace(newl)

        else:
            # Scalar value — emit as text element
            _validate_name(key)
            if pretty and depth > 0:
                content_handler.ignorableWhitespace(indent * depth)
            content_handler.startElement(key, _AttributesImpl({}))
            content_handler.characters(str(v))
            content_handler.endElement(key)
            if pretty:
                content_handler.ignorableWhitespace(newl)


def unparse(
    input_dict: dict,
    *,
    output: IO[str] | None = None,
    encoding: str = "utf-8",
    full_document: bool = True,
    short_empty_elements: bool = False,
    pretty: bool = False,
    indent: str = "\t",
    newl: str = "\n",
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    preprocessor: Callable | None = None,
    namespace_separator: str = ":",
    namespaces: dict[str, str] | None = None,
    comment_key: str = "#comment",
) -> str | None:
    """Convert a Python dict into an XML string.

    Compatible with ``xmltodict.unparse()``.  Keys prefixed with *attr_prefix*
    (default ``"@"``) become element attributes, *cdata_key* (default
    ``"#text"``) values become text content.

    Args:
        input_dict: Dictionary to convert.
        output: File-like object to write to.  If None, return a string.
        encoding: Output encoding (used in XML declaration).
        full_document: Include ``<?xml …?>`` declaration.
        short_empty_elements: Use ``<tag/>`` for empty elements.
        pretty: Pretty-print with indentation.
        indent: Indentation string (used when *pretty* is True).
        newl: Newline string (used when *pretty* is True).
        attr_prefix: Prefix for attribute keys in the input dict.
        cdata_key: Key for text content in the input dict.
        preprocessor: Callable ``(key, value) -> (key, value)`` or None.
        namespace_separator: Separator between namespace prefix and local name.
        namespaces: Dict mapping namespace URIs to prefixes.
        comment_key: Key for XML comments in the input dict.

    Returns:
        XML string if *output* is None, otherwise None.

    Raises:
        XMLError: If the dict cannot be serialized.
    """
    if not isinstance(input_dict, dict):
        raise XMLError(f"Expected dict, got {type(input_dict).__name__}")

    # Must have exactly one root key (excluding comment/attr keys)
    root_keys = [
        k for k in input_dict if not k.startswith(attr_prefix) and k != comment_key
    ]
    if len(root_keys) != 1:
        raise XMLError(
            f"Expected exactly one root element, got {len(root_keys)}: {root_keys}"
        )

    must_return = output is None
    if must_return:
        output = io.StringIO()

    content_handler = _XMLGen(output, encoding, short_empty_elements)
    if full_document:
        content_handler.startDocument()
    if pretty:
        content_handler.ignorableWhitespace(newl)

    root_key = root_keys[0]
    _emit(
        root_key,
        input_dict[root_key],
        content_handler,
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        depth=0,
        preprocessor=preprocessor,
        pretty=pretty,
        newl=newl,
        indent=indent,
        namespace_separator=namespace_separator,
        namespaces=namespaces,
        full_document=full_document,
        comment_key=comment_key,
    )

    if must_return:
        return output.getvalue()  # type: ignore[union-attr]
    return None


# ── extract_tags() ────────────────────────────────────────────────────────────

# Opening tag: <tagname ...attrs... > or <tagname ...attrs... />
_OPEN_TAG_RE = re.compile(
    r"<([a-zA-Z_][\w.-]*)"  # tag name
    r"((?:\s+[\w.:_-]+\s*=\s*"  # attribute name=
    r'(?:"[^"]*"|\'[^\']*\'|[^\s>]*))*)'  # attribute value
    r"\s*(/?)>"  # optional self-closing
)

_ATTR_RE = re.compile(
    r"([\w.:_-]+)\s*=\s*"
    r'(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
)


def _parse_attrs(attr_string: str) -> dict[str, str]:
    """Parse attributes from the attribute portion of an opening tag."""
    result: dict[str, str] = {}
    for m in _ATTR_RE.finditer(attr_string):
        key = m.group(1)
        val = (
            m.group(2)
            if m.group(2) is not None
            else (m.group(3) if m.group(3) is not None else m.group(4))
        )
        result[key] = val if val is not None else ""
    return result


def extract_tags(
    text: str,
    tag: str | None = None,
    *,
    first_only: bool = False,
) -> list[ExtractedTag]:
    """Extract XML-like tags from text, tolerating malformed XML.

    Designed for extracting structured tags from LLM output where the XML
    may be incomplete, improperly nested, or truncated mid-stream.

    Args:
        text: Raw text containing XML-like tags.
        tag: If provided, only extract tags with this name.  If None,
            extract all top-level tags found.
        first_only: If True, return after finding the first match.

    Returns:
        List of ``ExtractedTag`` objects.

    Example::

        >>> extract_tags('<answer>42</answer>', 'answer')
        [ExtractedTag(tag='answer', content='42', attrs={}, is_closed=True)]

        >>> extract_tags('Thinking... <thought>hmm')
        [ExtractedTag(tag='thought', content='hmm', attrs={}, is_closed=False)]
    """
    results: list[ExtractedTag] = []

    for m in _OPEN_TAG_RE.finditer(text):
        tag_name = m.group(1)
        attr_str = m.group(2)
        self_closing = m.group(3) == "/"

        if tag is not None and tag_name != tag:
            continue

        attrs = _parse_attrs(attr_str) if attr_str.strip() else {}

        if self_closing:
            results.append(
                ExtractedTag(
                    tag=tag_name,
                    content="",
                    attrs=attrs,
                    is_closed=True,
                )
            )
        else:
            # Search for matching closing tag with depth counting
            content_start = m.end()
            content, is_closed = _find_closing(text, content_start, tag_name)
            results.append(
                ExtractedTag(
                    tag=tag_name,
                    content=content,
                    attrs=attrs,
                    is_closed=is_closed,
                )
            )

        if first_only:
            break

    return results


def _find_closing(text: str, start: int, tag_name: str) -> tuple[str, bool]:
    """Find the matching closing tag, handling nested same-name tags.

    Returns:
        Tuple of (content, is_closed).
    """
    depth = 1
    pos = start
    open_pattern = re.compile(rf"<{re.escape(tag_name)}(?:\s[^>]*)?>")
    # Closing tag: </tagname> with optional whitespace
    close_pattern = re.compile(rf"</{re.escape(tag_name)}\s*>")

    while pos < len(text):
        # Find next open or close tag
        open_match = open_pattern.search(text, pos)
        close_match = close_pattern.search(text, pos)

        if close_match is None:
            # No closing tag found — unclosed
            return text[start:], False

        if open_match is not None and open_match.start() < close_match.start():
            # Nested open tag found before close
            # Check it's not self-closing
            full = text[open_match.start() : open_match.end()]
            if not full.rstrip(">").endswith("/"):
                depth += 1
            pos = open_match.end()
        else:
            depth -= 1
            if depth == 0:
                return text[start : close_match.start()], True
            pos = close_match.end()

    # Reached end of text without closing
    return text[start:], False


# ── Aliases ───────────────────────────────────────────────────────────────────

loads = parse
dumps = unparse
