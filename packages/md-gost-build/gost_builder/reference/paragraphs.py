"""Apply shared body, heading, code, and page settings."""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm

from gost_builder.reference import constants
from gost_builder.reference.formatting import find_style, force_tnr, set_font, set_para

HEADING_STYLES = (
    ("Heading 1", constants.HEADING_FONT_SIZE, constants.HEADING_SPACE_BEFORE_PT, 6),
    ("Heading 2", constants.BODY_FONT_SIZE, constants.HEADING_SPACE_BEFORE_PT, 6),
    ("Heading 3", constants.BODY_FONT_SIZE, 6, 6),
)


def set_body_styles(styles: constants.Style) -> constants.Style:
    """Set body styles."""
    normal = find_style(styles, "Normal")
    if normal is None:
        missing = "Normal"
        raise KeyError(missing)
    set_font(normal, constants.BODY_FONT_SIZE)
    set_para(
        normal,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(constants.FIRST_LINE_INDENT_CM),
        space_before=0,
        space_after=0,
    )
    for name in ("Body Text", "First Paragraph"):
        style = find_style(styles, name)
        if style is not None:
            _format_body_variant(style)
    return normal


def _format_body_variant(style: constants.Style) -> None:
    set_font(style, constants.BODY_FONT_SIZE)
    set_para(
        style,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(constants.FIRST_LINE_INDENT_CM),
        space_before=0,
        space_after=0,
    )


def apply_heading_styles(styles: constants.Style) -> None:
    """Apply heading styles."""
    for name, size, before, after in HEADING_STYLES:
        style = find_style(styles, name)
        if style is not None:
            _format_heading(style, size, before, after)


def _format_heading(style: constants.Style, size: int, before: int, after: int) -> None:
    set_font(style, size, bold=True, color=(0, 0, 0))
    set_para(
        style,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(constants.FIRST_LINE_INDENT_CM),
        space_before=before,
        space_after=after,
    )


def apply_toc_style(styles: constants.Style) -> None:
    """Заголовок «Содержание»: чёрный, жирный, по центру."""
    style = find_style(styles, "TOC Heading")
    if style is not None:
        _format_toc_heading(style)


def _format_toc_heading(style: constants.Style) -> None:
    set_font(style, constants.HEADING_FONT_SIZE, bold=True, color=(0, 0, 0))
    set_para(
        style,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(0),
        space_before=constants.HEADING_SPACE_BEFORE_PT,
        space_after=6,
    )
    properties = force_tnr(style.element)
    _force_bold(properties)
    color = properties.find(qn("w:color"))
    if color is not None:
        for attr in ("w:themeColor", "w:themeShade", "w:themeTint"):
            color.attrib.pop(qn(attr), None)


def _force_bold(properties: constants.Element) -> None:
    """В reference.docx Pandoc у TOC Heading явно выключены и w:b, и w:bCs."""
    for name in ("w:b", "w:bCs"):
        element = properties.find(qn(name))
        if element is None:
            properties.append(properties.makeelement(qn(name), {}))
        else:
            element.attrib.pop(qn("w:val"), None)
