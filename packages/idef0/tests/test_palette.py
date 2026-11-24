"""Проверки палитры и пользовательских цветов."""

import pytest

from idef0.colors import PALETTE, resolve_color
from idef0.errors import ModelError
from tests.support import ensure


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("Black", "#000000"),
        ("blue", PALETTE["blue"]),
        ("#a0F", "#aa00ff"),
        ("#AB12cd", "#ab12cd"),
    ],
)
def test_resolves_color(spec: str, expected: str) -> None:
    """Имена и обе формы HEX приводятся к однозначному RGB."""
    ensure(condition=resolve_color(spec) == expected)


@pytest.mark.parametrize("spec", ["", "blu", "123456", "#ggg", "#1234", "#12345678"])
def test_rejects_unknown_color(spec: str) -> None:
    """Ошибки в имени, цифрах и числе каналов диагностируются при вводе."""
    with pytest.raises(ModelError, match="цвет"):
        resolve_color(spec)
