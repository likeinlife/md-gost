"""Detect row numbers typed into table cells instead of a number column."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from gost_lint.markdown import Block, Document
from gost_lint.markdown.grid import Grid
from gost_lint.rules.registry import rule
from gost_lint.rules.table_shape import SEPARATOR_ROW

FileIssue = Iterator[tuple[int, int, str]]
CELL_NUMBER = re.compile(r"^(?P<num>\d+)[.)]\s+\S.*$")
RowPosition = tuple[int, list[str]]
NumberedCell = tuple[int, re.Match[str]]
PREVIEW_LENGTH = 40


@dataclass
class TableRows:
    """Represent Table Rows."""

    rows: list[RowPosition]
    width: int

    @classmethod
    def from_pipe(cls, block: Block) -> "TableRows":
        """Build from pipe."""
        rows = block.meta["rows"]
        body = [
            (offset, row)
            for offset, (row, line) in enumerate(zip(rows, block.lines, strict=True))
            if offset and not SEPARATOR_ROW.match(line.strip())
        ]
        return cls(body, len(rows[0]))

    def issue_for_column(self, block: Block, column: int) -> tuple[int, int, str] | None:
        """Handle issue for column."""
        numbered_start = _numbered_column_start(self.rows, column)
        if numbered_start is None:
            return None
        offset, match = numbered_start
        excerpt = match.group(0)[:PREVIEW_LENGTH]
        message = f"«{excerpt}» — номер строки набран внутри ячейки; "
        return (
            block.start + offset,
            1,
            f"{message}под нумерацию заводят отдельную колонку «№»",
        )


@rule("STYLE006", "error", "номер строки внутри ячейки таблицы")
def table_row_numbering(doc: Document) -> FileIssue:
    """Handle table row numbering."""
    for block in doc.of_kind("table"):
        yield from _numbering_issues(block)


def _numbering_issues(block: Block) -> FileIssue:
    rows = _table_rows(block)
    minimum_rows = 2
    if len(rows.rows) < minimum_rows:
        return
    for column in range(rows.width):
        issue = rows.issue_for_column(block, column)
        if issue is not None:
            yield issue


def _table_rows(block: Block) -> TableRows:
    grid: Grid | None = block.meta.get("grid")
    if grid is not None:
        return _grid_rows(grid)
    return TableRows.from_pipe(block)


def _grid_rows(grid: Grid) -> TableRows:
    if grid.errors:
        return TableRows([], grid.columns)
    grouped: dict[int, RowPosition] = {}
    for cell in grid.cells:
        if cell.offset <= grid.header_offset:
            continue
        if cell.row not in grouped:
            empty_row = ["" for _cell in range(grid.columns)]
            grouped[cell.row] = (cell.offset, empty_row)
        grouped[cell.row][1][cell.column] = cell.text
    return TableRows(list(grouped.values()), grid.columns)


def _numbered_column_start(rows: list[RowPosition], column: int) -> NumberedCell | None:
    numbered = [
        numbered_cell for row in rows if (numbered_cell := _numbered_cell(row, column)) is not None
    ]
    minimum_numbered = 2
    if len(numbered) < minimum_numbered:
        return None
    if len(numbered) * 2 <= len(rows):
        return None
    found_numbers = [int(match.group("num")) for _, match in numbered]
    if found_numbers != list(range(1, len(numbered) + 1)):
        return None
    return numbered[0]


def _numbered_cell(row: RowPosition, column: int) -> NumberedCell | None:
    offset, cells = row
    if column >= len(cells):
        return None
    match = CELL_NUMBER.match(cells[column])
    if match:
        return (offset, match)
    return None
