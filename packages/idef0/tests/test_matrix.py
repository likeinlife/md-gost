"""Сквозной перебор размеров и сочетаний внешних потоков."""

import pytest

from idef0.layout import Layout
from idef0.validation import validate
from tests.matrix import all_models
from tests.support import ensure

EXPECTED_COUNTS = (0, 0, 16, 64, 256, 1024, 4096)


@pytest.mark.parametrize("count", range(2, 7))
def test_every_supported_combination(count: int) -> None:
    """Проверить каждое допустимое сочетание без создания изображений."""
    total = 0
    for model in all_models(count):
        validate(model, Layout())
        total += 1
    ensure(condition=total == EXPECTED_COUNTS[count])
