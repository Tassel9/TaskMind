"""Win32 底层封装：窗口 / 进程 / 前台激活 / 输入合成 / 应用启动。

仅 Windows 可用；重活全部经 ctypes 延迟获取（非 Windows 上 import 本模块
不会崩溃，但函数调用会抛 RuntimeError）。

设计约束（对齐 macOS helper 的对外语义）：
- 一切坐标都是**物理像素**（进程已设 Per-Monitor-V2 DPI 感知）；
- 输入合成使用 ``SendInput``（Unicode 文本 / 按键 / 鼠标），与 Python
  端契约中的 ``delivery_status`` 对应；
- 未知 / 失败路径返回 False 或 None，由上层翻译为结构化错误码。
"""

from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger("taskmind.computer.win_helper.winapi")

__all__ = [
    "AppLaunch",
    "WindowInfo",
    "click_screen_point",
    "ensure_dpi_awareness",
    "enum_top_level_windows",
    "get_foreground_window",
    "get_window_bounds",
    "get_window_pid",
    "get_window_title",
    "is_iconic",
    "is_window",
    "is_window_visible",
    "launch_app",
    "list_process_pids",
    "move_cursor",
    "process_alive",
    "process_exe_path",
    "send_key_combo",
    "send_mouse_wheel",
    "send_unicode_text",
    "set_foreground_window",
    "virtual_screen_rect",
    "window_info",
    "windows_of_pid",
]

_IS_WINDOWS = sys.platform == "win32"


def _require_windows() -> None:
    if not _IS_WINDOWS:  # pragma: no cover - 防御性
        raise RuntimeError("Windows computer helper requires Windows")


def _user32():  # noqa: ANN202 - ctypes 动态对象
    _require_windows()
    return ctypes.windll.user32


def _kernel32():  # noqa: ANN202
    _require_windows()
    return ctypes.windll.kernel32


# ---------------------------------------------------------------------------
# DPI
# ---------------------------------------------------------------------------


def ensure_dpi_awareness() -> bool:
    """把当前进程设为 Per-Monitor-V2 DPI 感知（幂等）。

    不设置的话，GetWindowRect / SendInput 会返回虚拟化坐标，导致
    截图坐标映射与实际点击位置不一致。
    """

    if not _IS_WINDOWS:  # pragma: no cover
        return False
    user32 = _user32()
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return True
    except (AttributeError, OSError):
        pass
    try:
        shcore = ctypes.windll.shcore
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        return shcore.SetProcessDpiAwareness(2) == 0
    except (AttributeError, OSError):
        return False


# ---------------------------------------------------------------------------
# 窗口
# ---------------------------------------------------------------------------


GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
SW_RESTORE = 9
SW_SHOW = 5
SW_SHOWNORMAL = 1


class WindowInfo(NamedTuple):
    hwnd: int
    title: str
    bounds: tuple[int, int, int, int]  # x, y, width, height（物理像素）
    pid: int


def is_window(hwnd: int) -> bool:
    return bool(hwnd) and bool(_user32().IsWindow(wintypes.HWND(hwnd)))


def is_window_visible(hwnd: int) -> bool:
    return bool(_user32().IsWindowVisible(wintypes.HWND(hwnd)))


def is_iconic(hwnd: int) -> bool:
    return bool(_user32().IsIconic(wintypes.HWND(hwnd)))


def get_window_title(hwnd: int) -> str:
    user32 = _user32()
    length = user32.GetWindowTextLengthW(wintypes.HWND(hwnd))
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(wintypes.HWND(hwnd), buf, length + 1)
    return buf.value


def get_window_bounds(hwnd: int) -> tuple[int, int, int, int] | None:
    rect = wintypes.RECT()
    if not _user32().GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        return None
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return None
    return (rect.left, rect.top, width, height)


def get_window_pid(hwnd: int) -> int:
    pid = wintypes.DWORD(0)
    _user32().GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return int(pid.value)


