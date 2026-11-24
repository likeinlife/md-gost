"""Set borders, alignment, and automatic sizing for Word tables."""

from docx.table import Table

from gost_builder.ooxml import WORD_TAG_PREFIX


def table_borders(table: Table) -> None:
    """Handle table borders."""
    borders = table._tbl.tblPr.find(f"{WORD_TAG_PREFIX}tblBorders")
    if borders is None:
        borders = table._tbl.tblPr.makeelement(f"{WORD_TAG_PREFIX}tblBorders", {})
        table._tbl.tblPr.append(borders)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(f"{WORD_TAG_PREFIX}{side}")
        if element is None:
            element = borders.makeelement(f"{WORD_TAG_PREFIX}{side}", {})
            borders.append(element)
        element.set(f"{WORD_TAG_PREFIX}val", "single")
        element.set(f"{WORD_TAG_PREFIX}sz", "4")
        element.set(f"{WORD_TAG_PREFIX}space", "0")
        element.set(f"{WORD_TAG_PREFIX}color", "000000")


def autofit_table(table: Table) -> None:
    """Handle autofit table."""
    properties = table._tbl.tblPr
    table.autofit = True
    width = properties.find(f"{WORD_TAG_PREFIX}tblW")
    if width is None:
        width = properties.makeelement(f"{WORD_TAG_PREFIX}tblW", {})
        properties.append(width)
    width.set(f"{WORD_TAG_PREFIX}w", "5000")
    width.set(f"{WORD_TAG_PREFIX}type", "pct")
    layout = properties.find(f"{WORD_TAG_PREFIX}tblLayout")
    if layout is not None:
        layout.set(f"{WORD_TAG_PREFIX}type", "autofit")
    for row in table.rows:
        for cell in row.cells:
            properties = cell._tc.get_or_add_tcPr()
            width = properties.find(f"{WORD_TAG_PREFIX}tcW")
            if width is not None:
                width.set(f"{WORD_TAG_PREFIX}w", "0")
                width.set(f"{WORD_TAG_PREFIX}type", "auto")


def center_table(table: Table) -> None:
    """Handle center table."""
    properties = table._tbl.tblPr
    alignment = properties.find(f"{WORD_TAG_PREFIX}jc")
    if alignment is None:
        alignment = properties.makeelement(f"{WORD_TAG_PREFIX}jc", {})
        properties.append(alignment)
    alignment.set(f"{WORD_TAG_PREFIX}val", "center")
