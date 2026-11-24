"""Цветовые атрибуты в текстовых блоках IDEF0 и сообщения о некорректной записи."""

import pytest

from idef0._models import Block, Context
from idef0.arrows import Arrow
from idef0.colors import PALETTE
from idef0.decomposition import Decomposition
from idef0.errors import ModelError
from idef0.text import parse_text
from tests.support import ensure

_CONTEXT = """context A0 [color=BLUE fill=#EeF text_color=#123] : Работа [color=лишний]: пример
input [text_color=red] : Заявка
output [text_color=red] : Система
control [text_color=red] : Бюджет
mechanism [text_color=red] : Команда
"""
_ATTRIBUTES = "[color=purple text_color=#AbC]"
_CHAIN = f"""block A1 [fill=#def] : Анализ
block A2 : Исполнение
A1 -> A2 {_ATTRIBUTES} : Требования
input -> A1 {_ATTRIBUTES} : Заявка
A2 -> output {_ATTRIBUTES} : Система
control -> * {_ATTRIBUTES} : План
mechanism -> * {_ATTRIBUTES} : Группа
control -> A1,A2 {_ATTRIBUTES} : Бюджет
mechanism -> A2 {_ATTRIBUTES} : Команда
A2 -> A1.input {_ATTRIBUTES} : Вопрос
A2 -> A1.control {_ATTRIBUTES} : Замечания
"""
_RED = PALETTE["red"]
_PURPLE = PALETTE["purple"]
_TEXT = "#aabbcc"


def test_context_arrow_and_block_colors() -> None:
    """Окрасить все роли контекста и сохранить квадратные скобки в подписи."""
    diagram = parse_text(_CONTEXT)
    if not isinstance(diagram, Context):
        pytest.fail("Ожидался контекст")
    expected = Block(
        "A0",
        "Работа [color=лишний]: пример",
        fill="#eeeeff",
        color=PALETTE["blue"],
        text_color="#112233",
    )
    ensure(condition=diagram.block == expected)
    ensure(condition=diagram.inputs == [Arrow("Заявка", text_color=_RED)])
    ensure(condition=diagram.outputs == [Arrow("Система", text_color=_RED)])
    ensure(condition=diagram.controls == [Arrow("Бюджет", text_color=_RED)])
    ensure(condition=diagram.mechanisms == [Arrow("Команда", text_color=_RED)])


def test_colors_reach_all_cascade_arrows() -> None:
    """Передать цвета индивидуальных стрелок, общих шин, групп и обратных связей."""
    diagram = parse_text(_CHAIN)
    if not isinstance(diagram, Decomposition):
        pytest.fail("Ожидалась декомпозиция")
    model = diagram.to_model()
    ensure(condition=model.blocks[0].fill == "#ddeeff")
    ensure(condition=model.controls_color == model.mechanisms_color == _PURPLE)
    ensure(condition=model.controls_text_color == model.mechanisms_text_color == _TEXT)
    arrows = (
        *model.flows,
        *model.inputs,
        *model.outputs,
        *model.control_groups,
        *model.mechanisms_by_block,
        *model.input_links,
        *model.control_links,
    )
    for arrow in arrows:
        ensure(condition=arrow.color == _PURPLE)
        ensure(condition=arrow.text_color == _TEXT)


@pytest.mark.parametrize(
    ("attributes", "diagnostic"),
    [
        ("[color]", "имя=цвет"),
        ("[color=red color=blue]", "дважды"),
        ("[width=green]", "неизвестный атрибут"),
        ("[fill=red]", "заливку блока"),
        ("[color=#x11]", "Неизвестный цвет"),
        ("[text_color=purple", "атрибутами"),
    ],
)
def test_invalid_color_reports_line(attributes: str, diagnostic: str) -> None:
    """Показать ошибочное поле и исходную строку."""
    source = f"context A0 : Описание\n\noutput {attributes} : Чертёж"
    with pytest.raises(ModelError, match=rf"строка 3: .*{diagnostic}"):
        parse_text(source)
