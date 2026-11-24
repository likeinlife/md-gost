"""Define formula and bibliography paragraph styles."""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from gost_builder.reference import constants
from gost_builder.reference.formatting import make_para_style


def apply_formula_styles(styles: object, normal: object) -> None:
    """Apply formula styles."""
    _formula(styles, normal)
    _formula_number(styles, normal)
    _explanation(styles, normal)
    _bibliography(styles, normal)


def _formula(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTFormula",
        normal,
        size=constants.BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=0,
        space_after=0,
        italic=False,
    )


def _formula_number(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTFormulaNumber",
        normal,
        size=constants.BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=0,
        space_after=0,
        italic=False,
    )


def _explanation(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTExplanation",
        normal,
        size=constants.BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(0),
        space_before=0,
        space_after=0,
        italic=False,
    )


def _bibliography(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTBibliography",
        normal,
        size=constants.BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        spacing=constants.BODY_LINE_SPACING,
        first_indent=Cm(constants.FIRST_LINE_INDENT_CM),
        space_before=0,
        space_after=0,
        italic=False,
    )
