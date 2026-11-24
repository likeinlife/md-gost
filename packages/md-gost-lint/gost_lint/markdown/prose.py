"""Source positions occupied by literal Markdown, comments and displayed mathematics."""

import re
from bisect import bisect_right
from collections.abc import Iterator
from itertools import accumulate

from gost_lint.markdown.fences import closes_fence
from gost_lint.markdown.syntax import FENCE, MATH_DELIM
from gost_lint.markdown.types import Block

OPAQUE = frozenset(("code", "diagram", "listing", "formula"))
INLINE_TOKEN = re.compile(r"\\[^\n]|<!--|`+")
BLANK_LINE = re.compile(r"\n[ \t]*\n")
Span = tuple[int, int]


class ProseMap:
    """Look up insertion points in Python code points regardless of source line endings."""

    def __init__(self, text: str, blocks: list[Block]) -> None:
        """Initialize the instance."""
        source = text.replace("\r\n", "\n").replace("\r", "\n")
        lengths = [len(line) + 1 for line in source.split("\n")]
        self.starts = list(accumulate(lengths, initial=0))
        opaque = _block_ranges(blocks, self.starts, len(source))
        self.ranges = list(_literal_ranges(source, opaque))
        self.begins = [start for start, _ in self.ranges]

    def visible(self, line: int, column: int) -> bool:
        """Handle visible."""
        if not 0 <= line < len(self.starts) - 1:
            return False
        offset = self.starts[line] + column
        index = bisect_right(self.begins, offset) - 1
        if index < 0:
            return True
        start, end = self.ranges[index]
        return not start < offset < end

    def editable(self, line: int, start: int, end: int) -> bool:
        """Check the whole half-open edit range for intersections with literal text."""
        offset = self.starts[line]
        index = bisect_right(self.begins, offset + end - 1) - 1
        previous_end = self.ranges[index][1] if index >= 0 else 0
        return previous_end <= offset + start


def _block_ranges(blocks: list[Block], starts: list[int], size: int) -> Iterator[Span]:
    for block in blocks:
        if block.kind in OPAQUE:
            end = size + 1
            if _closed(block):
                end = starts[block.end] - 1
            yield starts[block.start - 1], end


def _closed(block: Block) -> bool:
    if block.kind == "formula":
        first = block.lines[0].strip()
        has_body = len(block.lines) > 1 or first != MATH_DELIM
        return has_body and block.lines[-1].strip().endswith(MATH_DELIM)
    opening = FENCE.match(block.lines[0])
    return (
        len(block.lines) > 1
        and opening is not None
        and closes_fence(block.lines[-1], opening["fence"])
    )


def _literal_ranges(source: str, opaque: Iterator[Span]) -> Iterator[Span]:
    cursor = 0
    for start, end in opaque:
        if start < cursor:
            continue
        for begin, stop in _inline_ranges(source, cursor, start):
            yield begin, stop
            cursor = stop
        if cursor <= start:
            yield start, end
            cursor = end
    yield from _inline_ranges(source, cursor, len(source))


def _inline_ranges(source: str, start: int, limit: int) -> Iterator[Span]:
    while start < limit:
        token = INLINE_TOKEN.search(source, start, limit)
        if token is None:
            return
        if token[0] == "<!--":
            start = _comment_end(source, token.end())
        elif token[0].startswith("`"):
            start = _inline_code_end(source, token, limit)
        else:
            start = token.end()
            continue
        yield token.start(), start


def _comment_end(source: str, start: int) -> int:
    closing = source.find("-->", start)
    if closing == -1:
        return len(source) + 1
    return closing + len("-->")


def _inline_code_end(source: str, token: re.Match[str], limit: int) -> int:
    blank = BLANK_LINE.search(source, token.end(), limit)
    boundary = blank.start() if blank else limit
    delimiter = re.compile(rf"(?<!`){token[0]}(?!`)")
    closing = delimiter.search(source, token.end(), boundary)
    if closing:
        return closing.end()
    newline = source.find("\n", token.end(), boundary)
    if newline < 0:
        return boundary + 1
    return newline + 1
