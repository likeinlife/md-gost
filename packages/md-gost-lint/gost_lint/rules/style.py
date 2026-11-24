"""Prose formatting the build renders without complaint but GOST forbids."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.refs import strip_code
from gost_lint.markdown.syntax import LIST_ITEM
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]

PAREN_REF = re.compile(
    r"\(\s*(?:см\.\s*)?(?:таблиц\w*|рисун\w*|табл\.|рис\.)\s*"
    r"\[@(?:tbl|fig):[\w-]+\]\s*\)",
    re.IGNORECASE,
)
PROSE_KINDS = ("paragraph", "list")


@rule("STYLE002", "warning", "ссылка скобочной пометкой вместо оборота")
def parenthetical_reference(doc: Document) -> FileIssue:
    """Handle parenthetical reference."""
    for block in doc.of_kind(*PROSE_KINDS):
        for offset, line in enumerate(block.lines):
            for found in PAREN_REF.finditer(strip_code(line)):
                yield (
                    block.start + offset,
                    found.start() + 1,
                    (
                        f"«{found.group(0)}» — ссылку вписывают в предложение: "
                        f"«приведено в таблице [@tbl:…]»"
                    ),
                )


@rule("STYLE004", "warning", "список из одного пункта")
def single_item_list(doc: Document) -> FileIssue:
    """Handle single item list."""
    for block in doc.of_kind("list"):
        numbered_rows = [line for line in block.lines if LIST_ITEM.match(line)]
        if len(numbered_rows) == 1:
            yield (
                block.start,
                1,
                (
                    "список из одного пункта — либо это обычный абзац, "
                    "либо не хватает остальных пунктов"
                ),
            )
