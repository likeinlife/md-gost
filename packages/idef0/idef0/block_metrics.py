"""Измерение и перенос надписей с фактическими шрифтами Matplotlib."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import partial

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from idef0.layout import Layout


@dataclass(frozen=True)
class Size:
    """Ширина и высота в координатах диаграммы."""

    width: float
    height: float


class Metrics:
    """Размеры объектов Text до выбора холста и положения стрелок."""

    def __init__(self, layout: Layout) -> None:
        """Применить те же параметры шрифта, DPI и полей, что и у итоговых осей."""
        figure = Figure(figsize=(1, 1))
        self._renderer = FigureCanvasAgg(figure).get_renderer()
        self._title = figure.text(0, 0, "", fontsize=layout.title_font_size)
        self._code = figure.text(0, 0, "", fontsize=layout.code_font_size)
        margins = figure.subplotpars
        self._scale = Size(
            figure.dpi * (margins.right - margins.left),
            figure.dpi * (margins.top - margins.bottom),
        )

    def measure(self, label: str, *, code: bool = False) -> Size:
        """Измерить всю надпись, включая межстрочные интервалы."""
        artist = self._code if code else self._title
        artist.set_text(label)
        bounds = artist.get_window_extent(self._renderer)
        width = bounds.width / self._scale.width
        return Size(width, bounds.height / self._scale.height)

    def word_width(self, label: str, preferred: float) -> float:
        """Сохранить слова целиком до двойной ширины, затем переносить по символам."""
        widths = (self.measure(word).width for word in label.split())
        longest = max(widths, default=0)
        if longest <= 2 * preferred:
            return longest
        glyphs = (self.measure(char).width for char in set(label))
        return max(2 * preferred, max(glyphs, default=0))

    def wrap(self, label: str, width: float) -> str:
        """Сохранить ручные переносы, добавить строки для слишком длинных надписей."""
        fits = partial(self._fits, width=width)
        return "\n".join(_wrap_line(line, fits) for line in label.split("\n"))

    def _fits(self, line: str, *, width: float) -> bool:
        return self.measure(line).width <= width


def _pieces(word: str, fits: Callable[[str], bool]) -> Iterator[str]:
    if fits(word):
        yield word
        return
    piece = ""
    for char in word:
        if piece and not fits(piece + char):
            yield piece
            piece = ""
        piece += char
    yield piece


def _wrap_line(line: str, fits: Callable[[str], bool]) -> str:
    if fits(line):
        return line
    rows = []
    current = ""
    pieces = (piece for word in line.split() for piece in _pieces(word, fits))
    for piece in pieces:
        candidate = f"{current} {piece}" if current else piece
        if current and not fits(candidate):
            rows.append(current)
            current = piece
        else:
            current = candidate
    rows.append(current)
    return "\n".join(rows)
