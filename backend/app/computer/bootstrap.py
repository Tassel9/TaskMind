"""Windows Computer bootstrap：解释器解析、依赖检查与运行时装配。

解释器优先级：显式参数 > TASKMIND_WIN_HELPER_PYTHON > 当前进程解释器。
Computer 不可用或被关闭时，Host 的其他功能仍可运行。
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .helper_client import ComputerHelperClient
from .helper_runtime import ComputerHelperRuntime
from .runtime import ComputerRuntime

logger = logging.getLogger("taskmind.computer.bootstrap")

# backend/app/computer/bootstrap.py → backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_COMPUTER_ENABLED = "TASKMIND_COMPUTER_ENABLED"
ENV_WIN_HELPER_PYTHON = "TASKMIND_WIN_HELPER_PYTHON"

#: Windows helper 的运行依赖（import spec 名）。
_WIN_HELPER_MODULES = ("uiautomation", "win32gui", "win32ui")


@dataclass(frozen=True, slots=True)
class ComputerHostStatus:
    """Computer Host 的轻量状态（不持久化，仅供 UI / 日志）。"""

    enabled: bool
    available: bool
    platform: str
    reason: str | None = None
    helper_path: str | None = None
    runtime: str | None = None


def current_platform() -> str:
    return sys.platform


def _is_executable(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False




def computer_enabled(enabled: bool | None = None) -> bool:
    """Computer 开关：显式参数 > TASKMIND_COMPUTER_ENABLED > 默认启用。

    默认启用；运行时是否可用由平台与依赖检查决定。
    """

    if enabled is not None:
        return enabled
    raw = os.environ.get(ENV_COMPUTER_ENABLED, "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return True




def _windows_helper_missing_modules() -> list[str]:
    """检查 Windows helper 运行依赖是否可用（缺失时 Computer 不可用）。"""

    missing: list[str] = []
    for module in _WIN_HELPER_MODULES:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def build_windows_computer(
    *,
    helper_path: str | Path | None = None,
    enabled: bool | None = None,
) -> tuple[ComputerRuntime | None, ComputerHostStatus]:
    """构建 Windows Computer Runtime（Python helper）；不可用时返回
    (None, unavailable status)。

    ``helper_path``：Windows 下表示 helper 的 Python 解释器（缺省用当前
    进程解释器，即 backend venv）。
    """

    platform = current_platform()
    is_enabled = computer_enabled(enabled)

    if not is_enabled:
        status = ComputerHostStatus(
            enabled=False,
            available=False,
            platform=platform,
            reason="disabled",
        )
        logger.info("Computer disabled; %s", status)
        return None, status

    if platform != "win32":
        status = ComputerHostStatus(
            enabled=True,
            available=False,
            platform=platform,
            reason="unsupported_platform",
        )
        logger.info("Computer unavailable on platform %s", platform)
        return None, status

    missing = _windows_helper_missing_modules()
    if missing:
        status = ComputerHostStatus(
            enabled=True,
            available=False,
            platform=platform,
            reason="helper_dependency_missing",
        )
        logger.info(
            "Windows computer helper dependencies missing: %s",
            ", ".join(missing),
        )
        return None, status

    interpreter = (
        helper_path
        or os.environ.get(ENV_WIN_HELPER_PYTHON)
        or sys.executable
    )
    python_path = Path(interpreter).expanduser()
    if not _is_executable(python_path):
        status = ComputerHostStatus(
            enabled=True,
            available=False,
            platform=platform,
            reason="helper_not_found",
        )
        logger.info(
            "Windows helper interpreter not found: %s", interpreter
        )
        return None, status

    client = ComputerHelperClient(
        python_path,
        helper_args=("-m", "app.computer.win_helper"),
        cwd=_BACKEND_ROOT,
    )
    runtime = ComputerHelperRuntime(client)
    status = ComputerHostStatus(
        enabled=True,
        available=True,
        platform=platform,
        reason=None,
        helper_path=f"{python_path} -m app.computer.win_helper",
        runtime="windows",
    )
    logger.info("Computer Runtime: Windows available (%s)", python_path)
    return runtime, status


def build_computer(
    *,
    helper_path: str | Path | None = None,
    enabled: bool | None = None,
) -> tuple[ComputerRuntime | None, ComputerHostStatus]:
    """构建 Windows Computer Runtime；不支持的平台返回 unavailable status。"""

    platform = current_platform()
    if platform == "win32":
        return build_windows_computer(helper_path=helper_path, enabled=enabled)

    is_enabled = computer_enabled(enabled)
    status = ComputerHostStatus(
        enabled=is_enabled,
        available=False,
        platform=platform,
        reason="disabled" if not is_enabled else "unsupported_platform",
    )
    logger.info("Computer unavailable on platform %s", platform)
    return None, status


__all__ = [
    "ComputerHostStatus",
    "build_computer",
    "build_windows_computer",
    "computer_enabled",
    "current_platform",
]
