"""Read and validate frame settings from book.toml."""

import sys
import tomllib
from pathlib import Path
from types import MappingProxyType

FrameSettings = dict[str, str | int]

DEFAULTS = MappingProxyType(
    {
        "author": "Иванов И.И.",
        "checker": "Петров П.П.",
        "title": "Отчет по учебной технологической (проектно-технологической) практике",
        "org": "ДГТУ, кафедра «ИТ»",
        "designation": "УП.280000.000",
        "sheets": "55",
        "first_sheet": "1",
        "page_start": 1,
    },
)


def load_params(manifest: Path) -> FrameSettings:
    """Load params."""
    with manifest.open("rb") as source_file:
        cfg = tomllib.load(source_file)
    frame = cfg.get("frame")
    frame_settings = dict(DEFAULTS)
    if isinstance(frame, dict):
        _warn_unknown_keys(frame)
        frame_settings.update(_known_frame_settings(frame))
    return frame_settings


def _warn_unknown_keys(frame: dict[str, str | int]) -> None:
    unknown = sorted(set(frame) - set(DEFAULTS))
    if unknown:
        keys = ", ".join(unknown)
        sys.stdout.write(f"add_frame: WARNING — ignoring unknown [frame] keys: {keys}\n")


def _known_frame_settings(frame: FrameSettings) -> FrameSettings:
    return {key: setting_value for key, setting_value in frame.items() if key in DEFAULTS}
