"""Проверка групповых стрелок."""

from idef0._models import Group
from idef0.errors import ModelError
from idef0.layout import Layout


def _check_group(group: Group, codes: list[str], layout: Layout) -> None:
    targets = group.targets
    count = len(targets)
    repeated = len(set(targets)) != count
    if repeated or count < layout.min_group_targets:
        message = "Групповая стрелка должна иметь хотя бы двух разных адресатов"
        raise ModelError(message)
    if any(code not in codes for code in targets):
        message = "Групповая стрелка ссылается на неизвестный блок"
        raise ModelError(message)


def validate_groups(groups: tuple[Group, ...], codes: list[str], layout: Layout) -> None:
    """Проверить количество групп и адресатов каждой стрелки."""
    if len(groups) > layout.max_groups_per_side:
        message = "Слишком много групповых стрелок на одной стороне"
        raise ModelError(message)
    for group in groups:
        _check_group(group, codes, layout)
