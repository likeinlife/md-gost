"""Whitespace checks that are safe to apply mechanically."""

from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.rules.registry import rule
from gost_lint.spacing import WHITESPACE, spaces

FileIssue = Iterator[tuple[int, int, str]]


@rule("TYPO005", "warning", "пробелы в конце строки или табуляция")
def trailing_whitespace(doc: Document) -> FileIssue:
    """Handle trailing whitespace."""
    for repair in spaces(doc, doc.format_scope):
        if repair.rule == WHITESPACE:
            yield repair.finding()
