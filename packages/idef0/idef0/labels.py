"""Перенос длинных подписей без замены исходного текста."""

from textwrap import fill

from idef0.layout import Layout


def wrap_label(label: str, layout: Layout) -> str:
    """Перенести каждую строку подписи на ширину, заданную раскладкой."""
    lines = label.split("\n")
    wrapped = (fill(line, width=layout.label_wrap_width) for line in lines)
    return "\n".join(wrapped)
