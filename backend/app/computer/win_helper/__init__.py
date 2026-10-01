"""Windows Computer Helper：长驻子进程，JSON Lines 协议（对齐 macOS 版）。

该子进程实现与 ``native/macos-computer-helper``（Swift）完全相同的协议与
安全语义（Session / Target / Observation 缓存 / freshness / 语义点击 /
输入验证），但底层改为 Windows 原生能力：

- 窗口与进程：Win32（``user32`` / ``kernel32``，经 pywin32 与 ctypes）；
- UI 元素树：UI Automation（``uiautomation``，等价于 macOS 的 AXUIElement）；
- 输入合成：``SendInput``（Unicode 文本 / 按键 / 鼠标，等价于 CGEvent）；
- 截图：``PrintWindow``（等价于 ScreenCaptureKit 的目标窗口截图）。

启动方式（由 backend bootstrap 负责）：``<venv python> -m app.computer.win_helper``，
stdin/stdout 使用 UTF-8 JSON Lines，stderr 为日志。

平台边界：本包整体仅 Windows 可用；非 Windows 平台上 import 本包不会崩溃
（重依赖都在函数内部延迟导入），但运行入口会直接报错退出。
"""

from __future__ import annotations

__all__ = ["HELPER_VERSION", "PROTOCOL_VERSION"]

HELPER_VERSION = "0.0.1"
PROTOCOL_VERSION = 1
