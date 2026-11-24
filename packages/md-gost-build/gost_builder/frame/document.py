"""Apply the configured GOST frame to the main-text sections of a Word document."""

import sys
from pathlib import Path

from gost_builder.frame.archive import read_package, update_package, write_package
from gost_builder.frame.headers import build_headers
from gost_builder.frame.settings import load_params


def add_frame(path: Path, manifest: Path) -> None:
    """Insert the frame and its stamp fields using settings from book.toml."""
    settings = load_params(manifest)
    headers = build_headers(settings)
    members = read_package(path)
    update_package(members, settings, headers)
    write_package(path, members)
    sys.stdout.write(f"frame added: {path}\n")
