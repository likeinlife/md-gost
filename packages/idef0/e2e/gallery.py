"""Генерация небольшого набора рисунков для визуальной проверки."""

import sys
from pathlib import Path

from matplotlib import pyplot as plt

from e2e.cases import cases
from idef0 import draw

REVIEW_DPI = 170


def generate(directory: Path) -> None:
    """Сохранить все контрольные рисунки в указанный каталог."""
    directory.mkdir(parents=True, exist_ok=True)
    for case in cases():
        figure = draw(case.model)
        figure.savefig(directory / f"{case.name}.png", dpi=REVIEW_DPI, bbox_inches="tight")
        plt.close(figure)


def main() -> None:
    """Сохранить рисунки в каталог img рядом с этим модулем."""
    generate(Path(__file__).resolve().parent / "img")
    sys.stdout.write("Галерея IDEF0 сохранена в e2e/img.\n")


if __name__ == "__main__":
    main()
