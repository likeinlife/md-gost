"""Проверки смыслового разбора диаграммы и координат ошибок в тексте."""

import pytest

from idef0._models import Context, Flow, Group, Port
from idef0.decomposition import Decomposition
from idef0.errors import ModelError
from idef0.text import parse_text
from tests.support import ensure

_FIRST = "A1"
_SECOND = "A2"

_CONTEXT = r"""context A0 : Разработать\nсистему
# Условия заказчика
input : Заявка: срочная
input : Обращение
output : Система
control : Договор
mechanism : Команда
"""
_CHAIN = """block A1 : Описать
block A2 : Сделать
A1 -> A2 : Задание
"""
_PORTS = """input -> A1 : Заявка
A2 -> output : Система
control -> * : Правила
mechanism -> * : Команда
control -> A1,A2 : Договор
mechanism -> A2 : Разработчик
A1 -> A2.input : Образец
A2 -> A1.control : Замечания
"""


def test_context_text() -> None:
    """Сохранить независимые стрелки, перенос и двоеточие в подписи."""
    diagram = parse_text(_CONTEXT)
    if not isinstance(diagram, Context):
        pytest.fail("Ожидалась контекстная диаграмма")
    ensure(condition=diagram.block.title == "Разработать\nсистему")
    ensure(condition=diagram.inputs == ["Заявка: срочная", "Обращение"])
    ensure(condition=diagram.mechanisms == ["Команда"])


def test_decomposition_text() -> None:
    """Различать основную связь, дополнительные связи и адресные внешние стрелки."""
    diagram = parse_text(_CHAIN + _PORTS)
    if not isinstance(diagram, Decomposition):
        pytest.fail("Ожидалась декомпозиция")
    model = diagram.to_model()
    ensure(condition=model.flows == (Flow(_FIRST, _SECOND, "Задание"),))
    ensure(condition=model.input_links == (Flow(_FIRST, _SECOND, "Образец"),))
    ensure(condition=model.control_links == (Flow(_SECOND, _FIRST, "Замечания"),))
    ensure(condition=model.control_groups == (Group((_FIRST, _SECOND), "Договор"),))
    ensure(condition=model.mechanisms_by_block == (Port(_SECOND, "Разработчик"),))
    ensure(condition=model.controls == "Правила")


@pytest.mark.parametrize(
    ("source", "line_number"),
    [
        ("", 1),
        ("\n# пример\nnot a declaration", 3),
        (f"{_CHAIN}A2 -> A1 : Обратно", 4),
        (f"{_CHAIN}A1 -> A2 : Повтор", 4),
        (f"{_CHAIN}control -> A1,A9 : Планы\nmechanism -> * : Команда", 4),
        (f"{_CHAIN}A1 -> A2.side : Описание", 4),
        (f"{_CHAIN}input -> A1 : Заявка\ninput -> A1 : Письмо", 5),
        ("block A1 : Один\nblock A2 : Два", 2),
        ("context A0 : Система\nblock A1 : Лишний", 2),
    ],
)
def test_invalid_text_reports_line(source: str, line_number: int) -> None:
    """Номер относится к строке исходника, включая комментарии и пустые строки."""
    with pytest.raises(ModelError, match=rf"строка {line_number}:"):
        parse_text(source)
