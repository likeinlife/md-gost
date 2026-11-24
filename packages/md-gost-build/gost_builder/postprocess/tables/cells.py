"""Format the contents and vertical alignment of table cells."""

from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm

from gost_builder.ooxml import WORD_TAG_PREFIX


def format_cell(cell: Any, *, is_header: bool) -> None:
    """Format cell."""
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if is_header:
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
    vertical_center(cell)


def vertical_center(cell: Any) -> None:
    """Handle vertical center."""
    properties = cell._tc.get_or_add_tcPr()
    alignment = properties.find(f"{WORD_TAG_PREFIX}vAlign")
    if alignment is None:
        alignment = properties.makeelement(f"{WORD_TAG_PREFIX}vAlign", {})
        properties.append(alignment)
    alignment.set(f"{WORD_TAG_PREFIX}val", "center")
