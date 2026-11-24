"""Apply GOST paragraph formatting to list items."""

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.text.paragraph import Paragraph

from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.numbering import BODY_FONT_SIZE, set_marker_indent, set_run_font
from gost_builder.postprocess.styles import style_name

FILTER_STYLE_PREFIX = "GOST"


def fix_paragraphs(doc: DocxDocument) -> None:
    """GOST formatting for list items.

    Captions and bibliography entries arrive already styled from the filter and
    are skipped, so this function is the single owner of list formatting.
    """
    for paragraph in doc.paragraphs:
        if _is_list_paragraph(paragraph):
            _format_list_paragraph(paragraph)


def _is_list_paragraph(paragraph: Paragraph) -> bool:
    style = style_name(paragraph)
    if style.startswith(FILTER_STYLE_PREFIX):
        return False
    properties = paragraph._p.find(f"{WORD_TAG_PREFIX}pPr")
    numbered = properties is not None and properties.find(f"{WORD_TAG_PREFIX}numPr") is not None
    return numbered or "List" in style or style == "Compact"


def _format_list_paragraph(paragraph: Paragraph) -> None:
    for run in paragraph.runs:
        set_run_font(run, BODY_FONT_SIZE)
    formatting = paragraph.paragraph_format
    formatting.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    formatting.line_spacing = 1.5
    formatting.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_marker_indent(paragraph._p.get_or_add_pPr())
