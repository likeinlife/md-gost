"""Проверка связей модели."""

from itertools import pairwise

from idef0._models import Cascade, Port
from idef0.errors import ModelError
from idef0.layout import Layout
from idef0.validation_groups import validate_groups
from idef0.validation_individual import validate_individual
from idef0.validation_links import check_links


def _check_codes(model: Cascade, layout: Layout) -> list[str]:
    codes = [block.code for block in model.blocks]
    size = len(codes)
    if not layout.min_blocks <= size <= layout.max_blocks:
        message = "Недопустимое число блоков"
        raise ModelError(message)
    if len(set(codes)) != size:
        message = "Коды блоков должны быть уникальны"
        raise ModelError(message)
    return codes


def _check_ports(ports: tuple[Port, ...], codes: list[str]) -> None:
    names = [port.block for port in ports]
    if any(name not in codes for name in names):
        message = "Внешний поток ссылается на неизвестный блок"
        raise ModelError(message)
    if len(set(names)) != len(names):
        message = "Поддерживается один вход и один выход на блок"
        raise ModelError(message)


def validate(model: Cascade, layout: Layout) -> None:
    """Проверить блоки, связи и внешние потоки каскада."""
    codes = _check_codes(model, layout)
    expected = list(pairwise(codes))
    actual = [(flow.source, flow.target) for flow in model.flows]
    if actual != expected:
        message = "Потоки должны соединять соседние блоки по порядку"
        raise ModelError(message)
    check_links(model.flows + model.input_links, codes)
    check_links(model.control_links, codes)
    _check_ports(model.inputs, codes)
    _check_ports(model.outputs, codes)
    validate_individual(model.controls_by_block, codes, layout)
    validate_individual(model.mechanisms_by_block, codes, layout)
    validate_groups(model.control_groups, codes, layout)
    validate_groups(model.mechanism_groups, codes, layout)
