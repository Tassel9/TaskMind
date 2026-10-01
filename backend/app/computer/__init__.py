"""Computer Runtime：目标绑定的屏幕观察、交互与跨平台原生实现。

本轮提供：
- ``models``：Observation / ElementTarget / CoordinateTarget / ActionResult；
- ``runtime``：ComputerRuntime 异步接口（Protocol）；
- ``fake``：FakeComputerRuntime（供 Agent Tool 离线单测使用）；
- ``tools``：computer_observe / click / type / key / scroll / open_app /
  focus_window 七个 Agent 工具 + ``register_computer_tools``；
- ``helper_client``：MacOSHelperClient（Python ↔ helper 子进程的 JSON Lines
  长驻客户端；macOS / Windows 共用）；
- ``macos``：MacOSComputerRuntime（协议映射层，本身无平台逻辑）；
- ``win_helper``：Windows helper 实现（UIAutomation / SendInput /
  PrintWindow），以 ``<python> -m app.computer.win_helper`` 启动。
"""

from .bootstrap import (
    ComputerHostStatus,
    build_computer,
    build_macos_computer,
    build_windows_computer,
    computer_enabled,
    current_platform,
    resolve_helper_path,
)
from .fake import FakeComputerRuntime, default_observation
from .helper_client import (
    ComputerHelperError,
    ComputerHelperProcessError,
    ComputerHelperProtocolError,
    MacOSHelperClient,
)
from .lease import (
    ComputerBusyError,
    ComputerLeaseHook,
    ComputerLeaseManager,
    ComputerLeaseSnapshot,
)
from .macos import MacOSComputerRuntime
from .models import (
    ActionName,
    ActionResult,
    ActiveApp,
    Bounds,
    CoordinateTarget,
    DeliveryStatus,
    Element,
    ElementStats,
    ElementTarget,
    Observation,
    Target,
    VerificationStatus,
    Window,
)
from .runtime import ComputerRuntime
from .session import (
    ComputerSession,
    ComputerSessionError,
    ComputerSessionManager,
    ComputerSessionMismatchError,
    ComputerSessionNotActiveError,
)
from .tools import (
    ComputerClickTool,
    ComputerFocusWindowTool,
    ComputerKeyTool,
    ComputerObserveTool,
    ComputerOpenAppTool,
    ComputerScrollTool,
    ComputerTypeTool,
    register_computer_tools,
)

__all__ = [
    "ActionName",
    "ActionResult",
    "ActiveApp",
    "Bounds",
    "ComputerBusyError",
    "ComputerClickTool",
    "ComputerFocusWindowTool",
    "ComputerHelperError",
    "ComputerHelperProcessError",
    "ComputerHelperProtocolError",
    "ComputerHostStatus",
    "ComputerKeyTool",
    "ComputerLeaseHook",
    "ComputerLeaseManager",
    "ComputerLeaseSnapshot",
    "ComputerObserveTool",
    "ComputerOpenAppTool",
    "ComputerRuntime",
    "ComputerScrollTool",
    "ComputerSession",
    "ComputerSessionError",
    "ComputerSessionManager",
    "ComputerSessionMismatchError",
    "ComputerSessionNotActiveError",
    "ComputerTypeTool",
    "CoordinateTarget",
    "DeliveryStatus",
    "Element",
    "ElementStats",
    "ElementTarget",
    "FakeComputerRuntime",
    "MacOSComputerRuntime",
    "MacOSHelperClient",
    "Observation",
    "Target",
    "VerificationStatus",
    "Window",
    "build_computer",
    "build_macos_computer",
    "build_windows_computer",
    "computer_enabled",
    "current_platform",
    "default_observation",
    "register_computer_tools",
    "resolve_helper_path",
]
