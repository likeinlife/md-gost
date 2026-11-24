"""Размер прямоугольника для полного названия функции и обозначения блока."""

from collections.abc import Iterable
from dataclasses import dataclass, replace

from idef0._models import Block, Cascade, Context
from idef0.block_metrics import Metrics, Size
from idef0.layout import Layout


@dataclass(frozen=True)
class _Fit:
    metrics: Metrics
    size: Size
    layout: Layout

    def width(self, block: Block) -> float:
        """Оставить запас для кода и слов, которые разумно поместить целиком."""
        inset = self.layout.code_inset
        code = self.metrics.measure(block.code, code=True)
        width = self.size.width
        if code.width + inset > width:
            width = code.width + 2 * inset
        if self.metrics.measure(block.title).width <= width:
            return width
        padding = 2 * inset
        word = self.metrics.word_width(block.title, width - padding)
        return max(width, word + padding)

    def block(self, block: Block, width: float) -> Block:
        """Перенести название только при нехватке места."""
        if self.metrics.measure(block.title).width <= width:
            return block
        usable = width - 2 * self.layout.code_inset
        title = self.metrics.wrap(block.title, usable)
        return replace(block, title=title)

    def clearance(self, block: Block, width: float) -> tuple[float, float]:
        """Разместить название в середине, сохранив место для кода справа внизу."""
        title = self.metrics.measure(block.title)
        code = self.metrics.measure(block.code, code=True)
        inset = self.layout.code_inset
        bottom = inset
        if (width - title.width) / 2 < code.width + inset:
            bottom += code.height + inset / 2
        lower = max(title.height / 2 + bottom, code.height + inset)
        return lower, title.height / 2 + inset / 2


def _height(
    base: float,
    ratio: float,
    limits: Iterable[tuple[float, float]],
) -> tuple[float, float]:
    lower, upper = map(max, zip(*limits, strict=True))
    height = max(base, lower + upper)
    center = min(max(height * ratio, lower), height - upper)
    return height, center / height


def _fit(
    blocks: tuple[Block, ...],
    size: Size,
    layout: Layout,
) -> tuple[tuple[Block, ...], Size, float]:
    fit = _Fit(Metrics(layout), size, layout)
    width = max(fit.width(block) for block in blocks)
    wrapped = tuple(fit.block(block, width) for block in blocks)
    height, ratio = _height(
        size.height,
        layout.title_y_ratio,
        (fit.clearance(block, width) for block in wrapped),
    )
    return wrapped, Size(width, height), ratio


def fit_context(model: Context, layout: Layout) -> tuple[Context, Layout]:
    """Учесть надписи контекстного блока до размещения внешних стрелок."""
    size = Size(layout.context_block_width, layout.context_block_height)
    blocks, fitted, ratio = _fit((model.block,), size, layout)
    return replace(model, block=blocks[0]), replace(
        layout,
        context_block_width=fitted.width,
        title_y_ratio=ratio,
        context_block_height=fitted.height,
    )


def fit_cascade(model: Cascade, layout: Layout) -> tuple[Cascade, Layout]:
    """Учесть наиболее длинное название при выборе размеров и шага каскада."""
    original = Size(layout.block_width, layout.block_height)
    blocks, size, ratio = _fit(model.blocks, original, layout)
    extra = size.height - original.height
    return replace(model, blocks=blocks), replace(
        layout,
        block_width=size.width,
        block_height=size.height,
        title_y_ratio=ratio,
        step_x=layout.step_x + (size.width - original.width),
        step_y=layout.step_y + extra,
        control_height=layout.control_height + extra,
        figure_top_padding=layout.figure_top_padding + extra,
    )
