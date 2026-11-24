"""Define the GOST caption styles."""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from gost_builder.reference import constants
from gost_builder.reference.formatting import make_para_style


def apply_caption_styles(styles: object, normal: object) -> None:
    """Apply caption styles."""
    _image_caption(styles, normal)
    _table_caption(styles, normal)
    _listing_caption(styles, normal)


def _image_caption(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTImageCaption",
        normal,
        size=constants.CAPTION_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=6,
        space_after=6,
        italic=False,
    )


def _table_caption(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTTableCaption",
        normal,
        size=constants.CAPTION_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=6,
        space_after=6,
        italic=False,
    )


def _listing_caption(styles: object, normal: object) -> None:
    make_para_style(
        styles,
        "GOSTListingCaption",
        normal,
        size=constants.CAPTION_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        spacing=1.0,
        first_indent=Cm(0),
        space_before=6,
        space_after=6,
        italic=False,
    )
