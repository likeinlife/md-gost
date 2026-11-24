"""Preserve manifest order when converting multiple chapters."""

from pathlib import Path

import pytest
from conftest import needs_pandoc
from test_helpers import ENCODING, build, snapshot

pytestmark = [needs_pandoc, pytest.mark.build]


def test_manifest_order_is_preserved(tmp_path: Path) -> None:
    (tmp_path / "book.toml").write_text(
        'output = "out.docx"\nchapters = ["z.md", "a.md"]\ntoc = false\n',
        encoding=ENCODING,
    )
    (tmp_path / "z.md").write_text("# Первая глава\n\nПервый текст.\n", encoding=ENCODING)
    (tmp_path / "a.md").write_text("# Вторая глава\n\nВторой текст.\n", encoding=ENCODING)
    completed_process = build(tmp_path)
    assert completed_process.returncode == 0, completed_process.stderr
    paragraphs = snapshot(tmp_path / "out.docx")["text"]
    assert paragraphs.index("Первая глава") < paragraphs.index("Вторая глава")
