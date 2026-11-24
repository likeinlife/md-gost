"""Format first-level headings and explicit `.page` breaks."""

import re

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.text.paragraph import CT_P
from docx.shared import Cm
from docx.text.paragraph import Paragraph

from gost_builder.postprocess.styles import style_name

APPENDIX_HEADING = re.compile(r"^Приложение [А-ЯЁ]\n\S", re.IGNORECASE)
PAGE_BREAK_STYLE = "GOSTPageBreak"


def format_heading_pages(doc: DocxDocument, *, page_break: bool) -> None:
    """Appendices and `{.page}` headings start on a new page."""
    _apply_page_markers(doc)
    for paragraph in doc.paragraphs:
        if style_name(paragraph).replace(" ", "") != "Heading1":
            continue
        formatting = paragraph.paragraph_format
        is_appendix = APPENDIX_HEADING.match(paragraph.text) is not None
        if is_appendix or page_break:
            formatting.page_break_before = True
        if is_appendix:
            formatting.alignment = WD_ALIGN_PARAGRAPH.CENTER
            formatting.first_line_indent = Cm(0)
            formatting.space_before = 0


def _apply_page_markers(doc: DocxDocument) -> None:
    for paragraph in list(doc.paragraphs):
        if (paragraph._p.style or "") != PAGE_BREAK_STYLE:
            continue
        target = _next_content_paragraph(doc, paragraph)
        if target is not None:
            target.paragraph_format.page_break_before = True
        parent = paragraph._p.getparent()
        if parent is not None:
            parent.remove(paragraph._p)


def _next_content_paragraph(doc: DocxDocument, marker: Paragraph) -> Paragraph | None:
    sibling = marker._p.getnext()
    while sibling is not None:
        if isinstance(sibling, CT_P) and not _is_layout_marker(sibling.style or ""):
            return Paragraph(sibling, doc)
        sibling = sibling.getnext()
    return None


def _is_layout_marker(style: str) -> bool:
    return style == PAGE_BREAK_STYLE or style.startswith("GOSTSection")
