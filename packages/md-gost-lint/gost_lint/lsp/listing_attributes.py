"""Find an editable Pandoc listing file attribute on the opening fence."""

import re
from dataclasses import dataclass

from gost_lint.markdown import Document
from gost_lint.markdown.metadata import attribute_tokens
from gost_lint.markdown.syntax import FENCE

OPEN = re.compile(r"\s*\{")


@dataclass(frozen=True)
class FileAttribute:
    """Represent File Attribute."""

    start: int
    end: int
    quote: str
    closing: str

    @classmethod
    def from_match(cls, match: re.Match[str]) -> "FileAttribute":
        """Build from match."""
        quote, raw = match["quote"], match["value"]
        start, end = match.span("value")
        if match["close"]:
            return cls(start, end, quote, "")
        end = start + len(raw.removesuffix("}"))
        closing = quote if raw.endswith("}") else f"{quote}}}"
        return cls(start, end, quote, closing)


ListingAttribute = tuple[FileAttribute, list[str]]


def file_attribute(document: Document, line: int, column: int) -> ListingAttribute | None:
    """Handle file attribute."""
    if line >= len(document.lines) or not document.is_prose_position(line, 0):
        return None
    source = document.lines[line]
    fence = FENCE.match(source)
    if fence is None:
        return None
    opener = OPEN.match(source, fence.start("info"))
    if opener and _listing_opens(document, line):
        return _attributes(source, opener.end(), column)
    return None


def _listing_opens(document: Document, line: int) -> bool:
    blocks = document.of_kind("code", "listing")
    return any(block.start == line + 1 for block in blocks)


def _attributes(source: str, offset: int, column: int) -> ListingAttribute | None:
    tokens = list(attribute_tokens(source, offset))
    classes = [match["class"].casefold() for match in tokens if match["class"]]
    fields = (FileAttribute.from_match(match) for match in tokens if match["key"] == "file")
    for attribute in fields:
        if attribute.start <= column <= attribute.end:
            return attribute, classes
    return None
