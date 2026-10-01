"""Computer bootstrap：为当前平台解析 helper 并构建真实 Runtime。

- macOS：Swift helper（``native/macos-computer-helper``），解析顺序：
  显式参数（CLI ``--computer-helper``）> 环境变量
  ``TASKMIND_MACOS_HELPER_PATH`` > dev 路径
  ``native/macos-computer-helper/.build/debug/MacOSComputerHelper``；
- Windows：Python helper（``app.computer.win_helper``，同一套 JSON Lines
  协议），以 ``<python> -m app.computer.win_helper`` 启动；解释器解析顺序：
  显式参数 > 环境变量 ``TASKMIND_WIN_HELPER_PYTHON`` > 当前进程解释器
  （即 backend venv）。

helper 找不到 / 依赖缺失 / 显式 disable 都**不**应影响 Host 启动
（Chat / Run / Automation 照常工作），只是 Computer 不可用。

不自动 ``swift build``：Host 启动不应依赖本机安装 Swift toolchain。
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .helper_client import MacOSHelperClient
from .macos import MacOSComputerRuntime
from .runtime import ComputerRuntime

logger = logging.getLogger("taskmind.computer.bootstrap")

# backend/app/computer/bootstrap.py → backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
# backend/app/computer/bootstrap.py → 项目根
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DEV_HELPER = (
    _PROJECT_ROOT
    / "native"
    / "macos-computer-helper"
    / ".build"
    / "debug"
    / "MacOSComputerHelper"
)

ENV_HELPER_PATH = "TASKMIND_MACOS_HELPER_PATH"
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
    return "macos" if sys.platform == "darwin" else sys.platform


def _is_executable(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def resolve_helper_path(explicit: str | Path | None = None) -> Path | None:
    """按 显式 > 环境变量 > dev 路径 顺序解析 helper 二进制。"""

    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env = os.environ.get(ENV_HELPER_PATH)
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(_DEFAULT_DEV_HELPER)

    for candidate in candidates:
        if _is_executable(candidate):
            return candidate.resolve()
    return None


def computer_enabled(enabled: bool | None = None) -> bool:
    """Computer 开关：显式参数 > TASKMIND_COMPUTER_ENABLED > 默认启用。

    默认启用（非 macOS 是否可用由 ``build_macos_computer`` 判定，不会因为
    平台不同而把用户显式启用的意图误判为 disabled）。
    """

    if enabled is not None:
        return enabled
    raw = os.environ.get(ENV_COMPUTER_ENABLED, "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return True


def build_macos_computer(
    *,
    helper_path: str | Path | None = None,
    enabled: bool | None = None,
) -> tuple[ComputerRuntime | None, ComputerHostStatus]:
    """构建真实 MacOSComputerRuntime；不可用时返回 (None, unavailable status)。"""

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

    if platform != "macos":
        status = ComputerHostStatus(
            enabled=True,
            available=False,
            platform=platform,
            reason="unsupported_platform",
        )
        logger.info("Computer unavailable on platform %s", platform)
        return None, status

    path = resolve_helper_path(helper_path)
    if path is None:
        status = ComputerHostStatus(
            enabled=True,
            available=False,
            platform=platform,
            reason="helper_not_found",
        )
        logger.info("Computer helper not found; Host continues without computer")
        return None, status

    client = MacOSHelperClient(path)
    runtime = MacOSComputerRuntime(client)
    status = ComputerHostStatus(
        enabled=True,
        available=True,
        platform=platform,
        reason=None,
        helper_path=str(path),
        runtime="macos",
    )
    logger.info("Computer Runtime: macOS available (%s)", path)
    return runtime, status


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
    进程解释器，即 backend venv）。Python 侧 Runtime 与 macOS 共用
    （``MacOSComputerRuntime`` 只负责协议映射，本身无平台逻辑）。
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

    client = MacOSHelperClient(
        python_path,
        helper_args=("-m", "app.computer.win_helper"),
        cwd=_BACKEND_ROOT,
    )
    runtime = MacOSComputerRuntime(client)
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
    """按当前平台构建 Computer Runtime（macOS: Swift helper / Windows:
    Python helper）；不支持的平台返回 unavailable status。"""

    platform = current_platform()
    if platform == "macos":
        return build_macos_computer(helper_path=helper_path, enabled=enabled)
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
    "build_macos_computer",
    "build_windows_computer",
    "computer_enabled",
    "current_platform",
    "resolve_helper_path",
]
