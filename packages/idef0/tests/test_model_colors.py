"""Цвета блоков и стрелок при преобразовании авторских моделей."""

from dataclasses import replace

import pytest

from idef0 import PALETTE, Arrow, Block, Decomposition, Link, ModelError, Waterfall
from idef0.colors import BLACK, WHITE
from tests.support import ensure

_FIRST = "A1"
_LAST = "A2"
_BLUE = "blue"
_RED = "red"
_DARK = "#135"
_SHADE = "#113355"
_LABEL = "Данные"
_END = "Конец"
_BLOCKS = (Block(_FIRST, "Начало"), Block(_LAST, _END))
_CHAIN = (Arrow(_LABEL, color=_BLUE, text_color=_DARK),)


def test_independent_default_colors() -> None:
    """Переопределение одного цвета сохраняет остальные значения."""
    block = Block(_FIRST, "Блок", fill=_DARK)
    colors = (block.color, block.fill, block.text_color)
    ensure(condition=colors == (BLACK, _SHADE, BLACK))
    ensure(condition=_BLOCKS[0].fill == WHITE)
    arrow = Arrow(_LABEL, color=_RED)
    ensure(condition=arrow.color == PALETTE[_RED])
    ensure(condition=arrow.text_color == BLACK)


def test_compact_colors_reach_all_arrow_types() -> None:
    """Поля внешних, групповых и межблочных потоков сохраняют оформление."""
    shared = Arrow("Порядок", color=_RED, text_color=_DARK)
    diagram = Waterfall(
        blocks=_BLOCKS,
        chain=_CHAIN,
        inputs={_FIRST: shared},
        outputs={_LAST: shared},
        controls=[
            shared,
            replace(shared, to=_FIRST),
            replace(shared, to=(_FIRST, _LAST)),
        ],
        mechanisms=shared,
        links=[Link(_LAST, _FIRST, _LABEL, role="control", color=_RED, text_color=_DARK)],
    ).to_model()
    local = (*diagram.inputs, *diagram.outputs, *diagram.controls_by_block)
    for arrow in (*local, *diagram.control_links, *diagram.control_groups):
        ensure(condition=arrow.color == PALETTE[_RED])
        ensure(condition=arrow.text_color == _SHADE)
    ensure(condition=diagram.flows[0].color == PALETTE[_BLUE])
    ensure(condition=diagram.mechanisms_text_color == _SHADE)
    ensure(condition=diagram.controls_color == shared.color)


def _colored_steps() -> Decomposition:
    diagram = Decomposition().step(_FIRST, "Начало", color=_RED, fill=_BLUE, text_color=_DARK)
    diagram.step(_LAST, _END, from_previous=_CHAIN[0])
    diagram.input(_LABEL, to=_FIRST, color=_RED, text_color=_DARK)
    diagram.output(_LABEL, source=_LAST, color=_BLUE)
    diagram.control(_LABEL, to=_FIRST, source=_LAST, text_color=_DARK)
    diagram.mechanism(_LABEL, color=_RED)
    return diagram


def test_step_colors_reach_model() -> None:
    """Пошаговая запись принимает оформление блоков, основной и обратной стрелок."""
    model = _colored_steps().to_model()
    ensure(condition=model.blocks[0].fill == PALETTE[_BLUE])
    ensure(condition=model.flows[0].text_color == _SHADE)
    ensure(condition=model.inputs[0].color == PALETTE[_RED])
    ensure(condition=model.outputs[0].text_color == BLACK)
    ensure(condition=model.control_links[0].text_color == _SHADE)
    ensure(condition=model.mechanisms_color == PALETTE[_RED])


def test_rejects_ambiguous_and_duplicate_arrows() -> None:
    """Цвет не меняет адрес стрелки и уникальность именованной связи."""
    model = Waterfall(blocks=_BLOCKS, chain=_CHAIN)
    ambiguous = Arrow(_LABEL, to=_FIRST)
    with pytest.raises(ModelError, match="адресат"):
        replace(model, chain=[ambiguous]).to_model()
    with pytest.raises(ModelError, match="адресат"):
        replace(model, inputs={_FIRST: ambiguous}).to_model()
    duplicate = Link(_FIRST, _LAST, _LABEL, role="input", color=_RED)
    with pytest.raises(ModelError, match="продублирован"):
        replace(model, links=[duplicate]).to_model()


def test_rejected_style_keeps_steps_unchanged() -> None:
    """Можно добавить шаг после ошибки в цвете или адресате основной стрелки."""
    diagram = Decomposition().step(_FIRST, "Начало")
    with pytest.raises(ModelError, match="цвет"):
        diagram.step(_LAST, _END, from_previous=_LABEL, fill="unknown")
    with pytest.raises(ModelError, match="адресат"):
        diagram.step(_LAST, _END, from_previous=Arrow(_LABEL, to=_LAST))
    diagram.step(_LAST, _END, from_previous=_LABEL)
    ensure(condition=diagram.to_model().blocks == _BLOCKS)
