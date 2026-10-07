"""沙箱策略的平台执行后端。"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from .errors import SandboxUnavailableError
from .models import (
    SandboxLaunchSpec,
    SandboxPolicy,
)


class SandboxBackend(ABC):
    """把统一策略编译为实际进程启动参数。"""

    @abstractmethod
    def prepare(
        self,
        *,
        command: Path,
        args: tuple[str, ...],
        env: dict[str, str],
        policy: SandboxPolicy,
    ) -> SandboxLaunchSpec:
        """生成启动规格，不执行进程。"""


class HostSandboxBackend(SandboxBackend):
    """显式关闭隔离时使用；仍保留清理后的环境变量。"""

    def prepare(
        self,
        *,
        command: Path,
        args: tuple[str, ...],
        env: dict[str, str],
        policy: SandboxPolicy,
    ) -> SandboxLaunchSpec:
        return SandboxLaunchSpec(
            command=str(command),
            args=args,
            cwd=str(policy.working_directory),
            env=env,
            backend="host",
            sandboxed=False,
        )




class UnsupportedSandboxBackend(SandboxBackend):
    """没有可靠平台实现时 fail closed。"""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def prepare(
        self,
        *,
        command: Path,
        args: tuple[str, ...],
        env: dict[str, str],
        policy: SandboxPolicy,
    ) -> SandboxLaunchSpec:
        del command, args, env, policy
        raise SandboxUnavailableError(
            f"平台 {self.platform!r} 尚无可用的 TaskMind 沙箱后端，拒绝降级执行"
        )














def resolve_executable(command: str, *, env: dict[str, str]) -> Path:
    """只接受真实存在的绝对 executable，同时保留虚拟环境入口语义。"""

    candidate = Path(command).expanduser()
    if candidate.is_absolute() or "/" in command:
        executable = candidate.absolute()
    else:
        found = shutil.which(command, path=env.get("PATH"))
        if found is None:
            raise SandboxUnavailableError(f"找不到可执行文件：{command}")
        executable = Path(found).absolute()
    try:
        resolved = executable.resolve(strict=True)
    except OSError as exc:
        raise SandboxUnavailableError(f"可执行文件无效：{executable}") from exc
    if not resolved.is_file() or not executable.is_file():
        raise SandboxUnavailableError(f"可执行文件无效：{executable}")
    return executable


__all__ = [
    "HostSandboxBackend",
    "SandboxBackend",
    "UnsupportedSandboxBackend",
    "resolve_executable",
]
