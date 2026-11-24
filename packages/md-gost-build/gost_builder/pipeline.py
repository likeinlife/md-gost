"""Build a document in manifest order from Markdown through final OOXML checks."""

import sys
import zipfile
from pathlib import Path

from gost_builder.errors import BuildError
from gost_builder.frame.document import add_frame
from gost_builder.lint import lint_docx, lint_markdown
from gost_builder.manifest import MANIFEST, load_manifest
from gost_builder.postprocess.document import postprocess
from gost_builder.render import render
from gost_builder.validation import preflight


def _verify(output: Path) -> None:
    sys.stdout.write("==> Verifying integrity\n")
    with zipfile.ZipFile(output) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            message = f"corrupt archive member: {damaged}"
            raise BuildError(message)
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    sys.stdout.write(f"OK: {output}\n    embedded media: {len(media)}\n")


def build(src: Path, *, lint_enabled: bool = True) -> Path:
    """Build the work in src and return the path to the verified DOCX."""
    src = src.resolve()
    if not src.is_dir():
        message = f"not a directory: {src}"
        raise BuildError(message)
    manifest = load_manifest(src)
    ready = preflight(src, manifest)
    if lint_enabled:
        lint_markdown(src, manifest.chapters)
    output = render(ready.pandoc, src, manifest, ready.plantuml)
    sys.stdout.write("==> Post-processing (styles, captions, tables)\n")
    postprocess(output, page_break_before_h1=manifest.page_break_before_h1)
    if manifest.frame:
        sys.stdout.write("==> Adding GOST frame (рамка + основная надпись)\n")
        add_frame(output, src / MANIFEST)
    lint_docx(output)
    _verify(output)
    sys.stdout.write(f"==> Done: {output}\n")
    return output
