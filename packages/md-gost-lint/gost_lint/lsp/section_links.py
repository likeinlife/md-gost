"""Inline Markdown links to sections in a work and their completion edits."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.lsp.headings import headings
from gost_lint.lsp.marks import Mark
from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan

OPENER = r"(?<![!\\])\[(?:\\.|[^\[\]\\]|\[[^\[\]]*\])*\]\(\s*"
DESTINATION = r"(?P<path>(?![/\\])(?:[^()<>:\s#?]+\.md)?)#"
FRAGMENT = r"[^()<>\s#]*"
CONTEXT = rf"{OPENER}{DESTINATION}(?P<key>{FRAGMENT})"
PREFIX = re.compile(rf"{CONTEXT}$")
TITLE = r"(?:\s+(?:\"[^\"]*\"|'[^']*'))?"
LINK = re.compile(rf"{CONTEXT}{TITLE}\s*\)")
TAIL = re.compile(FRAGMENT)
KEY = "key"


def _chapter(document: Document, match: re.Match[str]) -> Path | None:
    path = unquote(match["path"])
    if not path:
        return None
    candidate = document.path.parent / path
    try:
        return candidate.resolve()
    except (OSError, RuntimeError, ValueError):
        # An invalid filename or symlink loop cannot match a loaded chapter.
        return candidate


def section_uses(document: Document) -> Iterator[Mark]:
    """Handle section uses."""
    for number, line in enumerate(document.lines):
        for match in LINK.finditer(line):
            if match[KEY] and document.is_prose_position(number, match.start() + 1):
                yield _use(document, number, match)


def _use(document: Document, number: int, match: re.Match[str]) -> Mark:
    key = unquote(match[KEY])
    span = LabelSpan(key, number, *match.span(KEY))
    chapter = _chapter(document, match)
    return Mark(span, match.span(), section=True, chapter=chapter)


@dataclass(frozen=True)
class Fragment:
    """Represent Fragment."""

    prefix: str
    chapter: Path | None
    start: int
    end: int
    closing: str

    def suggestions(self, documents: list[Document]) -> Iterator[Suggestion]:
        """Handle suggestions."""
        for target, mark, title in headings(documents):
            key = mark.span.label
            if self.chapter and self.chapter != target.path:
                continue
            if key.startswith(self.prefix):
                detail = f"{target.rel} — {title}"
                yield Suggestion(key, detail, key + self.closing, self.start, self.end)


def fragment_at(document: Document, number: int, column: int) -> Fragment | None:
    """Handle fragment at."""
    if number >= len(document.lines):
        return None
    source = document.lines[number]
    match = PREFIX.search(source[:column])
    if match is None:
        return None
    if not document.is_prose_position(number, match.start() + 1):
        return None
    tail = TAIL.match(source, column)
    if tail is None:
        message = "section link has no tail"
        raise ValueError(message)
    return _fragment(_chapter(document, match), match, tail.end(), source)


def _fragment(chapter: Path | None, match: re.Match[str], end: int, source: str) -> Fragment:
    prefix = unquote(match[KEY])
    closing = _closing(source[end:])
    return Fragment(prefix, chapter, match.start(KEY), end, closing)


def _closing(following: str) -> str:
    return "" if following.lstrip().startswith((")", '"', "'")) else ")"