def window_info(hwnd: int) -> WindowInfo | None:
    bounds = get_window_bounds(hwnd)
    if bounds is None:
        return None
    return WindowInfo(
        hwnd=hwnd,
        title=get_window_title(hwnd),
        bounds=bounds,
        pid=get_window_pid(hwnd),
    )


def get_foreground_window() -> int:
    return int(_user32().GetForegroundWindow() or 0)


def _is_user_window(hwnd: int) -> bool:
    """过滤工具窗口：可见、非 WS_EX_TOOLWINDOW、尺寸有效。"""

    user32 = _user32()
    if not user32.IsWindowVisible(wintypes.HWND(hwnd)):
        return False
    ex_style = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE)
    if ex_style & WS_EX_TOOLWINDOW:
        return False
    return get_window_bounds(hwnd) is not None


def enum_top_level_windows() -> list[WindowInfo]:
    """枚举可见顶层用户窗口，按 Z 序（前台在前）。"""

    _require_windows()
    result: list[WindowInfo] = []
    user32 = _user32()
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _callback(hwnd: int, _lparam: int) -> bool:
        if _is_user_window(hwnd):
            info = window_info(hwnd)
            if info is not None:
                result.append(info)
        return True

    user32.EnumWindows(EnumProc(_callback), 0)
    return result


def windows_of_pid(pid: int) -> list[WindowInfo]:
    """目标进程的可见顶层窗口（Z 序）。"""

    return [info for info in enum_top_level_windows() if info.pid == pid]


def virtual_screen_rect() -> tuple[int, int, int, int]:
    """虚拟屏幕（所有显示器）矩形：x, y, width, height。"""

    user32 = _user32()
    SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
    SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
    return (
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


def set_foreground_window(hwnd: int) -> bool:
    """把窗口带到前台（best effort，含 AttachThreadInput 兜底）。

    Windows 前台锁（foreground lock）会让后台进程的 SetForegroundWindow
    静默失败；先附加到当前前台线程的输入队列再设置，可显著提高成功率。
    """

    _require_windows()
    if not is_window(hwnd):
        return False
    user32 = _user32()
    if get_foreground_window() == hwnd:
        return True
    if is_iconic(hwnd):
        user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)

    kernel32 = _kernel32()
    fg = get_foreground_window()
    fg_thread = (
        user32.GetWindowThreadProcessId(wintypes.HWND(fg), None) if fg else 0
    )
    cur_thread = kernel32.GetCurrentThreadId()
    attached = False
    if fg_thread and fg_thread != cur_thread:
        attached = bool(
            user32.AttachThreadInput(cur_thread, fg_thread, True)
        )
    try:
        user32.ShowWindow(wintypes.HWND(hwnd), SW_SHOW)
        ok = bool(user32.SetForegroundWindow(wintypes.HWND(hwnd)))
        if not ok:
            user32.BringWindowToTop(wintypes.HWND(hwnd))
            ok = get_foreground_window() == hwnd
    finally:
        if attached:
            user32.AttachThreadInput(cur_thread, fg_thread, False)
    return ok or get_foreground_window() == hwnd


# ---------------------------------------------------------------------------
# 进程
# ---------------------------------------------------------------------------

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def process_alive(pid: int) -> bool:
    if not pid:
        return False
    handle = _kernel32().OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, pid
    )
    if handle:
        _kernel32().CloseHandle(handle)
        return True
    return False


def process_exe_path(pid: int) -> str | None:
    """进程可执行文件完整路径（等价于 macOS 的 bundle 身份）。

    失败（权限不足 / 系统进程）返回 None。
    """

    if not pid:
        return None
    kernel32 = _kernel32()
    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, pid
    )
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(
            handle, 0, buf, ctypes.byref(size)
        ):
            return buf.value
        return None
    finally:
        kernel32.CloseHandle(handle)


def process_exe_name(pid: int) -> str | None:
    path = process_exe_path(pid)
    if not path:
        return None
    return os.path.basename(path)


