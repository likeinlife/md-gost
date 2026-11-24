"""Read, update, and write frame-enabled docx packages."""

import stat
import tempfile
import zipfile
from pathlib import Path

from gost_builder.frame.constants import PART_DEFAULT, PART_FIRST
from gost_builder.frame.parts import add_content_types, add_relationships, ensure_styles
from gost_builder.frame.section_xml import edit_document
from gost_builder.frame.settings import FrameSettings


def read_package(docx: Path) -> dict[str, bytes]:
    """Read package."""
    with zipfile.ZipFile(docx) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def update_package(
    members: dict[str, bytes],
    settings: FrameSettings,
    headers: tuple[bytes, bytes],
) -> None:
    """Update package."""
    rels, rid_first, rid_default = add_relationships(members["word/_rels/document.xml.rels"])
    members["word/_rels/document.xml.rels"] = rels
    members["[Content_Types].xml"] = add_content_types(members["[Content_Types].xml"])
    members["word/styles.xml"] = ensure_styles(members["word/styles.xml"])
    members["word/document.xml"] = edit_document(
        members["word/document.xml"],
        rid_first,
        rid_default,
        int(settings["page_start"]),
    )
    _write_headers(members, headers)


def _write_headers(members: dict[str, bytes], headers: tuple[bytes, bytes]) -> None:
    members[PART_FIRST] = headers[0]
    members[PART_DEFAULT] = headers[1]


def write_package(docx: Path, members: dict[str, bytes]) -> None:
    """Write package."""
    with tempfile.TemporaryDirectory(dir=docx.parent) as directory:
        temp_path = Path(directory) / docx.name
        temp_path.touch(mode=stat.S_IRUSR | stat.S_IWUSR)
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, member_bytes in members.items():
                archive.writestr(name, member_bytes)
        temp_path.replace(docx)
