"""Formula markers, inline formulas, and explanation paragraph checks."""

import re
from collections.abc import Iterator
from itertools import pairwise

from gost_lint.markdown import Block, Document
from gost_lint.markdown.adjacent_blocks import with_next
from gost_lint.markdown.refs import strip_code
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]
EXPLANATION_START = re.compile(r"^\s*[Гг]де\s")
DEFINITION_LINE = re.compile(r"^\s*\$[^$]+\$\s*[—–-]")
PROSE_KINDS = ("paragraph", "list")
COMMENT_KIND = "comment"
PREVIEW_LENGTH = 40


@rule("EQ001", "error", "маркер формулы оторван от формулы")
def eq_marker_not_before_formula(doc: Document) -> FileIssue:
    """Handle eq marker not before formula."""
    blocks = [block for block in doc.blocks if block.kind != COMMENT_KIND]
    for block, next_block in with_next(blocks):
        if block.kind != "eq_marker":
            continue
        yield from _extra_text_issue(block)
        if next_block is None or next_block.kind != "formula":
            yield (
                block.start,
                1,
                (
                    f"после маркера {block.meta['label']} нет формулы $$…$$ — "
                    f"метка уедет к следующей формуле или сборка остановится"
                ),
            )


def _extra_text_issue(block: Block) -> FileIssue:
    extra = block.meta["extra"]
    if extra:
        excerpt = extra[:PREVIEW_LENGTH]
        message = f"маркер {block.meta['label']} несёт текст «{excerpt}» — у формулы есть номер, "
        yield (block.start, 1, f"{message}но не подпись")


@rule("EQ002", "error", "формула набрана внутри абзаца")
def formula_inside_paragraph(doc: Document) -> FileIssue:
    """Handle formula inside paragraph."""
    for block in doc.of_kind(*PROSE_KINDS):
        yield from _inline_formula_issue(block)


def _inline_formula_issue(block: Block) -> FileIssue:
    for offset, line in enumerate(block.lines):
        column = strip_code(line).find("$$")
        if column >= 0:
            yield (
                block.start + offset,
                column + 1,
                (
                    "$$…$$ внутри абзаца — формула останется в строке текста, "
                    "без номера; отделите её пустой строкой"
                ),
            )
            return


@rule("EQ004", "error", "строка экспликации оторвана от «где»")
def explanation_split_into_paragraphs(doc: Document) -> FileIssue:
    """Handle explanation split into paragraphs."""
    blocks = [block for block in doc.blocks if block.kind != COMMENT_KIND]
    for previous, block in pairwise(blocks):
        if _is_split_explanation(previous, block):
            yield (
                block.start,
                1,
                (
                    "расшифровка обозначения стоит отдельным абзацем — перенесите "
                    "её в абзац «где …» переводом строки, иначе символы не "
                    "выровняются под формулой"
                ),
            )


def _is_split_explanation(previous: Block, block: Block) -> bool:
    starts_definition = block.kind == "paragraph" and DEFINITION_LINE.match(block.lines[0])
    if not starts_definition:
        return False
    opens_explanation = previous.kind == "paragraph" and EXPLANATION_START.match(previous.lines[0])
    return previous.kind == "formula" or bool(opens_explanation)
