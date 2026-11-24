"""Determine which table rows must stay connected across page breaks."""

from typing import Any

from docx.table import Table

from gost_builder.ooxml import WORD_TAG_PREFIX


def find_last_header_index(table: Table) -> int:
    """Find last header index."""
    last_header_index = 0
    for index, row in enumerate(table.rows):
        if index and not _repeats_header(row):
            break
        last_header_index = index
    return last_header_index


def _repeats_header(row: Any) -> bool:
    return row._tr.find(f"{WORD_TAG_PREFIX}trPr/{WORD_TAG_PREFIX}tblHeader") is not None


def is_header_row(row: Any, index: int) -> bool:
    """Return whether header row."""
    return index == 0 or _repeats_header(row)


def is_in_table_start_block(index: int, last_header_index: int, row_count: int) -> bool:
    """Return whether in table start block."""
    first_data_index = last_header_index + 1
    return first_data_index + 2 < row_count and first_data_index <= index < first_data_index + 2


def keep_row_paragraphs_together(row: Any) -> None:
    """Chain every XML paragraph in a row, including merged-cell paragraphs."""
    for paragraph in row._tr.iter(f"{WORD_TAG_PREFIX}p"):
        properties = paragraph.get_or_add_pPr()
        if properties.find(f"{WORD_TAG_PREFIX}keepNext") is None:
            properties.append(properties.makeelement(f"{WORD_TAG_PREFIX}keepNext", {}))
