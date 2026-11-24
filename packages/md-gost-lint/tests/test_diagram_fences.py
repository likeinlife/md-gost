"""Rendered figure fences follow the figure rules in every supported language."""

import pytest

from gost_lint.markdown.parser import parse as parse_document


@pytest.mark.parametrize("language", ["idef0", "plot", "plantuml"])
def test_figure_fences(language: str) -> None:
    header = f'#fig:example .{language} caption="Пример"'
    figure = parse_document(f"```{{{header}}}\nbody\n```")[0]
    assert figure.kind == "diagram"
    assert figure.meta["label"] == "fig:example"
    assert parse_document(f"```{language}\nbody\n```")[0].kind == "diagram"


def test_language_in_caption_is_a_listing() -> None:
    text = '```{.python #lst:a caption="Пример .idef0 в отчёте"}\npass\n```'
    assert parse_document(text)[0].kind == "listing"
