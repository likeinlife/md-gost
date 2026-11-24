"""Scan inline syntax whose whitespace is data, including Pandoc link destinations."""

from __future__ import annotations

import re
from bisect import bisect_right
from typing import TYPE_CHECKING

from gost_lint.markdown.prose import BLANK_LINE, Span

if TYPE_CHECKING:
    from collections.abc import Iterator

    from gost_lint.markdown.document import Document

TOKEN = re.compile(r"\\[^\n]|\]\(|\$\$?|\{|</?[a-zA-Z]")
QUOTED = r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"
LINK_DELIMITERS = re.compile(rf"\\.|(?<=\s)(?:{QUOTED})|<[^>]*>|[()]")
MATH_END = re.compile(r"(?<![\\\s])\$(?![\d$])")
ATTRIBUTE_END = re.compile(rf"(?:{QUOTED}|[^{{}}\n'\"])*}}")
TAG_END = re.compile(rf"(?:{QUOTED}|[^<>'\"])*>")
LITERAL_TAG = re.compile(r"<(code|kbd|samp|pre|textarea|script|style)\b", re.IGNORECASE)


def _link_end(source: str, start: int, limit: int) -> int:
    depth = 1
    for token in LINK_DELIMITERS.finditer(source, start, limit):
        if token[0] == "(":
            depth += 1
        elif token[0] == ")":
            depth -= 1
            if not depth:
                return token.end()
    return limit


def _math_end(source: str, token: re.Match[str], limit: int) -> int:
    start = token.end()
    if token[0] == "$$":
        close = source.find("$$", start, limit)
        return close + 2 if close >= 0 else limit
    if start == limit or source[start].isspace():
        return start
    match = MATH_END.search(source, start, limit)
    return match.end() if match else limit


def _tag_end(source: str, token: re.Match[str], limit: int) -> int:
    tag = LITERAL_TAG.match(source, token.start(), limit)
    if tag:
        closing = re.compile(rf"</{tag[1]}\s*>", re.IGNORECASE)
        end = closing.search(source, tag.end(), limit)
        return end.end() if end else limit
    match = TAG_END.match(source, token.end(), limit)
    return match.end() if match else token.end()


def _end(source: str, token: re.Match[str], limit: int) -> int:
    symbol = token[0]
    if symbol == "](":
        return _link_end(source, token.end(), limit)
    if symbol.startswith("$"):
        return _math_end(source, token, limit)
    if symbol.startswith("<"):
        return _tag_end(source, token, limit)
    if symbol == "{":
        match = ATTRIBUTE_END.match(source, token.end(), limit)
        if match:
            return match.end()
    return token.end()


def _paragraph_literals(doc: Document, source: str, start: int, limit: int) -> Iterator[Span]:
    while start < limit:
        token = TOKEN.search(source, start, limit)
        if token is None:
            return
        start = token.end()
        line = bisect_right(doc.prose.starts, token.start()) - 1
        column = token.start() - doc.prose.starts[line] + 1
        if doc.is_prose_position(line, column):
            start = _end(source, token, limit)
            yield token.start(), start


def inline_literals(doc: Document) -> Iterator[Span]:
    """Handle inline literals."""
    source = "\n".join(doc.lines)
    start = 0
    for blank in BLANK_LINE.finditer(source):
        yield from _paragraph_literals(doc, source, start, blank.start())
        start = blank.end()
    yield from _paragraph_literals(doc, source, start, len(source))
