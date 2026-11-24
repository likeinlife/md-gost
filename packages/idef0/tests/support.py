"""Общие помощники тестов диаграмм."""

from itertools import pairwise

import pytest

from idef0._models import Block, Cascade, Flow


def _blocks(count: int) -> tuple[Block, ...]:
    numbers = range(1, count + 1)
    return tuple(Block(f"A{number}", f"Блок {number}") for number in numbers)


def _flow(pair: tuple[Block, Block]) -> Flow:
    return Flow(pair[0].code, pair[1].code, "Данные")


def _flows(blocks: tuple[Block, ...]) -> tuple[Flow, ...]:
    pairs = pairwise(blocks)
    return tuple(_flow(pair) for pair in pairs)


def chain(count: int) -> Cascade:
    """Создать последовательную модель с заданным числом блоков."""
    blocks = _blocks(count)
    return Cascade(blocks, _flows(blocks), (), (), "Правила", "Средства")


def ensure(*, condition: bool) -> None:
    """Завершить тест ошибкой, если условие не выполняется."""
    if not condition:
        pytest.fail("Ожидание теста не выполнено")