def list_process_pids() -> list[int]:
    _require_windows()
    psapi = ctypes.WinDLL("psapi.dll")
    capacity = 2048
    while capacity <= 32768:
        arr = (wintypes.DWORD * capacity)()
        needed = wintypes.DWORD(0)
        if not psapi.EnumProcesses(
            arr, ctypes.sizeof(arr), ctypes.byref(needed)
        ):
            return []
        count = needed.value // ctypes.sizeof(wintypes.DWORD)
        if count < capacity:
            return [int(arr[i]) for i in range(count) if arr[i]]
        capacity *= 2
    return []


# ---------------------------------------------------------------------------
# 输入合成（SendInput）
# ---------------------------------------------------------------------------

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

WHEEL_DELTA = 120

_ULONG_PTR = (
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
)


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _send_inputs(inputs: list[_INPUT]) -> bool:
    """批量发送 INPUT 事件；数量不符（被 UIPI 拦截等）返回 False。"""

    if not inputs:
        return True
    user32 = _user32()
    array = (_INPUT * len(inputs))(*inputs)
    sent = user32.SendInput(
        len(inputs), ctypes.byref(array), ctypes.sizeof(_INPUT)
    )
    if sent != len(inputs):
        logger.warning(
            "SendInput delivered %s/%s events (input blocked?)",
            sent,
            len(inputs),
        )
        return False
    return True


