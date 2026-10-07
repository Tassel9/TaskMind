"""Windows Computer Runtime：屏幕观察、目标绑定、交互与 helper 通信。

ComputerHelperClient 管理 JSON Lines 传输；ComputerHelperRuntime 映射
ComputerRuntime 契约；win_helper 调用 UI Automation、SendInput 和 PrintWindow。
"""

from .bootstrap import (
    ComputerHostStatus,
    build_computer,
    build_windows_computer,
    computer_enabled,
    current_platform,
)
from .fake import FakeComputerRuntime, default_observation
from .helper_client import (
    ComputerHelperClient,
    ComputerHelperError,
    ComputerHelperProcessError,
    ComputerHelperProtocolError,
)
from .helper_runtime import ComputerHelperRuntime
from .lease import (
    ComputerBusyError,
    ComputerLeaseHook,
    ComputerLeaseManager,
    ComputerLeaseSnapshot,
)
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
    "ComputerHelperRuntime",
    "ComputerHelperClient",
    "Observation",
    "Target",
    "VerificationStatus",
    "Window",
    "build_computer",
    "build_windows_computer",
    "computer_enabled",
    "current_platform",
    "default_observation",
    "register_computer_tools",
]
