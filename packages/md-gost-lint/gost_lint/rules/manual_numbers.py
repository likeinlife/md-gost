"""Checks against manually entered table, figure, and formula numbers."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.refs import strip_code
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
MANUAL_NUMBER = re.compile(
    r"(?<![\w-])(?P<word>[Тт]аблиц[аеуы]|[Рр]исун(?:ок|ка|ке|ке)|[Лл]истинг[аеу]?|табл\.|рис\.)"
    r"\s*№?\s*(?P<num>\d+)",
)
MANUAL_EQ_NUMBER = re.compile(r"(?<![\w-])(?P<word>формул\w*)\s*№?\s*\(?(?P<num>\d+)\)?")
SKIP_KINDS = ("code", "diagram", "listing", "comment", "bib_marker", "formula")


def _prose_lines(doc: Document) -> Iterator[tuple[int, str]]:
    for block in doc.blocks:
        if block.kind in SKIP_KINDS:
            continue
        for offset, line in enumerate(block.lines):
            yield block.start + offset, strip_code(line)


@rule("EQ003", "error", "номер формулы набран руками")
def manual_formula_number(doc: Document) -> FileIssue:
    """Handle manual formula number."""
    for line, text in _prose_lines(doc):
        for found in MANUAL_EQ_NUMBER.finditer(text):
            message = f"«{found.group(0)}» — номера проставляет сборка, ссылайтесь меткой [@eq:…]"
            yield (line, found.start() + 1, message)


@rule("REF007", "error", "номер рисунка или таблицы набран руками")
def manual_number(doc: Document) -> FileIssue:
    """Handle manual number."""
    for line, text in _prose_lines(doc):
        for found in MANUAL_NUMBER.finditer(text):
            message = f"«{found.group(0)}» — номера проставляет сборка, "
            yield (
                line,
                found.start() + 1,
                f"{message}ссылайтесь меткой [@tbl:…], [@fig:…] или [@lst:…]",
            )
