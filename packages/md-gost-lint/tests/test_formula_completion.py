"""Symbol completions for the explanation under a display formula."""

from pathlib import Path

from gost_lint.lsp.completion_formulas import formula_symbol_suggestions
from gost_lint.markdown import Document

PERT = r"""<!-- #eq:pert -->

$$T_{ож} = \frac{t_{мин} + 4t_{нв} + t_{макс}}{6}$$

где $"""
MATURITY = r"""<!-- #eq:maturity -->

$$K_{з} = \frac{\sum_{i=1}^{n} w_i x_i}{\sum_{i=1}^{n} w_i}$$

где $"""
EXPLAINED = r"""<!-- #eq:pert -->

$$T_{ож} = \frac{t_{мин} + 4t_{нв} + t_{макс}}{6}$$

где $T_{ож}$ — ожидаемая продолжительность работы, рабочих дней;
$"""


def _labels(source: str) -> list[str]:
    document = Document.from_text(Path("chapter.md"), Path(), source)
    line = len(document.lines) - 1
    choices = formula_symbol_suggestions(document, line, len(document.lines[line]))
    assert choices is not None
    return [choice.label for choice in choices]


def test_pert_symbols_follow_formula_order() -> None:
    labels = _labels(PERT)
    assert labels == ["T_{ож}", "t_{мин}", "t_{нв}", "t_{макс}"]


def test_completion_inserts_the_symbol_and_a_dash() -> None:
    document = Document.from_text(Path("chapter.md"), Path(), PERT)
    line = len(document.lines) - 1
    choice = formula_symbol_suggestions(document, line, len(document.lines[line]))
    assert choice is not None
    assert choice[0].text == "$T_{ож}$ — "


def test_typed_prefix_narrows_the_symbols() -> None:
    assert _labels(f"{PERT}t_") == ["t_{мин}", "t_{нв}", "t_{макс}"]


def test_explained_symbol_is_not_offered_again() -> None:
    assert _labels(EXPLAINED) == ["t_{мин}", "t_{нв}", "t_{макс}"]


def test_structural_commands_are_not_symbols() -> None:
    labels = _labels(MATURITY)
    assert "frac" not in labels
    assert not any(label.startswith("\\") for label in labels)


def test_weighted_sum_keeps_indexed_symbols() -> None:
    labels = _labels(MATURITY)
    assert labels == ["K_{з}", "i", "n", "w_i", "x_i"]
