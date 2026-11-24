"""Source formatting shared by `md-gost format` and the editor."""

from gost_lint.formatter import format_text

CHAPTER = "# Глава\n\n"
PROSE = "Текст  после."
TABLE = "|A|B|\n|---|---|\n|x|два|"
ALIGNED = "| A   | B   |\n| --- | --- |\n| x   | два |"


def test_spaces_tables_and_single_trailing_break() -> None:
    source = f"{CHAPTER}{PROSE}\n\n{TABLE}\n\n"
    assert format_text(source) == f"{CHAPTER}Текст после.\n\n{ALIGNED}\n"
    assert format_text(format_text(source)) == format_text(source)


def test_preserves_crlf_and_formula_spaces() -> None:
    source = "# Глава\r\n\r\nТекст  после.\r\n\r\n$$\r\na  =  b ,\r\n$$\r\n"
    formatted = format_text(source)
    assert "Текст после.\r\n" in formatted
    assert "a  =  b ," in formatted
    assert "\n" not in formatted.replace("\r\n", "")


def test_keeps_heading_numbers_and_unclosed_fence() -> None:
    heading = f"{CHAPTER}## 3.1. Название\n\nТекст.\n"
    assert "## 3.1. Название" in format_text(heading)
    fenced = f"{CHAPTER}```\nкод\n\n"
    assert format_text(fenced) == fenced


def test_closed_fence_loses_only_extra_breaks() -> None:
    source = f"{CHAPTER}```\nкод\n```\n\n\n"
    assert format_text(source) == f"{CHAPTER}```\nкод\n```\n"
