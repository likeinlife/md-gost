"""Find the cited key and its bibliography within one manifest."""

import re
from dataclasses import dataclass

from lsprotocol import types

from gost_lint.lsp.bibliography_placement import bibliography_heading
from gost_lint.lsp.session import Cursor
from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan, line_key_spans

BARE_KEY = re.compile(r"(?<![\w\\/{#=])(?<!\]\()#(?P<key>bib:[\w-]+)")
PREFIX = "bib:"


@dataclass(frozen=True)
class Citation:
    """Represent Citation."""

    key: str
    bare: LabelSpan | None = None


def citation_at(cursor: Cursor) -> Citation | None:
    """Handle citation at."""
    point = cursor.position
    doc = cursor.document
    if point.line >= len(doc.lines):
        return None
    if not doc.is_prose_position(point.line, point.character):
        return None
    line = doc.lines[point.line]
    for span in line_key_spans(line, point.line):
        if span.label.startswith(PREFIX) and _on_key(span, point, line):
            return Citation(span.label)
    for match in BARE_KEY.finditer(line):
        if match.start() <= point.character <= match.end() and doc.is_prose_position(
            point.line,
            match.start("key"),
        ):
            return _bare_citation(match, point.line)
    return None


def _on_key(span: LabelSpan, point: types.Position, line: str) -> bool:
    start = span.start - 1
    if line[:start].endswith("["):
        start -= 1
    return start <= point.character <= span.end


def _bare_citation(match: re.Match[str], line: int) -> Citation:
    start, end = match.span()
    bracketed = match.string[:start].endswith("[")
    if bracketed and match.string.startswith("]", end):
        start -= 1
        end += 1
    key = match["key"]
    return Citation(key, LabelSpan(key, line, start, end))


def bibliography_document(cursor: Cursor) -> Document:
    """Handle bibliography document."""
    chapters = cursor.book.work.docs
    for chapter in chapters:
        if chapter.path.name.casefold() == "references.md":
            return chapter
    for chapter in chapters:
        if any(block.kind == "bib_marker" for _, block in chapter.definition_spans()):
            return chapter
    return next(filter(bibliography_heading, chapters), cursor.document)


def declaration(chapters: list[Document], key: str) -> tuple[Document, LabelSpan] | None:
    """Handle declaration."""
    for chapter in chapters:
        for span, _ in chapter.definition_spans():
            if span.label == key:
                return chapter, span
    return None
