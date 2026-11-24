"""Build image fixtures and inspect their rendered document XML."""

import zipfile
from pathlib import Path

from image_geometry_helpers import (
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    _assert_image_aspect,
    _assert_image_page_fit,
)
from png_helpers import make_png
from test_helpers import ENCODING, MANIFEST, Run, build


def build_large_image(tmp_path: Path) -> Run:
    image_dir = tmp_path / "img"
    image_dir.mkdir()
    make_png(image_dir / "tall.png", IMAGE_WIDTH, IMAGE_HEIGHT)
    chapter = "# Глава 1. Рисунок\n\n![Высокая схема](img/tall.png){#fig:tall}\n\nтекст.\n"
    (tmp_path / "CHAPTER_1.md").write_text(chapter, encoding=ENCODING)
    (tmp_path / "book.toml").write_text(MANIFEST, encoding=ENCODING)
    return build(tmp_path)


def assert_large_image_fits(tmp_path: Path) -> None:
    document = zipfile.ZipFile(tmp_path / "out.docx").read("word/document.xml").decode(ENCODING)
    _assert_image_page_fit(document)
    _assert_image_aspect(document)
