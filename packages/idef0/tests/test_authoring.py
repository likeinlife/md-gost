"""Проверки авторских форм декомпозиции и сообщений об ошибках."""

from dataclasses import replace

import pytest

from idef0 import Arrow, Block, Decomposition, Link, ModelError, Waterfall
from tests.support import ensure

_FIRST = "A1"
_LAST = "A2"
_CODES = (_FIRST, _LAST)
_ORDER = "План"
_COMMON = "Задание"
_GROUP = "Правила"
_RECEIVE = "Получить"
_PROCESS = "Обработать"


def _compact() -> Waterfall:
    return Waterfall(
        blocks=[Block(_FIRST, _RECEIVE), Block(_LAST, _PROCESS)],
        chain=[_COMMON],
        inputs={_FIRST: "Запрос"},
        outputs={_LAST: "Отчёт"},
        controls=[
            Arrow(_ORDER),
            Arrow("Срок", to=_FIRST),
            Arrow(_GROUP, to=_CODES),
        ],
        mechanisms="Команда",
        links=[
            Link(_LAST, _FIRST, "Уточнение", role="input"),
            Link(_LAST, _FIRST, "Проверка", role="control"),
        ],
    )


def _steps() -> Decomposition:
    diagram = Decomposition()
    diagram.step(_FIRST, _RECEIVE).step(_LAST, _PROCESS, from_previous=_COMMON)
    diagram.input("Запрос", to=_FIRST).output("Отчёт", source=_LAST)
    diagram.control(_ORDER).control("Срок", to=_FIRST)
    diagram.control(_GROUP, to=_CODES)
    diagram.mechanism("Команда")
    diagram.input("Уточнение", source=_LAST, to=_FIRST)
    return diagram.control("Проверка", source=_LAST, to=_FIRST)


def test_authoring_forms_have_the_same_model() -> None:
    """У стрелок сохраняются роли, адресаты и отдельные подписи."""
    model = _compact().to_model()
    ensure(condition=_steps().to_model() == model)
    ensure(condition=model.flows[0].source == _FIRST)
    ensure(condition=model.control_groups[0].targets == _CODES)
    ensure(condition=model.input_links[0].label == "Уточнение")
    ensure(condition=model.control_links[0].label == "Проверка")


@pytest.mark.parametrize("labels", [[], [_ORDER, _ORDER], "Я"])
def test_requires_label_per_neighbor(labels: list[str] | str) -> None:
    """Подписи задаются последовательностью по одной на пару блоков."""
    with pytest.raises(ModelError, match="chain"):
        replace(_compact(), chain=labels).to_model()


def test_invalid_step_keeps_the_builder_usable() -> None:
    """Отклонённый шаг не меняет декомпозицию."""
    diagram = Decomposition()
    with pytest.raises(ModelError, match="Первый шаг"):
        diagram.step(_FIRST, _RECEIVE, from_previous=_COMMON)
    diagram.step(_FIRST, _RECEIVE)
    with pytest.raises(ModelError, match="from_previous"):
        diagram.step(_LAST, _PROCESS)
    diagram.step(_LAST, _PROCESS, from_previous=_COMMON)
    ensure(condition=diagram.to_model().flows[0].label == _COMMON)


def test_validates_ports_and_shared_arrows() -> None:
    """Ошибочное добавление порта сохраняет первоначальный вход."""
    diagram = _steps()
    original = diagram.to_model()
    with pytest.raises(ModelError, match="уже есть"):
        diagram.input("Замена входа", to=_FIRST)
    with pytest.raises(ModelError, match="одного получателя"):
        diagram.control("Обратная связь", source=_LAST, to=_CODES)
    ensure(condition=diagram.to_model() == original)
    diagram.control("Ещё одна общая стрелка")
    with pytest.raises(ModelError, match="одна общая стрелка"):
        diagram.to_model()
