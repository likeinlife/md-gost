"""Table shape checks for pipe and grid tables."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Block, Document
from gost_lint.markdown.grid import Grid
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
SEPARATOR_ROW = re.compile(r"^[\s|:-]+$")


@rule("STYLE005", "error", "рассогласованная таблица")
def table_shape(doc: Document) -> FileIssue:
    """Handle table shape."""
    for block in doc.of_kind("table"):
        grid: Grid | None = block.meta.get("grid")
        if grid is not None:
            yield from _grid_shape_issues(block, grid)
            continue
        yield from _pipe_shape_issues(block)


def _grid_shape_issues(block: Block, grid: Grid) -> FileIssue:
    for offset, column, message in grid.errors:
        yield (block.start + offset, column, message)


def _pipe_shape_issues(block: Block) -> FileIssue:
    rows_with_lines = zip(block.meta["rows"], block.lines, strict=True)
    for offset, (row, line) in enumerate(rows_with_lines):
        if not SEPARATOR_ROW.match(line.strip()):
            yield from _row_shape_issues(block, row, offset)


def _row_shape_issues(block: Block, row: list[str], offset: int) -> FileIssue:
    width = len(block.meta["rows"][0])
    if len(row) != width:
        message = f"в строке {len(row)} ячеек, в заголовке {width} — "
        yield (block.start + offset, 1, f"{message}pandoc разберёт такую таблицу неверно")
    elif offset and not any(cell.strip() for cell in row):
        yield (block.start + offset, 1, "полностью пустая строка таблицы")
