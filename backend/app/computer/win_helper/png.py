"""PNG 编码（纯标准库：zlib + struct），避免引入 Pillow 等额外依赖。

只实现截图链路需要的子集：8-bit RGB、无滤波、单个 IDAT。
"""

from __future__ import annotations

import struct
import zlib

__all__ = ["encode_png_from_bgra", "encode_png_rgb"]


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def encode_png_rgb(width: int, height: int, rgb_rows: list[bytes]) -> bytes:
    """从 top-down RGB 行编码 PNG。``rgb_rows`` 每行长度必须为 width*3。"""

    if width <= 0 or height <= 0 or len(rgb_rows) != height:
        raise ValueError("invalid PNG dimensions / row count")
    stride = width * 3
    for row in rgb_rows:
        if len(row) != stride:
            raise ValueError("row size mismatch")
    raw = b"".join(b"\x00" + row for row in rgb_rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(
            b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        )
        + _chunk(b"IDAT", zlib.compress(raw, 3))
        + _chunk(b"IEND", b"")
    )


def encode_png_from_bgra(width: int, height: int, bits: bytes) -> bytes:
    """从 Win32 位图数据（BGRA，top-down 行序）编码 PNG。

    注意：pywin32 ``GetBitmapBits`` 实测返回 **top-down** 行序
    （首行即图像顶部），因此这里不做任何行翻转；曾按 DIB 惯例
    （bottom-up）倒序导致截图上下颠倒。
    """

    if width <= 0 or height <= 0:
        raise ValueError("invalid PNG dimensions")
    stride = width * 4
    if len(bits) < stride * height:
        raise ValueError("bitmap buffer too small")
    rows: list[bytes] = []
    for y in range(height):  # top-down：首行即图像顶部
        source = bits[y * stride : (y + 1) * stride]
        rgb = bytearray(width * 3)
        rgb[0::3] = source[2::4]
        rgb[1::3] = source[1::4]
        rgb[2::3] = source[0::4]
        rows.append(bytes(rgb))
    return encode_png_rgb(width, height, rows)
