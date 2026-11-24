"""Apply GOST typography and page geometry to the Pandoc reference template."""

import sys
import zipfile
from pathlib import Path

from docx import Document

from gost_builder.reference.constants import FONT, THEME_PART
from gost_builder.reference.styles import apply_styles


def patch_theme(path: Path) -> None:
    """Rewrite the theme's Aptos font bindings to TNR.

    Members are rewritten in their original archive order (the OPC spec wants
    [Content_Types].xml first) and the whole thing is done in memory, so a
    failure cannot leave a half-extracted temp directory behind.
    """
    members = _read_theme_members(path)
    patched = [_patch_theme_member(name, payload) for name, payload in members]
    _write_theme(path, patched)


def _read_theme_members(path: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as archive:
        return [(entry.filename, archive.read(entry.filename)) for entry in archive.infolist()]


def _patch_theme_member(name: str, payload: bytes) -> tuple[str, bytes]:
    if name != THEME_PART:
        return name, payload
    xml = payload.decode("utf-8")
    xml = xml.replace('typeface="Aptos Display"', f'typeface="{FONT}"')
    xml = xml.replace('typeface="Aptos"', f'typeface="{FONT}"')
    return name, xml.encode("utf-8")


def _write_theme(path: Path, members: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members:
            archive.writestr(name, payload)


def style_reference(path: Path) -> None:
    """Apply GOST styles and fonts to the reference template in place."""
    doc = Document(str(path))
    apply_styles(doc)
    doc.save(str(path))
    patch_theme(path)
    sys.stdout.write(f"GOST reference.docx written: {path}\n")
