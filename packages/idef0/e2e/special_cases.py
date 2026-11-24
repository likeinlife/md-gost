"""Граничные случаи управления, механизмов и подписей."""

from collections.abc import Iterator

from e2e.steps import steps
from idef0 import Decomposition

SECOND = "A2"


def _different() -> Decomposition:
    diagram = steps(3)
    for code in ("A1", SECOND, "A3"):
        diagram.control(f"Правило {code}", to=code)
        diagram.mechanism(f"Исполнитель {code}", to=code)
    return diagram


def _many() -> Decomposition:
    diagram = steps(3)
    for number in range(1, 7):
        diagram.control(f"Регламент {number}", to=SECOND)
        diagram.mechanism(f"Специалист {number}", to=SECOND)
    return diagram


def _mixed() -> Decomposition:
    diagram = steps(3)
    diagram.control("Правила")
    diagram.mechanism("Средства")
    diagram.control("Согласованные требования", to="A1")
    diagram.control("Ограничение бюджета", to=SECOND)
    diagram.mechanism("Среда разработки", to=SECOND)
    diagram.mechanism("Сотрудник поддержки", to="A3")
    return diagram


def _long() -> Decomposition:
    long_flow = "Согласованные функциональные требования и критерии приёмки информационной системы"
    diagram = steps(3, first_flow=long_flow)
    diagram.control("Правила")
    diagram.mechanism("Средства")
    diagram.input(
        "Первоначальная заявка заказчика с подробным описанием потребностей организации",
        to="A1",
    )
    diagram.control(
        "Подробный регламент согласования и документирования изменений требований заказчика",
        to=SECOND,
    )
    diagram.mechanism("Сотрудник технической поддержки и сопровождения системы", to="A3")
    return diagram


def special_models() -> Iterator[tuple[str, Decomposition]]:
    """Вернуть четыре сценария с разными управляющими воздействиями."""
    yield from (
        ("different", _different()),
        ("many", _many()),
        ("mixed", _mixed()),
        ("long", _long()),
    )
