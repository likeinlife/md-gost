"""Normalize cell padding while keeping Pandoc grid edges and spans fixed."""

from gost_lint.markdown.grid import Grid, GridCell
from gost_lint.markdown.table_widths import text_width
from gost_lint.markdown.types import Block


def format_grid(block: Block) -> list[str]:
    """Format grid."""
    grid: Grid = block.meta["grid"]
    if grid.errors:
        return block.lines
    if any(len(row) != text_width(row) for row in block.lines):
        return block.lines
    indent = block.lines[0].partition("+")[0]
    if not all(line.startswith(indent) for line in block.lines):
        return block.lines
    rows = [line.removeprefix(indent).rstrip(" \t") for line in block.lines]
    for cell in grid.cells:
        _pad_cell(rows, grid, cell)
    return [indent + row for row in rows]


def _pad_cell(rows: list[str], grid: Grid, cell: GridCell) -> None:
    left = grid.column_edges[cell.column] + 1
    right = grid.column_edges[cell.column + cell.colspan]
    segment = slice(left, right)
    indexes = range(cell.offset, grid.row_edges[cell.row + cell.rowspan])
    populated = [index for index in indexes if rows[index][segment].strip(" ")]
    # Relative indentation across lines can express lists, paragraphs and code.
    if len(populated) == 1:
        _pad_at(rows, populated[0], segment)


def _pad_at(rows: list[str], index: int, segment: slice) -> None:
    row = rows[index]
    raw = row[segment]
    if raw.startswith("    ") or "|" in raw or "+" in raw:
        return
    text = raw.strip(" ")
    if len(text) < len(raw):
        text = f" {text}"
    before = row[: segment.start] + text.ljust(len(raw))
    rows[index] = before + row[segment.stop :]
