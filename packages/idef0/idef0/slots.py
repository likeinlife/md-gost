"""Разделение сторон блока между общими и индивидуальными стрелками."""

from idef0._models import Cascade
from idef0.slot_data import groups, ports, shared


def _selected(model: Cascade, code: str, *, top: bool) -> list[int]:
    choices = groups(model, top=top)
    return [index for index, group in enumerate(choices) if code in group.targets]


def _total(model: Cascade, code: str, *, top: bool) -> int:
    group_count = len(_selected(model, code, top=top))
    choices = ports(model, top=top)
    individual = sum(port.block == code for port in choices)
    extra = model.control_links if top else ()
    return (
        group_count
        + individual
        + shared(model, top=top)
        + sum(link.target == code for link in extra)
    )


def group_ratio(model: Cascade, code: str, group_index: int, *, top: bool) -> float:
    """Вернуть позицию подключения выбранной групповой стрелки."""
    selected = _selected(model, code, top=top)
    slot = selected.index(group_index) + 1
    return slot / (_total(model, code, top=top) + 1)


def shared_ratio(model: Cascade, code: str, *, top: bool) -> float:
    """Вернуть позицию общей для всех блоков стрелки."""
    slot = len(_selected(model, code, top=top)) + 1
    return slot / (_total(model, code, top=top) + 1)


def individual_ratio(model: Cascade, code: str, index: int, *, top: bool) -> float:
    """Вернуть позицию индивидуальной стрелки на стороне блока."""
    group_count = len(_selected(model, code, top=top))
    slot = group_count + shared(model, top=top) + index + 1
    return slot / (_total(model, code, top=top) + 1)


def control_link_ratio(model: Cascade, code: str, index: int) -> float:
    """Вернуть позицию внутреннего управления после внешних стрелок."""
    individual = sum(port.block == code for port in model.controls_by_block)
    return individual_ratio(model, code, individual + index, top=True)
