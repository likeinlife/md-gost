"""Сравнение цветов геометрии и подписей в объектах Matplotlib."""

from collections import Counter

from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.text import Annotation

from tests.support import ensure

CONTROL_GROUP = "#118"
MECHANISM_GROUP = "#119"


def heads(ax: Axes) -> Counter[str]:
    """Считать наконечники по цвету, сверяя их контур и заливку."""
    counts: Counter[str] = Counter()
    for artist in ax.texts:
        if isinstance(artist, Annotation) and artist.arrow_patch is not None:
            patch = artist.arrow_patch
            color = mcolors.to_hex(patch.get_edgecolor())
            ensure(condition=mcolors.to_hex(patch.get_facecolor()) == color)
            counts[color] += 1
    return counts


def labels(ax: Axes) -> dict[str, str]:
    """Получить видимые надписи и цвета их текста."""
    visible = (text for text in ax.texts if text.get_text())
    return {text.get_text(): mcolors.to_hex(text.get_color()) for text in visible}


def expected_heads(*, linked: bool) -> Counter[str]:
    """Ожидаемые цвета всех головок в проверочном каскаде."""
    singles = ("#111", "#112", "#113", "#116", "#117")
    doubles = ("#114", "#115", CONTROL_GROUP, MECHANISM_GROUP)
    counts = Counter({mcolors.to_hex(color): 2 for color in doubles})
    counts.update(map(mcolors.to_hex, singles))
    if linked:
        counts.update(map(mcolors.to_hex, ("#11a", "#11b")))
    return counts


def check_wires(ax: Axes, *, linked: bool) -> None:
    """Проверить цвета участков линий и обоих компонентов маркера."""
    colors = [mcolors.to_hex(line.get_color()) for line in ax.lines]
    expected = [
        "#111",
        "#114",
        "#115",
        CONTROL_GROUP,
        CONTROL_GROUP,
        MECHANISM_GROUP,
        MECHANISM_GROUP,
    ]
    if linked:
        expected.extend(("#11a", "#11b"))
    expected_counts = Counter(map(mcolors.to_hex, expected))
    ensure(condition=Counter(colors) == expected_counts)
    for line in ax.lines:
        if line.get_marker() == "o":
            ensure(condition=line.get_markerfacecolor() == line.get_color())
            ensure(condition=line.get_markeredgecolor() == line.get_color())
