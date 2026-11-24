"""Protect literal source and layout-sensitive Markdown during mechanical edits."""

from __future__ import annotations

import re
from bisect import bisect_left
from collections.abc import Iterator
from typing import TYPE_CHECKING

from gost_lint.markdown.format_literals import inline_literals

if TYPE_CHECKING:
    from gost_lint.markdown.document import Document
    from gost_lint.markdown.types import Block

NumberedLines = Iterator[tuple[int, str]]
RAW_HTML = re.compile(r"^\s*<(pre|script|style|textarea|table|div|details)\b", re.IGNORECASE)
RAW_TEX = re.compile(r"^\s*\\begin\{([\w*]+)\}")
INDENTED = re.compile(r"^(?: {4}| {0,3}\t| {0,3}>)")
REFERENCE_DEF = re.compile(r"^\s*\[[^\]]+\]:")
SIMPLE_TABLE_RULE = re.compile(r"^\s*-{2,}(?:[ \t]+-{2,})+\s*$")
METADATA_KEY = re.compile(r"^\s*(?:[\w\"'-][^:]*:|[#!&])")
METADATA_END = re.compile(r"^(?:---|\.\.\.)\s*$")
VERBATIM = (
    "code",
    "diagram",
    "listing",
    "formula",
    "table",
    "table_marker",
    "eq_marker",
    "bib_marker",
    "comment",
    "image",
)


def _closing(line: str) -> str:
    html = RAW_HTML.match(line)
    if html:
        return f"</{html[1]}>".casefold()
    tex = RAW_TEX.match(line)
    return rf"\end{{{tex[1]}}}".casefold() if tex else ""


def _metadata_start(lines: list[str], number: int) -> bool:
    if number and lines[number - 1].strip():
        return False
    following = lines[number + 1 : number + 2]
    return bool(following and METADATA_KEY.match(following[0]))


def _raw_end(doc: Document, number: int) -> re.Pattern[str] | None:
    line = doc.lines[number]
    column = len(line) - len(line.lstrip()) + 1
    if not doc.is_prose_position(number, column):
        return None
    if line == "---" and _metadata_start(doc.lines, number):
        return METADATA_END
    closing = _closing(line)
    if closing and not line.rstrip().endswith("/>"):
        return re.compile(re.escape(closing), re.IGNORECASE)
    return None


def _layout_rows(doc: Document) -> Iterator[int]:
    rows = iter(enumerate(doc.lines))
    for number, line in rows:
        terminator = _raw_end(doc, number)
        if terminator is None:
            continue
        yield number
        if terminator != METADATA_END and terminator.search(line):
            continue
        yield from _until(rows, terminator)


def _until(rows: NumberedLines, terminator: re.Pattern[str]) -> Iterator[int]:
    for number, line in rows:
        yield number
        if terminator.search(line):
            break


def _layout_block(block: Block) -> bool:
    if block.kind != "paragraph":
        return False
    return any(
        REFERENCE_DEF.match(line) or SIMPLE_TABLE_RULE.fullmatch(line) for line in block.lines
    )


class FormatScope:
    """Represent Format Scope."""

    def __init__(self, document: Document) -> None:
        """Initialize the instance."""
        self.document = document
        self.blocked = set(_layout_rows(document))
        self.prose_ends = {block.end for block in document.of_kind("paragraph", "list")}
        self.verbatim = {
            row
            for block in document.of_kind(*VERBATIM)
            for row in range(block.start - 1, block.end)
        }
        for block in document.blocks:
            if _layout_block(block):
                self.blocked.update(range(block.start - 1, block.end))
        self.literals = list(inline_literals(document))
        self.ends = [end for _, end in self.literals]

    def table_allowed(self, block: Block) -> bool:
        """Handle table allowed."""
        if block.start - 1 in self.prose_ends:
            return False
        return all(
            row not in self.blocked and self.document.is_prose_position(row, 0)
            for row in range(block.start - 1, block.end)
        )

    def editable(self, line: int, start: int, end: int) -> bool:
        """Handle editable."""
        if (
            line in self.verbatim
            or line in self.blocked
            or INDENTED.match(self.document.lines[line])
        ):
            return False
        if not self.document.prose.editable(line, start, end):
            return False
        offset = self.document.prose.starts[line]
        index = bisect_left(self.ends, offset + start + 1)
        if index == len(self.literals):
            return True
        return self.literals[index][0] >= offset + end
