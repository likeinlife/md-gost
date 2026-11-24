"""Проверки публичного построения рисунков и профиля отчёта."""

from itertools import pairwise

import pytest
from matplotlib import rc_context, rcParams
from matplotlib.figure import Figure

from idef0 import Block, Context, Decomposition, Layout, Waterfall, draw
from tests.support import ensure

_REPORT_SIZE = 13
_CUSTOM_SIZE = 17


def _context() -> Context:
    return Context(Block("A0", "Работа"), "Заявка", "Отчёт", "План", "Команда")


def _title_size(figure: Figure) -> float | str:
    return next(
        label.get_fontsize() for label in figure.axes[0].texts if label.get_text() == "Работа"
    )


def test_report_style_is_scoped() -> None:
    """Профиль подбирает шрифт для рисунка и сохраняет внешние настройки."""
    with rc_context({"font.family": ["monospace"]}):
        figure = draw(_context(), style="report")
        labels = figure.axes[0].texts
        names = labels[0].get_fontfamily()
        ensure(condition=names != ["monospace"])
        ensure(condition=rcParams["font.family"] == ["monospace"])
    ensure(condition=_title_size(figure) == _REPORT_SIZE)


def test_explicit_layout_with_report() -> None:
    """Переданная раскладка задаёт размер шрифта при выбранном профиле."""
    figure = draw(_context(), Layout(title_font_size=_CUSTOM_SIZE), style="report")
    ensure(condition=_title_size(figure) == _CUSTOM_SIZE)


def test_unknown_style() -> None:
    """Опечатка в имени профиля диагностируется до построения рисунка."""
    with pytest.raises(ValueError, match="Неизвестный профиль"):
        draw(_context(), style="missing")


def test_draws_both_cascade_forms() -> None:
    """Компактная форма и пошаговое описание дают одинаковые подписи."""
    blocks = [Block("A1", "Ввод"), Block("A2", "Вывод")]
    compact = Waterfall(blocks=blocks, chain=["Данные"])
    steps = Decomposition()
    steps.step("A1", "Ввод")
    steps.step("A2", "Вывод", from_previous="Данные")
    first = [label.get_text() for label in draw(compact).axes[0].texts]
    second = [label.get_text() for label in draw(steps).axes[0].texts]
    ensure(condition=first == second)


def test_custom_block_limit() -> None:
    """Расширенная раскладка разрешает каскад с дополнительным блоком."""
    count = Layout().max_blocks + 1
    codes = map(str, range(count))
    blocks = [Block(code, code) for code in codes]
    diagram = Waterfall(blocks=blocks, chain=["Данные" for _ in pairwise(blocks)])
    figure = draw(diagram, Layout(max_blocks=count))
    ensure(condition=len(figure.axes[0].patches) >= count)
