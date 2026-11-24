"""Границы названий и кодов на экранных и печатных рисунках."""

import pytest
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

from idef0 import Block, Context, Layout, Waterfall, draw
from tests.support import ensure

_LONG_TERM = "СверхдлинноеСловоБезПробеловДляПроверкиРазмещения"
_MANUAL = "Первая строка\nВторая строка"
_PRINT_DPI = 300


def _bounds(ax: Axes, label: str) -> Bbox:
    wanted = "".join(label.split())
    for artist in ax.texts:
        if "".join(artist.get_text().split()) == wanted:
            return artist.get_window_extent()
    pytest.fail(f"Пропала подпись {label!r}")


def _check_block(ax: Axes, index: int, block: Block) -> None:
    rectangle = ax.patches[index].get_window_extent()
    title = _bounds(ax, block.title)
    code = _bounds(ax, block.code)
    for box in (title, code):
        ensure(condition=rectangle.contains(box.x0, box.y0))
        ensure(condition=rectangle.contains(box.x1, box.y1))
    ensure(condition=not title.overlaps(code))


def _check(figure: Figure, blocks: list[Block], dpi: int) -> None:
    figure.set_dpi(dpi)
    FigureCanvasAgg(figure).draw()
    for index, block in enumerate(blocks):
        _check_block(figure.axes[0], index, block)


@pytest.mark.parametrize("style", [None, "report"])
@pytest.mark.parametrize("dpi", [100, _PRINT_DPI])
def test_automatic_breaks(style: str | None, dpi: int) -> None:
    """Обе подписи и длинное слово в каскаде остаются внутри своих блоков."""
    blocks = [Block("A1", "Подготовить проект"), Block("A2", "Проверить проект")]
    diagram = Waterfall(blocks=blocks, chain=["Запрос"])
    _check(draw(diagram, style=style), blocks, dpi)
    blocks = [Block("A1", _LONG_TERM), Block("A2", _MANUAL)]
    diagram = Waterfall(blocks=blocks, chain=["Запрос"])
    figure = draw(diagram, style=style)
    _check(figure, blocks, dpi)
    labels = {label.get_text() for label in figure.axes[0].texts}
    ensure(condition=_MANUAL in labels)


@pytest.mark.parametrize("ratio", [0, 1])
def test_long_context_and_code(ratio: float) -> None:
    """Длинный код и заголовок разделяются даже при смещённой точке привязки."""
    block = Block("Участок-подготовки-A153", f"Анализ документов и {_LONG_TERM}")
    context = Context(block, "Данные", "Отчёт", "Правила", "Команда")
    layout = Layout(title_y_ratio=ratio, context_block_width=1)
    _check(draw(context, layout), [block], _PRINT_DPI)
