"""Получение управляющих воздействий и механизмов блока."""

from idef0._models import Cascade, Group, Port


def groups(model: Cascade, *, top: bool) -> tuple[Group, ...]:
    """Выбрать группы для стороны блока."""
    return model.control_groups if top else model.mechanism_groups


def ports(model: Cascade, *, top: bool) -> tuple[Port, ...]:
    """Выбрать индивидуальные стрелки для стороны блока."""
    return model.controls_by_block if top else model.mechanisms_by_block


def shared(model: Cascade, *, top: bool) -> bool:
    """Проверить наличие общей стрелки на стороне блока."""
    return bool(model.controls if top else model.mechanisms)
