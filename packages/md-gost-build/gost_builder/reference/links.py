"""Keep Word hyperlink text black, including after the link is followed."""

from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

from gost_builder.reference import constants
from gost_builder.reference.formatting import find_style

_THEME_COLOR_ATTRS = ("w:themeColor", "w:themeShade", "w:themeTint")


def apply_link_styles(styles: constants.Style) -> None:
    """Ссылка остаётся чёрной и до перехода, и после него."""
    hyperlink = find_style(styles, "Hyperlink")
    if hyperlink is not None:
        _pin_black(hyperlink)
    _pin_black(_followed_link(styles, hyperlink))


def _followed_link(styles: constants.Style, hyperlink: constants.Style | None) -> constants.Style:
    """Стиль посещённой ссылки: без него Word красит переход в фиолетовый."""
    followed = find_style(styles, "FollowedHyperlink")
    if followed is not None:
        return followed
    followed = styles.add_style("FollowedHyperlink", WD_STYLE_TYPE.CHARACTER, builtin=True)
    if hyperlink is not None:
        followed.base_style = hyperlink.base_style
    return followed


def _pin_black(style: constants.Style) -> None:
    """Явный чёрный без цвета темы: themeColor в Word перекрывает w:val."""
    properties = style.element.get_or_add_rPr()
    color = properties.find(qn("w:color"))
    if color is None:
        color = properties.makeelement(qn("w:color"), {})
        properties.append(color)
    color.set(qn("w:val"), "000000")
    for attr in _THEME_COLOR_ATTRS:
        color.attrib.pop(qn(attr), None)
