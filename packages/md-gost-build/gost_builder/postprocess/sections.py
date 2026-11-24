"""Turn Pandoc's page format markers into next-page Word sections."""

from types import MappingProxyType

from docx.document import Document as DocxDocument
from docx.enum.section import WD_ORIENT, WD_SECTION_START
from docx.oxml.ns import qn
from docx.oxml.text.paragraph import CT_P
from docx.section import Section
from docx.shared import Mm, Pt
from docx.text.paragraph import Paragraph

from gost_builder.postprocess.page_breaks import format_heading_pages
from gost_builder.postprocess.page_numbers import use_appendix_header

PageFormat = tuple[WD_ORIENT, int, int, str]
A4_SHORT_MM = 210
SHARED_SIDE_MM = 297
A3_LONG_MM = 420
BODY_MARKER = "GOSTSectionBody"
BODY_FORMAT = (WD_ORIENT.PORTRAIT, A4_SHORT_MM, SHARED_SIDE_MM, "9")
PAGE_FORMATS = MappingProxyType(
    {
        "GOSTSectionA4Portrait": BODY_FORMAT,
        "GOSTSectionA4Landscape": (WD_ORIENT.LANDSCAPE, SHARED_SIDE_MM, A4_SHORT_MM, "9"),
        "GOSTSectionA3Portrait": (WD_ORIENT.PORTRAIT, SHARED_SIDE_MM, A3_LONG_MM, "8"),
        "GOSTSectionA3Landscape": (WD_ORIENT.LANDSCAPE, A3_LONG_MM, SHARED_SIDE_MM, "8"),
    },
)


def format_sections(doc: DocxDocument, *, page_break: bool) -> None:
    """Format sections."""
    format_heading_pages(doc, page_break=page_break)
    for marker in doc.paragraphs:
        style = marker._p.style
        page_format = PAGE_FORMATS.get(style or "")
        if page_format is not None:
            section = _start_section(doc, marker)
            _set_page_format(section, page_format)
            use_appendix_header(doc, section)
        elif style == BODY_MARKER:
            _set_page_format(_start_section(doc, marker), BODY_FORMAT)


def _set_page_format(section: Section, page_format: PageFormat) -> None:
    orientation, width, height, paper_code = page_format
    section.orientation = orientation
    section.page_width = Mm(width)
    section.page_height = Mm(height)
    section._sectPr.get_or_add_pgSz().set(qn("w:code"), paper_code)


def _start_section(doc: DocxDocument, marker: Paragraph) -> Section:
    previous = marker._p.getprevious()
    # Pandoc wraps sections in bookmark nodes beside the heading paragraph.
    heading = next(marker._p.itersiblings(tag=qn("w:p")), None)
    if isinstance(heading, CT_P):
        Paragraph(heading, doc).paragraph_format.page_break_before = False
    if previous is None:
        doc._element.body.remove(marker._p)
        return doc.sections[-1]

    section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    boundary = doc.paragraphs[-1]
    _move_section_break(boundary, previous, marker)
    doc._element.body.remove(marker._p)
    section.different_first_page_header_footer = False
    numbering = section._sectPr.find(qn("w:pgNumType"))
    if numbering is not None:
        numbering.attrib.pop(qn("w:start"), None)
    return section


def _move_section_break(boundary: Paragraph, previous: object, marker: Paragraph) -> None:
    if isinstance(previous, CT_P):
        previous.set_sectPr(boundary._p.xpath("w:pPr/w:sectPr")[0])
        body = boundary._p.getparent()
        body.remove(boundary._p)
    else:
        marker._p.addprevious(boundary._p)
        formatting = boundary.paragraph_format
        formatting.space_before = Pt(0)
        formatting.space_after = Pt(0)
        formatting.line_spacing = Pt(1)
