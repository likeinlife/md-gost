import re

import pytest
from conftest import BuiltFactory, needs_pandoc
from test_helpers import W_T

pytestmark = [needs_pandoc, pytest.mark.build]


def test_chapter_heading_keeps_inline_markup(built: BuiltFactory) -> None:
    """«Глава N.» is stripped without flattening the rest of the heading."""
    parts = built("# Глава 1. Анализ *предметной* области\n\nтекст.\n")
    document = parts["word/document.xml"]

    assert "1. Анализ предметной области" in "".join(W_T.findall(document))
    runs = re.findall(r"<w:r\b.*?</w:r>", document, re.DOTALL)
    assert any("<w:i/>" in run and "предметной" in run for run in runs), (
        "курсив внутри заголовка потерялся"
    )


def _style_xml(styles: str, style_id: str) -> str:
    marker = f'w:styleId="{style_id}"'
    start = styles.rfind("<w:style ", 0, styles.index(marker))
    return styles[start : styles.index("</w:style>", start)]


def test_toc_heading_is_black_bold_and_centered(built: BuiltFactory) -> None:
    """Заголовок «Содержание» чёрный, жирный и стоит по центру."""
    parts = built("# Глава 1. Тест\n\nТекст.\n")
    style = _style_xml(parts["word/styles.xml"], "TOCHeading")

    assert 'w:jc w:val="center"' in style
    assert 'w:color w:val="000000"' in style
    assert "themeColor" not in style
    assert "<w:b/>" in style
    assert "<w:bCs/>" in style


def test_internal_link_stays_black(built: BuiltFactory) -> None:
    """Ссылка, в том числе на приложение, остаётся чёрной и после перехода."""
    parts = built(
        "# Глава 1. Тест\n\n"
        "Фрагмент приведён в [приложении А](#appendix-a).\n\n"
        "# Приложение А. Фрагмент {#appendix-a}\n\n"
        "Текст приложения.\n",
    )

    for style_id in ("Hyperlink", "FollowedHyperlink"):
        style = _style_xml(parts["word/styles.xml"], style_id)
        assert 'w:color w:val="000000"' in style
        assert "themeColor" not in style
    link = re.search(r"<w:hyperlink\b.*?</w:hyperlink>", parts["word/document.xml"], re.DOTALL)
    assert link is not None
    assert 'w:rStyle w:val="Hyperlink"' in link.group(0)
    assert "w:color" not in link.group(0)


def test_em_dash_replaced_in_every_part(built: BuiltFactory) -> None:
    em = "—"
    parts = built(f"# Глава 1. Тест\n\nТекст {em} раз.[^a]\n\n[^a]: Сноска {em} два.\n")

    assert "word/footnotes.xml" in parts, "сносок нет — тест ничего не проверяет"
    for name, xml in parts.items():
        if name.startswith("word/"):
            assert em not in "".join(W_T.findall(xml)), f"длинное тире осталось в {name}"
