"""Build numbered figures from inline and file-based IDEF0 descriptions."""

import zipfile
from pathlib import Path

import pytest
from conftest import WorkFactory, needs_pandoc
from test_helpers import ENCODING, MANIFEST

pytestmark = [needs_pandoc, pytest.mark.build]
IMAGE_COUNT = 2

CHAPTER = """# Описание

Модель приведена на рисунках [@fig:context] и [@fig:chain].

```{.idef0 #fig:context caption="Контекст"}
context A0 [fill=#eef4ff text_color=#123] : Выпустить систему
input [color=#432 text_color=#753] : Заявка
output : Система
```

Контекст задаёт границы работ.

![Декомпозиция](chain.idef0){#fig:chain}

Разработчики возвращают замечания аналитикам через управляющую стрелку.
"""
CHAIN = """block A1 [color=#628] : Анализ
block A2 : Разработка
A1 -> A2 [color=#047] : Требования
A2 -> A1.control [color=#d52 text_color=#836] : Замечания
"""

SVG_COLORS = (
    (b"#eef4ff", b"#112233", b"#443322", b"#775533"),
    (b"#662288", b"#004477", b"#dd5522", b"#883366"),
)


def test_text_figures_in_docx(work: WorkFactory, tmp_path: Path) -> None:
    """Render both text inputs and resolve their numbered captions."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    (tmp_path / "chain.idef0").write_text(CHAIN, encoding=ENCODING)
    completed, directory = work(CHAPTER, lint=True)
    assert completed.returncode == 0, completed.stderr
    with zipfile.ZipFile(directory / "out.docx") as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        document = archive.read("word/document.xml").decode(ENCODING)
    assert len(media) == IMAGE_COUNT
    assert all(f"Рисунок {number}" in document for number in (1, 2))


def test_text_colors_in_embedded_svg(work: WorkFactory, tmp_path: Path) -> None:
    """Check actual colors of both SVGs embedded in the Word document."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    (tmp_path / "chain.idef0").write_text(CHAIN, encoding=ENCODING)
    completed, directory = work(CHAPTER, manifest=f"{MANIFEST}prefer_vector = true\n")
    assert completed.returncode == 0, completed.stderr
    figures = _embedded_svg(directory)
    assert len(figures) == IMAGE_COUNT
    for palette in SVG_COLORS:
        assert any(all(color in svg for color in palette) for svg in figures)


def _embedded_svg(directory: Path) -> list[bytes]:
    with zipfile.ZipFile(directory / "out.docx") as archive:
        names = [name for name in archive.namelist() if name.endswith(".svg")]
        return [archive.read(name) for name in names]


def test_invalid_text_stops_build(work: WorkFactory, tmp_path: Path) -> None:
    """Propagate the source filename and DSL line number from the renderer."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    (tmp_path / "chain.idef0").write_text(f"{CHAIN}input -> A9 : Заявка", encoding=ENCODING)
    completed, _ = work(CHAPTER)
    assert completed.returncode != 0
    assert "chain.idef0: IDEF0, строка 5:" in completed.stderr
