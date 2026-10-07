"""目标窗口截图：PrintWindow 优先，桌面裁剪兜底。

截图像素坐标映射为屏幕物理坐标，越界请求明确拒绝。
"""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from pathlib import Path

from . import windows_api
from .png import encode_png_from_bgra

logger = logging.getLogger("taskmind.computer.win_helper.capture")

__all__ = ["CaptureResult", "ScreenshotMapping", "capture_window_screenshot"]

PW_RENDERFULLCONTENT = 2
SRCCOPY = 0x00CC0020


@dataclass(frozen=True)
class ScreenshotMapping:
    pixel_width: int
    pixel_height: int
    x: int
    y: int
    width: int
    height: int

    def global_point(self, x: int, y: int) -> tuple[float, float] | None:
        """截图坐标 → 屏幕物理坐标；越界返回 None。"""

        if (
            self.pixel_width <= 0
            or self.pixel_height <= 0
            or x < 0
            or y < 0
            or x >= self.pixel_width
            or y >= self.pixel_height
        ):
            return None
        return (
            self.x + x * self.width / self.pixel_width,
            self.y + y * self.height / self.pixel_height,
        )


@dataclass(frozen=True)
class CaptureResult:
    png_path: str
    mapping: ScreenshotMapping


class CaptureError(RuntimeError):
    """截图失败（结构化 code 由 handlers 翻译进 screenshot_error）。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _looks_blank(bits: bytes, sample_count: int = 64) -> bool:
    """采样检查是否全黑（PrintWindow 对部分窗口返回黑图）。"""

    if not bits:
        return True
    total = len(bits)
    step = max(4, total // sample_count // 4 * 4)
    non_blank = False
    for offset in range(0, total - 3, step):
        if bits[offset] or bits[offset + 1] or bits[offset + 2]:
            non_blank = True
            break
    return not non_blank


def _capture_via_printwindow(
    hwnd: int, width: int, height: int
) -> bytes | None:
    """PrintWindow 抓取；返回 BGRA bottom-up 数据或 None。"""

    import win32gui  # noqa: PLC0415 - Windows-only，延迟导入
    import win32ui  # noqa: PLC0415

    hwnd_dc = None
    mfc_dc = None
    save_dc = None
    bitmap = None
    try:
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        ok = ctypes.windll.user32.PrintWindow(
            hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT
        )
        if not ok:
            return None
        bits = bitmap.GetBitmapBits(True)
        if _looks_blank(bits):
            return None
        return bits
    except Exception:  # noqa: BLE001 - GDI 失败统一走 fallback
        logger.exception("PrintWindow capture failed for hwnd=%s", hwnd)
        return None
    finally:
        try:
            if bitmap is not None:
                win32gui.DeleteObject(bitmap.GetHandle())
            if save_dc is not None:
                save_dc.DeleteDC()
            if mfc_dc is not None:
                mfc_dc.DeleteDC()
            if hwnd_dc is not None:
                win32gui.ReleaseDC(hwnd, hwnd_dc)
        except Exception:  # noqa: BLE001
            logger.debug("GDI cleanup issue for hwnd=%s", hwnd, exc_info=True)


def _capture_via_desktop(
    x: int, y: int, width: int, height: int
) -> bytes | None:
    """桌面 DC 裁剪（窗口必须处于可见状态；被遮挡时会拍到遮挡内容）。"""

    import win32con  # noqa: PLC0415
    import win32gui  # noqa: PLC0415
    import win32ui  # noqa: PLC0415

    desktop_dc = None
    mfc_dc = None
    save_dc = None
    bitmap = None
    try:
        desktop_dc = win32gui.GetWindowDC(0)
        mfc_dc = win32ui.CreateDCFromHandle(desktop_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (x, y), win32con.SRCCOPY)
        return bitmap.GetBitmapBits(True)
    except Exception:  # noqa: BLE001
        logger.exception("desktop capture failed")
        return None
    finally:
        try:
            if bitmap is not None:
                win32gui.DeleteObject(bitmap.GetHandle())
            if save_dc is not None:
                save_dc.DeleteDC()
            if mfc_dc is not None:
                mfc_dc.DeleteDC()
            if desktop_dc is not None:
                win32gui.ReleaseDC(0, desktop_dc)
        except Exception:  # noqa: BLE001
            logger.debug("GDI cleanup issue (desktop)", exc_info=True)


def capture_window_screenshot(
    hwnd: int, output_path: str
) -> CaptureResult:
    """抓取目标窗口并写入 PNG；失败抛 ``CaptureError``。

    - 窗口最小化时无法截图（不改变窗口状态）；
    - PrintWindow 全黑 / 失败时回退桌面裁剪。
    """

    if not windows_api.is_window(hwnd):
        raise CaptureError("screenshot_capture_failed", "window is gone")
    if windows_api.is_iconic(hwnd):
        raise CaptureError(
            "screenshot_capture_failed", "window is minimized"
        )
    bounds = windows_api.get_window_bounds(hwnd)
    if bounds is None:
        raise CaptureError("screenshot_capture_failed", "invalid window bounds")
    x, y, width, height = bounds

    bits = _capture_via_printwindow(hwnd, width, height)
    if bits is None:
        bits = _capture_via_desktop(x, y, width, height)
    if bits is None:
        raise CaptureError(
            "screenshot_capture_failed", "no capture backend succeeded"
        )

    png_bytes = encode_png_from_bgra(width, height, bits)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes)

    return CaptureResult(
        png_path=str(path),
        mapping=ScreenshotMapping(
            pixel_width=width,
            pixel_height=height,
            x=x,
            y=y,
            width=width,
            height=height,
        ),
    )
