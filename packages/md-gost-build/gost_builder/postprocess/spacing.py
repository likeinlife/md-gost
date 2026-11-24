"""Add the required blank lines around tables, formulas, and captions."""

from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from gost_builder.ooxml import WORD_TAG_PREFIX
from gost_builder.postprocess.blank_lines import add_blank_line_after, add_blank_line_before
from gost_builder.postprocess.styles import style_name
from gost_builder.postprocess.tables.kinds import is_formula_table

CODE_STYLE = "Source Code"


def blank_line_after_tables(doc: DocxDocument) -> None:
    """Put exactly one empty line (single spacing) after every table.

    Word gives a table no bottom margin, so the next paragraph touches the
    border. An empty paragraph is used rather than `space_before` on the next
    paragraph: it reads as a literal blank line and survives manual editing.
    """
    body = doc.element.body
    for tbl in list(body.iterchildren(f"{WORD_TAG_PREFIX}tbl")):
        if is_formula_table(Table(tbl, doc)):
            continue  # spacing around a formula follows its own rule
        add_blank_line_after(tbl, doc)


def blank_lines_around_formulas(doc: DocxDocument) -> None:
    """«Выше и ниже каждой формулы должна быть оставлена одна свободная строка».

    Экспликация отдельной строки не требует: она лежит внутри той же таблицы,
    сразу под формулой, как того и требует ГОСТ.
    """
    body = doc.element.body
    for tbl in list(body.iterchildren(f"{WORD_TAG_PREFIX}tbl")):
        if not is_formula_table(Table(tbl, doc)):
            continue
        add_blank_line_before(tbl, doc)
        add_blank_line_after(tbl, doc)


def blank_line_after_code(doc: DocxDocument) -> None:
    """Пустая строка после блока кода — тот же зазор, что у таблицы.

    Весь блок кода pandoc укладывает в один абзац, поэтому интервалов между
    его строками нет и следующий абзац иначе начинается вплотную к коду.
    """
    body = doc.element.body
    for child in list(body.iterchildren(f"{WORD_TAG_PREFIX}p")):
        para = Paragraph(child, doc)
        if style_name(para) == CODE_STYLE and para.text.strip():
            add_blank_line_after(child, doc)


def blank_line_after_image_captions(doc: DocxDocument) -> None:
    """Insert the same blank line after a figure caption as after a table.

    The caption closes the figure block, so the body text that follows needs the
    same visual gap; `space_after` on the style is not enough to match it.
    """
    body = doc.element.body
    for child in list(body.iterchildren(f"{WORD_TAG_PREFIX}p")):
        para = Paragraph(child, doc)
        if style_name(para) == "GOSTImageCaption" and para.text.strip():
            add_blank_line_after(child, doc)
