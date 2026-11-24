"""Проверка количества и адресатов индивидуальных стрелок."""

from idef0._models import Port
from idef0.errors import ModelError
from idef0.layout import Layout


def validate_individual(ports: tuple[Port, ...], codes: list[str], layout: Layout) -> None:
    """Проверить адреса и ограничение числа стрелок на одну сторону блока."""
    for code in codes:
        count = sum(port.block == code for port in ports)
        if count > layout.max_individual_arrows:
            message = "Слишком много индивидуальных стрелок у блока"
            raise ModelError(message)
    if any(port.block not in codes for port in ports):
        message = "Индивидуальная стрелка ссылается на неизвестный блок"
        raise ModelError(message)
