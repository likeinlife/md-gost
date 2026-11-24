"""Проверка индивидуальных управляющих воздействий и механизмов."""

from dataclasses import replace

import pytest

from e2e.special_cases import special_models
from idef0._models import Port
from idef0.errors import ModelError
from idef0.layout import DEFAULT_LAYOUT
from idef0.validation import validate
from idef0.waterfall import _draw_waterfall
from tests.block_checks import check_labels_outside_blocks
from tests.individual_checks import (
    check_no_overlap,
    expected_labels,
    many_labels,
    normal_labels,
    select_labels,
)
from tests.support import chain, ensure


def test_six_horizontal_labels() -> None:
    """Шесть стрелок с каждой стороны сохраняют неперекрывающиеся подписи."""
    models = dict(special_models())
    figure = _draw_waterfall(models["many"].to_model())
    check_no_overlap(figure, many_labels())
    names = many_labels()
    labels = select_labels(figure, names)
    ensure(condition=all(label.get_rotation() == 0 for label in labels))
    ensure(condition=all(label.get_horizontalalignment() == "center" for label in labels))


def test_long_labels_are_preserved_on_diagram() -> None:
    """Длинные подписи переносятся и остаются непосредственно на схеме."""
    models = dict(special_models())
    model = models["long"].to_model()
    figure = _draw_waterfall(model)
    actual = normal_labels(figure)
    expected = expected_labels(model)
    ensure(condition=all(label in actual for label in expected))
    check_labels_outside_blocks(figure, set(expected))


def test_unknown_individual_block_is_rejected() -> None:
    """Индивидуальную стрелку нельзя привязать к несуществующему блоку."""
    model = replace(chain(2), controls_by_block=(Port("A9", "Правило"),))
    with pytest.raises(ModelError, match="неизвестный блок"):
        validate(model, DEFAULT_LAYOUT)


def test_too_many_individual_arrows_are_rejected() -> None:
    """На одной стороне допускается не более шести индивидуальных стрелок."""
    labels = (f"Правило {number}" for number in range(7))
    ports = tuple(Port("A1", label) for label in labels)
    model = replace(chain(2), mechanisms_by_block=ports)
    with pytest.raises(ModelError, match="Слишком много"):
        validate(model, DEFAULT_LAYOUT)
