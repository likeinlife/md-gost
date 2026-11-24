"""Formatting passes for borderless formula tables."""

from typing import Any

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table

from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.styles import style_name
from gost_builder.postprocess.tables.cells import vertical_center
from gost_builder.postprocess.tables.kinds import EXPLANATION_STYLE, is_formula_table

Element = Any


def _formula_cell_margins(properties: Element) -> None:
    margins = properties.find(f"{WORD_TAG_PREFIX}tblCellMar")
    if margins is None:
        margins = properties.makeelement(f"{WORD_TAG_PREFIX}tblCellMar", {})
        properties.append(margins)
    for side in ("left", "right"):
        margin = margins.find(f"{WORD_TAG_PREFIX}{side}")
        if margin is None:
            margin = margins.makeelement(f"{WORD_TAG_PREFIX}{side}", {})
            margins.append(margin)
        margin.set(f"{WORD_TAG_PREFIX}w", "0")
        margin.set(f"{WORD_TAG_PREFIX}type", "dxa")


def _formula_borders(properties: Element) -> None:
    borders = properties.find(f"{WORD_TAG_PREFIX}tblBorders")
    if borders is None:
        borders = properties.makeelement(f"{WORD_TAG_PREFIX}tblBorders", {})
        properties.append(borders)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = borders.find(f"{WORD_TAG_PREFIX}{side}")
        if border is None:
            border = borders.makeelement(f"{WORD_TAG_PREFIX}{side}", {})
            borders.append(border)
        border.set(f"{WORD_TAG_PREFIX}val", "none")
        border.set(f"{WORD_TAG_PREFIX}sz", "0")
        border.set(f"{WORD_TAG_PREFIX}space", "0")


def format_formula_tables(doc: DocxDocument) -> None:
    """Set invisible borders and layout for formula tables."""
    for table in doc.tables:
        if is_formula_table(table):
            _format_formula_table(table)


def _center_formula_row(table: Table) -> None:
    row = table.rows[0]
    properties = row._tr.get_or_add_trPr()
    if properties.find(f"{WORD_TAG_PREFIX}cantSplit") is None:
        properties.append(properties.makeelement(f"{WORD_TAG_PREFIX}cantSplit", {}))
    for cell in row.cells:
        vertical_center(cell)
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_with_next = True


def _format_formula_table(table: Table) -> None:
    properties = table._tbl.tblPr
    _formula_borders(properties)
    _formula_cell_margins(properties)
    _justify_explanations(table)
    _center_formula_row(table)


def _justify_explanations(table: Table) -> None:
    for row in table.rows[1:]:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                if style_name(paragraph) == EXPLANATION_STYLE:
                    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
