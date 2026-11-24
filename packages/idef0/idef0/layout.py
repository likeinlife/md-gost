"""Параметры геометрии и оформления диаграмм."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    """Геометрия диаграммы в условных единицах и оформление в пунктах.

    Координаты рассчитаны для читаемой схемы на странице, а не по стандарту
    IDEF0. Параметры с суффиксом ``ratio`` — доли ширины или высоты блока.
    """

    # Размер каскадного блока и шаг между левыми нижними углами соседних блоков.
    block_width: float = 1.55
    block_height: float = 0.85
    step_x: float = 2.1
    step_y: float = 1.55
    first_x: float = 0.9
    last_y: float = 2.3
    # Верхняя шина над первым блоком, нижняя шина и подпись под ней.
    control_height: float = 1.5
    mechanism_height: float = 0.55
    bus_label_gap: float = 0.15
    figure_top_padding: float = 2.3
    figure_right_padding: float = 2.15
    # Положение текста в блоке: название чуть выше центра, код в нижнем углу.
    title_y_ratio: float = 0.59
    code_inset: float = 0.08
    # Доли высоты блока для отдельных стрелок внешних входов и выходов.
    input_port_ratio: float = 0.2
    output_port_ratio: float = 0.7
    outside_left: float = 0.05
    outside_right_inset: float = 0.15
    input_label_gap: float = 0.13
    flow_label_x_gap: float = 0.05
    flow_label_y_gap: float = 0.1
    flow_label_y_with_output: float = -0.65
    output_label_right_inset: float = 1.95
    output_label_gap: float = 0.12
    # Размер контекстного холста и положение блока на нём.
    context_width: float = 10
    context_height: float = 5.6
    context_block_x: float = 3.6
    context_block_y: float = 2
    context_block_width: float = 2.8
    context_block_height: float = 1.6
    context_arrow_margin: float = 0.4
    context_control_top: float = 5.1
    context_mechanism_bottom: float = 0.5
    context_input_label_x: float = 0.4
    context_output_label_x: float = 6.55
    context_side_label_y: float = 2.95
    context_vertical_label_x: float = 5.12
    context_control_label_y: float = 4.5
    context_mechanism_label_y: float = 1.05
    # Запас между контекстными стрелками и их подписями.
    context_side_padding: float = 0.25
    context_line_spacing: float = 1.2
    context_side_label_gap: float = 0.1
    context_vertical_padding: float = 0.3
    # Толщина линий и размеры текста заданы в пунктах Matplotlib.
    line_width: float = 1.1
    bus_line_width: float = 1
    arrow_size: float = 11
    title_font_size: float = 9.5
    code_font_size: float = 8.5
    bus_font_size: float = 10
    port_font_size: float = 9
    flow_font_size: float = 8
    output_font_size: float = 8.5
    label_box_padding: float = 0.4
    # Слои: стрелки под блоками, подписи поверх контуров.
    arrow_layer: int = 2
    block_layer: int = 3
    block_text_layer: int = 4
    flow_text_layer: int = 5
    max_blocks: int = 6
    min_blocks: int = 2
    # Индивидуальные стрелки и перенос подписей.
    max_individual_arrows: int = 6
    individual_arrow_length: float = 0.6
    individual_text_padding: float = 0.35
    individual_font_size: float = 7
    individual_line_spacing: float = 1.2
    individual_label_pitch: float = 0.25
    label_wrap_width: int = 22
    # Потребность в месте для горизонтальных подписей при переносе строк.
    text_horizontal_padding: float = 0.2
    text_vertical_padding: float = 0.25
    flow_line_height: float = 0.19
    points_per_inch: int = 72
    # Вертикальный шаг шин групповых стрелок и отступ подписи.
    group_bus_spacing: float = 0.5
    group_label_gap: float = 0.12
    group_dot_size: float = 3
    group_font_size: float = 8
    group_line_height: float = 0.18
    max_groups_per_side: int = 4
    min_group_targets: int = 2
    # Интервал между дорожками обратных межблочных стрелок.
    link_lane_spacing: float = 0.36


DEFAULT_LAYOUT = Layout()
