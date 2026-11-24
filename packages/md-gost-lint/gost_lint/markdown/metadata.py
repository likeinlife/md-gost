"""Parse Pandoc attributes and Markdown table rows."""

import re
from collections.abc import Iterator
from types import MappingProxyType
from typing import Any

from gost_lint.markdown.pipe_rows import cells
from gost_lint.markdown.syntax import CAPTION_KEY, LABEL, LABEL_KEY, SOURCE_KEY

QUOTED_ATTRIBUTE = re.compile(r'(["\']).*?\1')
ATTRIBUTE_TOKEN = re.compile(
    r"""(?P<key>[\w:-]+)\s*=\s*(?P<quote>["'])(?P<value>(?:\\.|(?!(?P=quote))[^\\])*)"""
    r"(?P<close>(?P=quote))?|\.(?P<class>[\w#+-]+)|(?P<end>})|[^\s{}]+",
)
FIELD_KEYS = MappingProxyType({"file": SOURCE_KEY, "caption": CAPTION_KEY, "lines": "lines"})


def attribute_tokens(source: str, offset: int = 0) -> Iterator[re.Match[str]]:
    """Read Pandoc attributes up to the closing brace, preserving editor offsets."""
    for match in ATTRIBUTE_TOKEN.finditer(source, offset):
        if match["end"]:
            break
        yield match


def _blank_attribute(match: re.Match[str]) -> str:
    return " " * len(match[0])


def attribute_label(source: str) -> re.Match[str] | None:
    """Handle attribute label."""
    unquoted = QUOTED_ATTRIBUTE.sub(_blank_attribute, source)
    return LABEL.search(unquoted)


def _marker_label(label: re.Match[str]) -> str:
    """Join a Pandoc label kind and name."""
    kind = label.group("kind")
    name = label.group("name")
    return f"{kind}:{name}"


def attributes(source: str) -> dict[str, Any]:
    """Pull label, caption, line range and source from Pandoc attributes."""
    metadata: dict[str, Any] = {}
    label = attribute_label(source)
    if label:
        metadata[LABEL_KEY] = _marker_label(label)
    for match in attribute_tokens(source):
        key = FIELD_KEYS.get(match["key"])
        if key and match["close"]:
            metadata.setdefault(key, match["value"])
    return metadata


def table_rows(lines: list[str]) -> list[list[str]]:
    """Handle table rows."""
    return [cells(line) for line in lines]
