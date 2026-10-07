"""Windows Computer Helper：通过 JSON Lines 提供原生电脑操作。

使用 UI Automation 读取元素树、SendInput 合成输入、PrintWindow 截图。
模块在运行时加载 Windows 依赖，纯逻辑模块可用于离线测试。
"""

from __future__ import annotations

__all__ = ["HELPER_VERSION", "PROTOCOL_VERSION"]

HELPER_VERSION = "0.0.1"
PROTOCOL_VERSION = 1
