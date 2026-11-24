"""Проверки создания файлов изображений через рендерер документов."""

import importlib
from pathlib import Path
from typing import Protocol, cast

import pytest

from tests.support import ensure


class PlotRenderer(Protocol):
    """Интерфейс рендерера документа."""

    def render(self, source: Path, target: Path) -> None:
        """Создать изображение из Python-файла."""


RENDERER_DIR = Path(__file__).resolve().parents[2] / "md-gost-build" / "lib"
CONTEXT = """diagram = idef0.Context(
    idef0.Block("A0", "Работа"), ["Вход", "Данные"], ["Выход", "Отчёт"],
    ["Правила", "Договор"], ["Ресурсы", "Команда"]
)
"""
WATERFALL = """diagram = idef0.Waterfall(
    blocks=(idef0.Block("A1", "Анализ"), idef0.Block("A2", "Передача")),
    chain=["Данные"], inputs={"A1": "Заявка"}, outputs={"A2": "Результат"},
    controls=[
        idef0.Arrow("Правила"),
        idef0.Arrow("Дополнительный регламент", to="A1"),
        idef0.Arrow("Общее правило", to=("A1", "A2")),
    ],
    mechanisms=[idef0.Arrow("Исполнители"), idef0.Arrow("Специалист", to="A2")],
    links=[
        idef0.Link("A2", "A1", "Предложения", role="input"),
        idef0.Link("A2", "A1", "Замечания", role="control"),
    ],
)
"""
PLOT = "fig, ax = plt.subplots()\nax.plot([1, 2], [2, 3])\n"


@pytest.fixture
def renderer(monkeypatch: pytest.MonkeyPatch) -> PlotRenderer:
    """Загрузить рендерер с его собственными импортами."""
    monkeypatch.syspath_prepend(str(RENDERER_DIR))
    return cast("PlotRenderer", importlib.import_module("render_plot"))


@pytest.mark.parametrize("source_text", [CONTEXT, WATERFALL, PLOT])
@pytest.mark.parametrize("suffix", ["png", "svg"])
def test_render_to_file(
    renderer: PlotRenderer,
    tmp_path: Path,
    source_text: str,
    suffix: str,
) -> None:
    """Контекст, каскад и Matplotlib сохраняются в обоих форматах."""
    source = tmp_path / "diagram.py"
    target = tmp_path / f"output.{suffix}"
    source.write_text(source_text, encoding="utf-8")
    renderer.render(source, target)
    image_bytes = target.read_bytes()
    signature = b"<svg" if suffix == "svg" else b"\x89PNG\r\n\x1a\n"
    ensure(condition=signature in image_bytes)


def test_rejects_ambiguous_result(renderer: PlotRenderer, tmp_path: Path) -> None:
    """Одновременно заданные диаграмма и фигура не выбираются произвольно."""
    source = tmp_path / "diagram.py"
    source.write_text(f"{CONTEXT}fig = plt.figure()\n", encoding="utf-8")
    with pytest.raises(ValueError, match="either diagram"):
        renderer.render(source, tmp_path / "output.png")


@pytest.mark.parametrize("diagram_text", ["42", "None"])
def test_rejects_unknown_diagram(renderer: PlotRenderer, tmp_path: Path, diagram_text: str) -> None:
    """Неподдерживаемое значение не превращается в пустую диаграмму."""
    source = tmp_path / "diagram.py"
    source.write_text(f"diagram = {diagram_text}\n", encoding="utf-8")
    with pytest.raises(TypeError, match=r"idef0\.Context"):
        renderer.render(source, tmp_path / "output.png")
