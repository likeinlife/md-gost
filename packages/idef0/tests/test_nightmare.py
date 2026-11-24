"""Проверка плотной схемы из шести блоков и множества стрелок."""

from e2e.nightmare import nightmare
from idef0.waterfall import _draw_waterfall
from tests.block_checks import check_labels_outside_blocks
from tests.individual_checks import check_no_overlap


def test_dense_diagram_labels_do_not_overlap() -> None:
    """Подписи всех 60 индивидуальных стрелок не накладываются друг на друга и на блоки."""
    model = nightmare().to_model()
    ports = model.controls_by_block + model.mechanisms_by_block
    names = {port.label for port in ports}
    names.update(port.label for port in model.inputs + model.outputs)
    names.update(group.label for group in model.control_groups + model.mechanism_groups)
    names.update((model.controls, model.mechanisms))
    figure = _draw_waterfall(model)
    check_no_overlap(figure, names)
    check_labels_outside_blocks(figure, names)
