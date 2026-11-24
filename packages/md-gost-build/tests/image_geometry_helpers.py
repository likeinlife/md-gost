"""Check image extents and page dimensions in rendered Word XML."""

import re

ASPECT_RATIO_TOLERANCE = 0.01

IMAGE_WIDTH = 700

IMAGE_HEIGHT = 4000

TWIPS_TO_EMU = 635


def _assert_image_page_fit(document: str) -> None:
    cx, cy = _image_extent(document)
    max_width, max_height = _text_area(document)
    assert cx <= max_width
    assert cy <= max_height


def _assert_image_aspect(document: str) -> None:
    width, height = _image_extent(document)
    aspect_ratio = width / height
    assert abs(aspect_ratio - IMAGE_WIDTH / IMAGE_HEIGHT) < ASPECT_RATIO_TOLERANCE


def _image_extent(document: str) -> tuple[int, int]:
    extent = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', document)
    assert extent is not None, "рисунка нет в выходном документе"
    return int(extent.group(1)), int(extent.group(2))


def _text_area(document: str) -> tuple[int, int]:
    page_size = _page_attributes(document, r"<w:pgSz\b[^>]*>")
    page_margins = _page_attributes(document, r"<w:pgMar\b[^>]*>")
    width = _available_width(page_size, page_margins)
    height = _available_height(page_size, page_margins)
    return width * TWIPS_TO_EMU, height * TWIPS_TO_EMU


def _page_attributes(document: str, pattern: str) -> dict[str, int]:
    match = re.search(pattern, document)
    assert match is not None, "не найдена геометрия страницы"
    return {
        key: int(attribute_value)
        for key, attribute_value in re.findall(r'w:(\w+)="(\d+)"', match.group(0))
    }


def _available_width(size: dict[str, int], margins: dict[str, int]) -> int:
    return size["w"] - margins["right"] - margins["left"]


def _available_height(size: dict[str, int], margins: dict[str, int]) -> int:
    return size["h"] - margins["top"] - margins["bottom"]
