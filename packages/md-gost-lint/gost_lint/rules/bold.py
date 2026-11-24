"""Check that body prose does not use bold emphasis."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.markdown.grid import Grid
from gost_lint.markdown.refs import strip_code
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
RuleIssue = tuple[int, int, str]
BoldMatch = re.Match[str]
BOLD = re.compile(r"\*\*(?P<text>[^*]+)\*\*")
PREVIEW_LENGTH = 30
NON_PROSE = ("code", "diagram", "listing", "heading", "comment", "formula")


@rule("STYLE001", "error", "жирный шрифт в основном тексте")
def bold_in_body(doc: Document) -> FileIssue:
    """Handle bold in body."""
    for block in doc.blocks:
        if block.kind not in NON_PROSE:
            yield from _bold_in_block(block)


def _bold_in_block(block: Block) -> FileIssue:
    grid: Grid | None = block.meta.get("grid")
    for offset, line in enumerate(block.lines):
        if _is_table_header(block, grid, offset):
            continue
        for match in BOLD.finditer(strip_code(line)):
            yield _bold_issue(block, offset, match)


def _is_table_header(block: Block, grid: Grid | None, offset: int) -> bool:
    if block.kind != "table":
        return False
    if grid is None:
        return offset == 0
    return offset < grid.header_offset


def _bold_issue(block: Block, offset: int, match: BoldMatch) -> RuleIssue:
    excerpt = match.group("text")[:PREVIEW_LENGTH]
    message = f"жирный «{excerpt}» — выделение допустимо только в заголовках"
    return (block.start + offset, match.start() + 1, message)
