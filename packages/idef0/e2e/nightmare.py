"""Предельный сценарий с большим числом стрелок."""

from e2e.steps import steps
from idef0 import Decomposition

ARROWS_PER_BLOCK = 5
_INPUT_BLOCKS = 4
_GROUP = ("A1", "A3", "A5")


def _external_arrows(diagram: Decomposition) -> None:
    for index in range(1, 7):
        code = f"A{index}"
        if index <= _INPUT_BLOCKS:
            diagram.input(f"Заявка {code}", to=code)
        diagram.output(f"Итог {code}", source=code)
        for number in range(1, ARROWS_PER_BLOCK + 1):
            diagram.control(f"Правило {code}.{number}", to=code)
            diagram.mechanism(f"Исполнитель {code}.{number}", to=code)


def nightmare() -> Decomposition:
    """Добавить по пять индивидуальных стрелок каждого типа на каждый блок."""
    diagram = steps(6)
    diagram.control("Правила")
    diagram.mechanism("Средства")
    _external_arrows(diagram)
    diagram.control("Общий контроль A1, A3, A5", to=_GROUP)
    diagram.control("Общий регламент A2, A4, A5", to=("A2", "A4", "A5"))
    diagram.mechanism("Общая платформа", to=_GROUP)
    return diagram
