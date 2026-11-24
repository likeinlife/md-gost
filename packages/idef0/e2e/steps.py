"""Нумерованная цепочка блоков для примеров каскада."""

from idef0 import Decomposition


def steps(size: int, *, first_flow: str = "Данные") -> Decomposition:
    """Связать соседние шаги и подписать первый переход отдельно."""
    diagram = Decomposition()
    diagram.step("A1", "Блок 1")
    diagram.step("A2", "Блок 2", from_previous=first_flow)
    for number in range(3, size + 1):
        diagram.step(f"A{number}", f"Блок {number}", from_previous="Данные")
    return diagram
