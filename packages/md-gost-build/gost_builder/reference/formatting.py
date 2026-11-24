"""Reusable style and paragraph formatting helpers."""

from typing import Any

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from gost_builder.reference import constants

Style = constants.Style
Element = constants.Element


def force_tnr(element: Element) -> Element:
    """Pin every font slot of a style element to TNR, dropping theme bindings."""
    rpr = element.get_or_add_rPr()
    _set_font_slots(rpr, constants.FONT)
    return rpr


def _set_font_slots(rpr: Element, font_name: str) -> None:
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), font_name)


def set_font(style: Style, size: int, **options: Any) -> None:
    """Set font."""
    font = style.font
    font.name = constants.FONT
    font.size = Pt(size)
    font.bold = options.get("bold", False)
    color = options.get("color")
    if color is not None:
        font.color.rgb = RGBColor(*color)
    force_tnr(style.element)


def set_code_font(style: Style) -> None:
    """Моноширинный чёрный шрифт листинга, без привязки к шрифту темы."""
    style.font.name = constants.CODE_FONT
    style.font.size = Pt(constants.CODE_SIZE)
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    _set_font_slots(rpr, constants.CODE_FONT)


def set_para(style: Style, **options: Any) -> None:
    """Set para."""
    formatting = style.paragraph_format
    alignment = options.get("align")
    if alignment is not None:
        formatting.alignment = alignment
    formatting.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    formatting.line_spacing = options.get("spacing", constants.BODY_LINE_SPACING)
    formatting.space_before = Pt(options.get("space_before", 0))
    formatting.space_after = Pt(options.get("space_after", 0))
    first_indent = options.get("first_indent")
    if first_indent is not None:
        formatting.first_line_indent = first_indent


def make_para_style(styles: Style, name: str, base: Style, **options: Any) -> Style:
    """Define a custom GOST paragraph style visible in Word's Styles pane."""
    st = find_style(styles, name)
    if st is None:
        st = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = base
    set_font(st, options["size"], bold=options.get("bold", False))
    if options.get("italic") is not None:
        st.font.italic = options["italic"]
    set_para(
        st,
        align=options["align"],
        spacing=options["spacing"],
        first_indent=options["first_indent"],
        space_before=options["space_before"],
        space_after=options["space_after"],
    )
    # Without qFormat + a UI priority Word hides custom styles from the gallery.
    st.quick_style = True
    st.hidden = False
    st.unhide_when_used = True
    st.priority = 10
    el = st.element
    semi = el.find(qn("w:semiHidden"))
    if semi is not None:
        el.remove(semi)
    if el.find(qn("w:qFormat")) is None:
        el.append(el.makeelement(qn("w:qFormat"), {}))
    return st


def find_style(styles: Style, name: str) -> Style | None:
    """Find style."""
    return next((style for style in styles if style.name == name), None)
