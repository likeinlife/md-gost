"""Границы внешних подписей при стандартном сохранении рисунка."""

from io import BytesIO
from itertools import repeat

import pytest
from matplotlib.figure import Figure
from PIL import Image, ImageChops

from idef0 import Arrow, Block, Context, Decomposition, draw
from tests.support import ensure

_LINE_COUNT = 16
_LONG = "\n".join(repeat("Согласованные требования", _LINE_COUNT))
_RED = "red"
_TOLERANCE_PX = 2


def _cascade() -> Decomposition:
    diagram = Decomposition()
    diagram.step("A1", "Анализ")
    diagram.step("A2", "Разработка", from_previous="Задание")
    diagram.input(_LONG, to="A1", text_color=_RED)
    diagram.output("Широкоформатный чертёж", source="A2", text_color=_RED)
    diagram.control(_LONG, text_color=_RED)
    return diagram


def _context() -> Context:
    control = Arrow(_LONG, text_color=_RED)
    return Context(Block("A0", "Работа"), "", "", control, "")


def _red_extent(figure: Figure, *, tight: bool) -> tuple[int, int]:
    with BytesIO() as stream:
        figure.savefig(stream, format="png", bbox_inches="tight" if tight else None)
        stream.seek(0)
        with Image.open(stream) as raster:
            mask = ImageChops.subtract(raster.getchannel("R"), raster.getchannel("G"))
            bounds = mask.getbbox()
    if bounds is None:
        pytest.fail("В PNG отсутствуют цветные подписи")
    return mask.crop(bounds).size


@pytest.mark.parametrize("diagram", [_context(), _cascade()])
@pytest.mark.parametrize("style", [None, "report"])
def test_savefig_contains_all_labels(diagram: Context | Decomposition, style: str | None) -> None:
    """Обычный PNG показывает надписи целиком, как экспорт по границам объектов."""
    figure = draw(diagram, style=style)
    plain = _red_extent(figure, tight=False)
    cropped = _red_extent(figure, tight=True)
    ensure(condition=plain == pytest.approx(cropped, abs=_TOLERANCE_PX))
    for point in figure.get_tightbbox().get_points():
        ensure(condition=figure.bbox_inches.contains(*point))
