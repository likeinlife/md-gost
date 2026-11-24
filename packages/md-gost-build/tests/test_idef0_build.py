"""Build a document containing IDEF0 models and an ordinary plot."""

import zipfile
from pathlib import Path

import pytest
from conftest import WorkFactory, needs_pandoc

pytestmark = [needs_pandoc, pytest.mark.build]
IMAGE_COUNT = 3

CONTEXT_AND_PLOT = """# Проверка

Контекст представлен на рисунке [@fig:context], каскад — на рисунке [@fig:cascade],
а график — на рисунке [@fig:plot].

```{.plot #fig:context caption="Контекст"}
diagram = idef0.Context(idef0.Block("A0", "Работа"), "Вход", "Выход", "Управление", "Ресурс")
```

![Каскад](cascade.py){#fig:cascade}

```{.plot #fig:plot caption="График"}
fig, ax = plt.subplots()
ax.plot([1, 2], [2, 3])
```
"""
CASCADE = """diagram = idef0.Waterfall(
    blocks=(idef0.Block("A1", "Анализ"), idef0.Block("A2", "Передача")),
    chain=["Данные"],
    inputs={"A1": "Заявка"}, outputs={"A2": "Результат"},
    controls="Правила", mechanisms="Команда",
)
"""


def test_idef0_and_plot_in_docx(work: WorkFactory, tmp_path: Path) -> None:
    """Render inline and file-based models alongside a Matplotlib figure."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    (tmp_path / "cascade.py").write_text(CASCADE, encoding="utf-8")
    completed, directory = work(CONTEXT_AND_PLOT)
    assert completed.returncode == 0, completed.stderr
    with zipfile.ZipFile(directory / "out.docx") as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        document = archive.read("word/document.xml").decode("utf-8")
    assert len(media) == IMAGE_COUNT
    assert all(f"Рисунок {number}" in document for number in (1, 2, 3))
