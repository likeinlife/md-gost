"""Generate small grayscale PNG fixtures using only the standard library."""

import struct
import zlib
from pathlib import Path

GRAY_MAX = 255
CRC_MASK = 0xFFFFFFFF
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def make_png(path: Path, width: int, height: int) -> None:
    raw = _png_rows(width, height)
    header = _png_header(width, height)
    image_data = _png_chunk(b"IDAT", zlib.compress(raw, 6))
    ending = _png_chunk(b"IEND", b"")
    path.write_bytes(PNG_SIGNATURE + header + image_data + ending)


def _png_header(width: int, height: int) -> bytes:
    header_data = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return _png_chunk(b"IHDR", header_data)


def _png_rows(width: int, height: int) -> bytes:
    return b"".join(_png_row(width, height, row) for row in range(height))


def _png_row(width: int, height: int, row: int) -> bytes:
    shade = (row * GRAY_MAX) // height
    return bytes((0, *(shade for _ in range(width))))


def _png_chunk(tag: bytes, member_bytes: bytes) -> bytes:
    checksum = zlib.crc32(tag + member_bytes) & CRC_MASK
    length = struct.pack(">I", len(member_bytes))
    crc = struct.pack(">I", checksum)
    return length + tag + member_bytes + crc
