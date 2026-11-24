"""Apply code, compact, and page styles to the reference document."""

from docx.document import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Mm

from gost_builder.reference import constants
from gost_builder.reference.formatting import find_style, set_code_font, set_font, set_para


def apply_code_styles(styles: constants.Style) -> None:
    """Apply code styles."""
    code = _get_code_style(styles)
    set_code_font(code)
    set_para(
        code,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=0,
        space_after=0,
    )
    code.quick_style = True
    verbatim = find_style(styles, "Verbatim Char")
    if verbatim is not None:
        set_code_font(verbatim)


def _get_code_style(styles: constants.Style) -> constants.Style:
    code = find_style(styles, "Source Code")
    if code is not None:
        return code
    return styles.add_style("Source Code", WD_STYLE_TYPE.PARAGRAPH)


def apply_compact_styles(styles: constants.Style) -> None:
    """Apply compact styles."""
    for name in ("Table Caption", "Image Caption", "Caption", "Compact"):
        style = find_style(styles, name)
        if style is not None:
            set_font(style, constants.CAPTION_FONT_SIZE)


def set_page_geometry(doc: DocxDocument) -> None:
    """Set page geometry."""
    for section in doc.sections:
        section.page_width = Mm(constants.A4_WIDTH_MM)
        section.page_height = Mm(constants.A4_HEIGHT_MM)
        section.left_margin = Mm(constants.LEFT_MARGIN_MM)
        section.right_margin = Mm(constants.RIGHT_MARGIN_MM)
        section.top_margin = Mm(constants.VERTICAL_MARGIN_MM)
        section.bottom_margin = Mm(constants.VERTICAL_MARGIN_MM)