def _key_event(
    vk: int,
    *,
    scan: int = 0,
    down: bool,
    unicode_mode: bool = False,
    extended: bool = False,
) -> _INPUT:
    flags = 0
    if unicode_mode:
        flags |= KEYEVENTF_UNICODE
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if not down:
        flags |= KEYEVENTF_KEYUP
    item = _INPUT(type=INPUT_KEYBOARD)
    item.ki = _KEYBDINPUT(
        wVk=0 if unicode_mode else vk,
        wScan=scan,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    return item


def send_unicode_text(
    text: str, chunk_units: int = 20, inter_chunk_sleep: float = 0.02
) -> bool:
    """发送 Unicode 文本（KEYEVENTF_UNICODE），UTF-16 分块（对齐 macOS 版）。

    每个 code unit 一对 down/up；代理对（emoji 等）作为连续 code unit
    自然成对投递。空字符串不产生任何事件。

    分块刻意保持较小（默认 20 code units）并在批间留出短暂间隔：
    实测目标应用（WinForms TextBox 等）在单批事件过多时会丢尾部字符。
    """

    if not text:
        return True
    units = text.encode("utf-16-le")
    code_units = [
        int.from_bytes(units[i : i + 2], "little")
        for i in range(0, len(units), 2)
    ]
    for start in range(0, len(code_units), chunk_units):
        chunk = code_units[start : start + chunk_units]
        events: list[_INPUT] = []
        for unit in chunk:
            events.append(
                _key_event(0, scan=unit, down=True, unicode_mode=True)
            )
            events.append(
                _key_event(0, scan=unit, down=False, unicode_mode=True)
            )
        if not _send_inputs(events):
            return False
        time.sleep(inter_chunk_sleep)
    return True


def send_key_combo(vk: int, modifier_vks: list[int], *, extended: bool = False) -> bool:
    """发送按键组合：modifier 按下（正序）→ 键 down/up → modifier 释放（逆序）。"""

    events: list[_INPUT] = []
    for mod in modifier_vks:
        events.append(_key_event(mod, down=True, extended=False))
    events.append(_key_event(vk, down=True, extended=extended))
    events.append(_key_event(vk, down=False, extended=extended))
    for mod in reversed(modifier_vks):
        events.append(_key_event(mod, down=False, extended=False))
    return _send_inputs(events)


def _absolute_coords(x: int, y: int) -> tuple[int, int]:
    """物理像素坐标 → 虚拟桌面 0..65535 归一化坐标。"""

    vx, vy, vw, vh = virtual_screen_rect()
    if vw <= 1 or vh <= 1:
        return 0, 0
    norm_x = round((x - vx) * 65535 / (vw - 1))
    norm_y = round((y - vy) * 65535 / (vh - 1))
    return norm_x, norm_y


def _mouse_move_event(x: int, y: int) -> _INPUT:
    norm_x, norm_y = _absolute_coords(x, y)
    item = _INPUT(type=INPUT_MOUSE)
    item.mi = _MOUSEINPUT(
        dx=norm_x,
        dy=norm_y,
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        time=0,
        dwExtraInfo=0,
    )
    return item


def move_cursor(x: int, y: int) -> bool:
    return _send_inputs([_mouse_move_event(x, y)])


def click_screen_point(x: int, y: int) -> bool:
    """绝对坐标左键单击（物理像素，虚拟桌面归一化）。"""

    move = _mouse_move_event(x, y)
    down = _INPUT(type=INPUT_MOUSE)
    down.mi = _MOUSEINPUT(
        dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTDOWN,
        time=0, dwExtraInfo=0,
    )
    up = _INPUT(type=INPUT_MOUSE)
    up.mi = _MOUSEINPUT(
        dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTUP,
        time=0, dwExtraInfo=0,
    )
    return _send_inputs([move, down, up])


def send_mouse_wheel(*, clicks: int, horizontal: bool = False) -> bool:
    """滚轮事件：clicks 为正=上/右，负=下/左（每档 WHEEL_DELTA）。"""

    if clicks == 0:
        return True
    item = _INPUT(type=INPUT_MOUSE)
    item.mi = _MOUSEINPUT(
        dx=0,
        dy=0,
        mouseData=ctypes.c_uint32(clicks * WHEEL_DELTA).value,
        dwFlags=MOUSEEVENTF_HWHEEL if horizontal else MOUSEEVENTF_WHEEL,
        time=0,
        dwExtraInfo=0,
    )
    return _send_inputs([item])


# ---------------------------------------------------------------------------
# 应用启动
# ---------------------------------------------------------------------------


class AppLaunch(NamedTuple):
    pid: int | None
    exe: str | None
    method: str  # "create_process" / "shell_execute"
    window_hwnd: int | None = None


_APP_PATHS_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"

_PE_SUBSYSTEM_GUI = 2
_PE_SUBSYSTEM_CONSOLE = 3


def _pe_subsystem(path: str) -> int | None:
    """读取 PE OptionalHeader.Subsystem（2=GUI，3=Console）。

    控制台应用（cmd / powershell 等）不能用 DETACHED_PROCESS 启动：
    没有控制台会直接退出；GUI 应用则用 DETACHED_PROCESS 避免附着宿主控制台。
    """

    try:
        with open(path, "rb") as fh:
            if fh.read(2) != b"MZ":
                return None
            fh.seek(0x3C)
            offset = int.from_bytes(fh.read(4), "little")
            fh.seek(offset)
            if fh.read(4) != b"PE\x00\x00":
                return None
            fh.seek(offset + 0x18 + 0x44)
            return int.from_bytes(fh.read(2), "little")
    except OSError:
        return None


def _resolve_app_paths(app: str) -> str | None:
    """注册表 App Paths 解析（等价于 macOS 的 LaunchServices 名称解析）。"""

    try:
        import winreg
    except ImportError:  # pragma: no cover - 非 Windows
        return None
    name = app if app.lower().endswith(".exe") else f"{app}.exe"
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for subkey in (name,):
            try:
                with winreg.OpenKey(root, f"{_APP_PATHS_KEY}\\{subkey}") as key:
                    value, _ = winreg.QueryValueEx(key, None)
                    if value and Path(value).is_file():
                        return str(value)
            except OSError:
                continue
    return None


def _looks_like_shell_target(app: str) -> bool:
    """判断是否 shell 协议/文档目标（ms-settings:、https://、C:\\ 之外）。"""

    if len(app) > 1 and app[1] == ":" and app[0].isalpha():
        return False  # 盘符路径
    if ":" in app:
        return True
    return False


def _resolve_exe(app: str) -> str | None:
    """app → 可执行文件路径；解析不了返回 None。"""

    candidate = Path(app).expanduser()
    if candidate.is_file() and candidate.suffix.lower() == ".exe":
        return str(candidate)
    if candidate.is_file():
        return None  # 文档 / 快捷方式 → 走 shell
    found = shutil.which(app)
    if found is None and not app.lower().endswith(".exe"):
        found = shutil.which(f"{app}.exe")
    if found:
        return found
    return _resolve_app_paths(app)


def _shell_execute(target: str) -> bool:
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "open", target, None, None, SW_SHOWNORMAL
    )
    return int(result) > 32


