"""Common data and byte-level utilities for md-to-gost tests."""

import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

TOOL = Path(__file__).resolve().parents[1]
ENTRY_POINT = TOOL / "md_to_gost.py"
EXAMPLE = TOOL.parents[1] / "example"
GOLDEN = Path(__file__).resolve().parent / "golden.json"
ENCODING = "utf-8"
NO_LINT = "--no-lint"
MANIFEST = 'output = "out.docx"\nchapters = ["CHAPTER_1.md"]\n'
W_T = re.compile(r"<w:t[^>]*>([^<]*)</w:t>")
P_STYLE = re.compile(r'<w:pStyle w:val="([^"]+)"/>')
Run = subprocess.CompletedProcess[str]


def build(src: Path, *, lint: bool = False) -> Run:
    """Build a directory. Linting is off by default."""
    return subprocess.run(
        _build_args(src, lint=lint),
        capture_output=True,
        text=True,
        check=False,
    )


def _build_args(src: Path, *, lint: bool) -> list[str]:
    args = [sys.executable, str(ENTRY_POINT)]
    if not lint:
        args.append(NO_LINT)
    args.append(str(src))
    return args


def snapshot(docx: Path) -> dict[str, Any]:
    """Deterministic view of a built document (the raw zip bytes are not)."""
    archive = zipfile.ZipFile(docx)
    document = archive.read("word/document.xml").decode(ENCODING)
    snap: dict[str, Any] = {
        "text": W_T.findall(document),
        "pstyles": P_STYLE.findall(document),
        "media_count": len([name for name in archive.namelist() if name.startswith("word/media/")]),
    }
    for part in ("word/header_frame1.xml", "word/header_frame2.xml"):
        if part in archive.namelist():
            found = W_T.findall(archive.read(part).decode(ENCODING))
            snap[part] = [target for target in found if target.strip()]
    return snap
