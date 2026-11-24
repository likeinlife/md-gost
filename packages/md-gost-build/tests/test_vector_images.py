"""Exercise both generated formats and embedded SVG through the whole build."""

import zipfile
from pathlib import Path

import pytest
from conftest import WorkFactory, needs_pandoc
from test_helpers import MANIFEST

from gost_builder.errors import BuildError
from gost_builder.plantuml_cmd import resolve_plantuml

pytestmark = [needs_pandoc, pytest.mark.build]


def _plantuml_missing() -> bool:
    try:
        resolve_plantuml()
    except BuildError:
        return True
    return False


@pytest.mark.skipif(_plantuml_missing(), reason="plantuml не найден в PATH")
@pytest.mark.parametrize("vector", [False, True])
def test_generated_images_follow_manifest(work: WorkFactory, *, vector: bool) -> None:
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    completed, directory = work(PLOT_AND_DIAGRAM, manifest=_manifest(vector=vector))
    assert completed.returncode == 0, completed.stderr
    _assert_generated_images(directory, vector=vector)


PLOT_AND_DIAGRAM = """# Рисунки

На рисунках [@fig:diagram] и [@fig:plot] показаны данные.

```{.plantuml #fig:diagram caption="Схема"}
Alice -> Bob: hello
```

```{.plot #fig:plot caption="График"}
fig, ax = plt.subplots()
sns.barplot(x=[1, 2], y=[3, 4], ax=ax)
```
"""


def _manifest(*, vector: bool) -> str:
    setting = str(vector).lower()
    return f"{MANIFEST}prefer_vector = {setting}\n"


def _assert_generated_images(directory: Path, *, vector: bool) -> None:
    extension = "svg" if vector else "png"
    for stem in ("diagram_01", "plot_02"):
        assert (directory / ".md-to-gost" / "img" / f"{stem}.{extension}").is_file()
    with zipfile.ZipFile(directory / "out.docx") as archive:
        expected = 2 if vector else 0
        assert sum(name.endswith(".svg") for name in archive.namelist()) == expected
        document = archive.read("word/document.xml").decode("utf-8")
        assert ("svgBlip" in document) is vector
        assert "Рисунок 1" in document
        assert "Рисунок 2" in document


def test_existing_svg_is_numbered(work: WorkFactory, tmp_path: Path) -> None:
    (tmp_path / "figure.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
        '<rect width="100" height="50" fill="red"/></svg>',
        encoding="utf-8",
    )
    completed, directory = work(
        "# Тест\n\nНа рисунке [@fig:test].\n\n![Схема](figure.svg){#fig:test}\n",
    )
    assert completed.returncode == 0, completed.stderr
    with zipfile.ZipFile(directory / "out.docx") as archive:
        assert any(name.endswith(".svg") for name in archive.namelist())
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Рисунок 1" in document
        assert "svgBlip" in document