def _wait_for_new_window(
    before_hwnds: set[int],
    expected_name: str | None,
    timeout: float,
    *,
    process_pid: int | None = None,
) -> WindowInfo | None:
    """等待出现属于目标应用的新窗口，返回窗口信息（找不到返回 None）。

    匹配优先级：
    1. 窗口进程 == 启动进程（原生应用）；
    2. 窗口进程 exe 名 == 目标 exe（Packaged App 由系统激活）；
    3. 任意新出现的顶层用户窗口（共享宿主场景：cmd 由 Windows Terminal
       承载、Win11 记事本多窗口共享进程等——窗口进程与目标进程都不同）。

    第 3 级是兜底：hwnd 是启动前后的差集，误绑概率低；只有在前两级
    超时都未命中时才使用。
    """

    deadline = time.monotonic() + timeout
    fallback: WindowInfo | None = None
    expected = expected_name.lower() if expected_name else None
    while time.monotonic() < deadline:
        for info in enum_top_level_windows():
            if info.hwnd in before_hwnds:
                continue
            if process_pid is not None and info.pid == process_pid:
                return info
            if expected is not None:
                exe = process_exe_name(info.pid)
                if exe and exe.lower() == expected:
                    return info
            if fallback is None:
                fallback = info
        time.sleep(0.15)
    return fallback


def launch_app(app: str) -> AppLaunch:
    """启动应用（exe / 文档 / shell 协议），尽量返回窗口进程 pid。

    找不到可解析目标时抛 FileNotFoundError，由上层翻译为 app_not_found。
    """

    _require_windows()
    exe = None
    if not _looks_like_shell_target(app):
        exe = _resolve_exe(app)
    before_hwnds = {info.hwnd for info in enum_top_level_windows()}
    if exe is not None:
        if _pe_subsystem(exe) == _PE_SUBSYSTEM_CONSOLE:
            flags = (
                subprocess.CREATE_NEW_CONSOLE
                | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            flags = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        process = subprocess.Popen(  # noqa: S603 - 目标由本地解析得出
            [exe],
            close_fds=True,
            creationflags=flags,
        )
        expected = os.path.basename(exe).lower()
        window = _wait_for_new_window(
            before_hwnds, expected, timeout=3.0, process_pid=process.pid
        )
        return AppLaunch(
            pid=window.pid if window else process.pid,
            exe=exe,
            method="create_process",
            window_hwnd=window.hwnd if window else None,
        )

    # shell execute：文档 / 协议 / 未解析到的名字。
    if not _shell_execute(app):
        raise FileNotFoundError(app)
    expected = None
    candidate = Path(app)
    if candidate.suffix.lower() == ".exe":
        expected = candidate.name.lower()
    window = _wait_for_new_window(before_hwnds, expected, timeout=5.0)
    pid = window.pid if window else None
    resolved_exe = process_exe_path(pid) if pid else None
    return AppLaunch(
        pid=pid,
        exe=resolved_exe,
        method="shell_execute",
        window_hwnd=window.hwnd if window else None,
    )
