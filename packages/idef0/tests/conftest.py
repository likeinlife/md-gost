"""Фикстуры тестов IDEF0."""

from collections.abc import Iterator

import pytest
from matplotlib import pyplot as plt


@pytest.fixture(autouse=True)
def close_figures() -> Iterator[None]:
    """Закрывать фигуры после каждого теста."""
    yield
    plt.close("all")
