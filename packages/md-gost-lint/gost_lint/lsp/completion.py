"""Context-sensitive Markdown completions for GOST works."""

from gost_lint.lsp.completion_blocks import block_suggestions
from gost_lint.lsp.completion_formulas import formula_symbol_suggestions
from gost_lint.lsp.completion_heading_attrs import heading_attribute_suggestions
from gost_lint.lsp.completion_listing_paths import listing_path_suggestions
from gost_lint.lsp.completion_markup import markup_suggestions
from gost_lint.lsp.completion_paths import path_suggestions
from gost_lint.lsp.completion_refs import reference_at
from gost_lint.lsp.completion_tables import row_suggestion
from gost_lint.lsp.completion_types import EditorOptions, Suggestion
from gost_lint.lsp.section_links import fragment_at
from gost_lint.markdown import Document
from gost_lint.work import Work

ROW_PREFIXES = ("", "|")


def complete(
    document: Document,
    work: Work,
    line: int,
    column: int,
    options: EditorOptions,
) -> list[Suggestion]:
    """Return edits using zero-based Python character offsets on the requested line."""
    if not document.is_prose_position(line, column):
        paths = listing_path_suggestions(document, work.root, line, column, options.workspace_root)
        return paths or block_suggestions(
            document,
            work.docs,
            line,
            column,
            options.pandoc_languages,
        )
    source = document.lines[line] if line < len(document.lines) else ""
    links = _links(document, work, line, column)
    if links is not None:
        return links
    typed = _typed(document, line, column)
    if typed is not None:
        return typed
    if source.strip() in ROW_PREFIXES and not source[column:].strip():
        row = _row(document, line, source, snippets=options.snippets)
        if row is not None:
            return row
    return markup_suggestions(
        document,
        work.docs,
        line,
        column,
        snippets=options.snippets,
    )


def _typed(document: Document, line: int, column: int) -> list[Suggestion] | None:
    symbols = formula_symbol_suggestions(document, line, column)
    if symbols is not None:
        return symbols
    return heading_attribute_suggestions(document, line, column)


def _links(document: Document, work: Work, line: int, column: int) -> list[Suggestion] | None:
    source = document.lines[line] if line < len(document.lines) else ""
    reference = reference_at(source, column)
    if reference is not None:
        return reference.suggestions(work.docs)
    fragment = fragment_at(document, line, column)
    if fragment is not None:
        return list(fragment.suggestions(work.docs))
    return path_suggestions(document, work.docs, work.root, line, column) or None


def _row(
    document: Document,
    line: int,
    source: str,
    *,
    snippets: bool,
) -> list[Suggestion] | None:
    if any(
        "grid" in block.meta and block.start <= line + 1 <= block.end
        for block in document.of_kind("table")
    ):
        return []
    row = row_suggestion(document, line, source, snippets=snippets)
    return [row] if row else None
