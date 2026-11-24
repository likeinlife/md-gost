"""Format data-table rows and apply page-break constraints."""

from typing import Any

from docx.table import Table

from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.tables.cells import format_cell
from gost_builder.postprocess.tables.row_constraints import (
    find_last_header_index,
    is_header_row,
    is_in_table_start_block,
    keep_row_paragraphs_together,
)


def format_table_rows(table: Table) -> None:
    """Format table rows."""
    last_header_index = find_last_header_index(table)
    row_count = len(table.rows)
    for index, row in enumerate(table.rows):
        _format_table_row(row, index, last_header_index, row_count)


def _format_table_row(row: Any, index: int, last_header_index: int, row_count: int) -> None:
    _prevent_row_split(row)
    is_header = is_header_row(row, index)
    _format_row_cells(row, is_header=is_header)
    if is_header or is_in_table_start_block(index, last_header_index, row_count):
        keep_row_paragraphs_together(row)


def _prevent_row_split(row: Any) -> None:
    properties = row._tr.get_or_add_trPr()
    if properties.find(f"{WORD_TAG_PREFIX}cantSplit") is None:
        properties.append(properties.makeelement(f"{WORD_TAG_PREFIX}cantSplit", {}))


def _format_row_cells(row: Any, *, is_header: bool) -> None:
    for cell in row.cells:
        format_cell(cell, is_header=is_header)
