"""Labels, cross-references and bibliography.

Some of this the build also checks, but it dies on the first failure and
without a line number. Here everything is reported at once, before pandoc
is even started.
"""

from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.adjacent_blocks import with_next
from gost_lint.rules.registry import rule

FileIssue = Iterator[tuple[int, int, str]]


@rule("REF002", "error", "маркер подписи оторван от таблицы")
def marker_not_before_table(doc: Document) -> FileIssue:
    """Handle marker not before table."""
    blocks = [block for block in doc.blocks if block.kind != "comment"]
    for block, following in with_next(blocks):
        if block.kind != "table_marker":
            continue
        if following is None or following.kind != "table":
            yield (
                block.start,
                1,
                (
                    f"между маркером {block.meta['label']} и таблицей есть "
                    f"другой блок — подпись уедет к следующей таблице"
                ),
            )
