"""Rewrite Markdown chapters the way the editor formats them."""

import re
from pathlib import Path

from gost_lint.markdown import Document
from gost_lint.markdown.format_tables import format_table
from gost_lint.repairs import applicable_repairs
from gost_lint.spacing import spaces

NEWLINE = re.compile(r"(\r\n|\r|\n)")
SAMPLE = Path("chapter.md")
ROOT = Path()


def format_text(text: str) -> str:
    """Align tables, clear redundant spaces, and keep a single trailing break."""
    if not text:
        return text
    return _ending("".join(_parts(text)))


def _parts(text: str) -> list[str]:
    document = Document.from_text(SAMPLE, ROOT, text)
    parts = NEWLINE.split(text)
    _spacing(document, parts)
    _tables(document, parts)
    return parts


def _spacing(document: Document, parts: list[str]) -> None:
    edits = applicable_repairs(spaces(document, document.format_scope))
    for edit in reversed(edits):
        index = 2 * edit.line
        parts[index] = edit.replace(parts[index])


def _tables(document: Document, parts: list[str]) -> None:
    for block in document.of_kind("table"):
        if not document.format_scope.table_allowed(block):
            continue
        formatted = format_table(block)
        start = block.start - 1
        if len(formatted) != block.end - start:
            continue
        for offset, line in enumerate(formatted):
            parts[2 * (start + offset)] = line


def _ending(text: str) -> str:
    document = Document.from_text(SAMPLE, ROOT, text)
    newline = _newline(text)
    if not document.lines or not _prose_tail(document):
        if text.endswith(("\n", "\r")):
            return text
        return text + newline
    trimmed = text
    while trimmed.endswith("\r\n"):
        trimmed = trimmed[:-2]
    while trimmed.endswith(("\n", "\r")):
        trimmed = trimmed[:-1]
    return trimmed + newline


def _prose_tail(document: Document) -> bool:
    if document.text.endswith(("\r", "\n")):
        return document.is_prose_position(len(document.lines), 0)
    last = len(document.lines) - 1
    return document.is_prose_position(last, len(document.lines[last]))


def _newline(text: str) -> str:
    matched = NEWLINE.search(text)
    if matched is None:
        return "\n"
    return matched[0]
