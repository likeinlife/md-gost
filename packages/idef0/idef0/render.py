"""Построение контекста и декомпозиции с выбранным оформлением."""

from matplotlib import rc_context
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, findfont

from idef0._models import Context
from idef0.api import Waterfall
from idef0.canvas import fit_canvas
from idef0.context import _draw_context
from idef0.decomposition import Decomposition
from idef0.layout import DEFAULT_LAYOUT, Layout
from idef0.waterfall import _draw_waterfall

_REPORT_MARGIN = 1.5
_REPORT_BLOCK_WIDTH = 1.25
_REPORT_FONT_SIZE = 13
_REPORT_LAYOUT = Layout(
    first_x=_REPORT_MARGIN,
    block_width=_REPORT_BLOCK_WIDTH,
    block_height=1,
    text_horizontal_padding=0.1,
    figure_right_padding=_REPORT_MARGIN,
    output_label_right_inset=_REPORT_BLOCK_WIDTH,
    title_font_size=_REPORT_FONT_SIZE,
    code_font_size=_REPORT_FONT_SIZE,
    bus_font_size=_REPORT_FONT_SIZE,
    port_font_size=_REPORT_FONT_SIZE,
    output_font_size=_REPORT_FONT_SIZE,
    flow_font_size=_REPORT_FONT_SIZE,
)


def _figure(diagram: Context | Waterfall | Decomposition, layout: Layout) -> Figure:
    if isinstance(diagram, Context):
        return fit_canvas(_draw_context(diagram, layout))
    if isinstance(diagram, (Waterfall, Decomposition)):
        return fit_canvas(_draw_waterfall(diagram.to_model(layout), layout))
    message = "diagram must be an idef0.Context, idef0.Waterfall or idef0.Decomposition"
    raise TypeError(message)


def draw(
    diagram: Context | Waterfall | Decomposition,
    layout: Layout | None = None,
    *,
    style: str | None = None,
) -> Figure:
    """Построить рисунок. Профиль report задаёт шрифт и раскладку для отчёта на A4.

    Явный layout переопределяет геометрию и размеры текста выбранного профиля.
    """
    if style is None:
        return _figure(diagram, layout or DEFAULT_LAYOUT)
    if style != "report":
        message = f"Неизвестный профиль IDEF0 {style!r}. Доступен 'report'."
        raise ValueError(message)
    fonts = FontProperties(family=["Times New Roman", "Liberation Serif", "DejaVu Serif"])
    page_font = FontProperties(fname=findfont(fonts)).get_name()
    with rc_context({"font.family": page_font}):
        return _figure(diagram, layout or _REPORT_LAYOUT)
