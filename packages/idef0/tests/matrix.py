"""Перебор поддерживаемых сочетаний внешних потоков."""

from collections.abc import Iterator
from dataclasses import replace
from itertools import combinations, product

from idef0._models import Block, Cascade, Port
from tests.support import chain

Blocks = tuple[Block, ...]


def _subsets(blocks: Blocks) -> Iterator[Blocks]:
    for size in range(len(blocks) + 1):
        yield from combinations(blocks, size)


def _ports(blocks: Blocks, label: str) -> tuple[Port, ...]:
    return tuple(Port(block.code, label) for block in blocks)


def _model(base: Cascade, inputs: Blocks, outputs: Blocks) -> Cascade:
    incoming = _ports(inputs, "Вход")
    outgoing = _ports(outputs, "Выход")
    return replace(base, inputs=incoming, outputs=outgoing)


def all_models(count: int) -> Iterator[Cascade]:
    """Перебрать все допустимые наборы входов и выходов для числа блоков."""
    base = chain(count)
    subsets = tuple(_subsets(base.blocks))
    for inputs, outputs in product(subsets, repeat=2):
        yield _model(base, inputs, outputs)
