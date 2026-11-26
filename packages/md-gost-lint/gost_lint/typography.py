"""Autofix a hyphen used as a dash, and straight quotes in prose.

Paired ``"`` become «». A spaced hyphen between words becomes an em dash;
the build later shortens it. An unpaired quote is reported and left in place.
Quotes that delimit code, math, link targets and attributes stay as written.
A hyphen inside an attribute value is prose and is rewritten with the rest.
"""

import re
from bisect import bisect_left, bisect_right
from collections.abc import Collection, Iterator

from gost_lint.markdown import Document
from gost_lint.repairs import Repair

HYPHEN = "TYPO001"
QUOTES = "TYPO002"
HYPHEN_MESSAGE = "дефис между словами — нужно тире «—» (сборка сама заменит его на короткое)"
QUOTE_MESSAGE = 'прямые кавычки " — в русском тексте ставятся «ёлочки»'
SKIP_KINDS = ("code", "diagram", "listing", "comment", "bib_marker", "formula")
HYPHEN_GAP = re.compile(r"(?<=[\w»)]) - (?=[\w«(])")
DASH_GAP = " — "
STRAIGHT = '"'
OPEN_QUOTE = "«"
CLOSE_QUOTE = "»"
ATTRIBUTE = "{"
OPENERS = "([{-—–"
CLOSERS = ".,;:!?)]}-—–…"
Mark = tuple[int, str]


class _Scan:
    """Scan prose lines that typography may edit."""

    def __init__(self, doc: Document) -> None:
        """Initialize the instance."""
        self.doc = doc

    def lines(self) -> Iterator[tuple[int, str]]:
        """Handle lines."""
        blocked = self.doc.format_scope.blocked
        for block in self.doc.blocks:
            if block.kind in SKIP_KINDS:
                continue
            for offset, line_text in enumerate(block.lines):
                number = block.start - 1 + offset
                if number not in blocked:
                    yield number, line_text

    def locked(self, line: int, start: int, end: int, *, attribute_ok: bool) -> bool:
        """Return whether the span is markup that must stay unchanged."""
        if not self.doc.prose.editable(line, start, end):
            return True
        token = self._token(line, start, end)
        if token is None:
            return False
        return token != ATTRIBUTE or not attribute_ok

    def quote_locked(self, line: int, index: int) -> bool:
        """Return whether this straight quote is a markup delimiter."""
        end = index + 1
        return self.locked(line, index, end, attribute_ok=False)

    def gap_locked(self, line: int, gap: re.Match[str]) -> bool:
        """Return whether this hyphen sits in code, math or a link target."""
        start, end = gap.span()
        return self.locked(line, start, end, attribute_ok=True)

    def _token(self, line: int, start: int, end: int) -> str | None:
        offset = self.doc.prose.starts[line]
        ends = self.doc.format_scope.ends
        index = bisect_left(ends, offset + start + 1)
        literals = self.doc.format_scope.literals
        if index == len(literals):
            return None
        start_at = literals[index][0]
        if start_at >= offset + end:
            return None
        return self._at(start_at)

    def _at(self, offset: int) -> str:
        starts = self.doc.prose.starts
        number = bisect_right(starts, offset) - 1
        column = offset - starts[number]
        return self.doc.lines[number][column]


def hyphen_repairs(doc: Document) -> Iterator[Repair]:
    """Handle hyphen repairs."""
    scan = _Scan(doc)
    for line, line_text in scan.lines():
        yield from _emit(scan, line, line_text, quotes=False, hyphens=True)


def quote_issues(doc: Document) -> Iterator[tuple[int, int, str]]:
    """Handle quote issues."""
    scan = _Scan(doc)
    for line, line_text in scan.lines():
        for index, char in enumerate(line_text):
            if char == STRAIGHT and not scan.quote_locked(line, index):
                yield line + 1, index + 1, QUOTE_MESSAGE


def typography_repairs(doc: Document, enabled: Collection[str]) -> Iterator[Repair]:
    """Handle typography repairs."""
    if HYPHEN not in enabled and QUOTES not in enabled:
        return
    scan = _Scan(doc)
    quotes = QUOTES in enabled
    hyphens = HYPHEN in enabled
    for line, line_text in scan.lines():
        yield from _emit(scan, line, line_text, quotes=quotes, hyphens=hyphens)


def _marks(scan: _Scan, line: int, line_text: str) -> list[Mark]:
    opened: list[int] = []
    marks: list[Mark] = []
    for index, char in enumerate(line_text):
        if char == STRAIGHT and not scan.quote_locked(line, index):
            _pair(line_text, index, opened, marks)
    return marks


def _pair(line_text: str, index: int, opened: list[int], marks: list[Mark]) -> None:
    if index == 0:
        opening = True
    else:
        previous = line_text[index - 1]
        opening = previous.isspace() or previous in OPENERS
    if index + 1 == len(line_text):
        closing = True
    else:
        following = line_text[index + 1]
        closing = following.isspace() or following in CLOSERS
    if opening and not (closing and opened):
        opened.append(index)
        return
    if closing and opened:
        start = opened.pop()
        marks.append((start, OPEN_QUOTE))
        marks.append((index, CLOSE_QUOTE))


def _emit(
    scan: _Scan,
    line: int,
    line_text: str,
    *,
    quotes: bool,
    hyphens: bool,
) -> Iterator[Repair]:
    marks = _marks(scan, line, line_text) if quotes else []
    chars = list(line_text)
    for index, glyph in marks:
        chars[index] = glyph
        yield Repair(QUOTES, line, index, index + 1, glyph, QUOTE_MESSAGE)
    if not hyphens:
        return
    for found in HYPHEN_GAP.finditer("".join(chars)):
        if not scan.gap_locked(line, found):
            yield Repair(HYPHEN, line, found.start(), found.end(), DASH_GAP, HYPHEN_MESSAGE)
