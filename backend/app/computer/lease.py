"""进程内 owner + 跨 Host 文件锁的 Computer Machine Lease。

跨进程互斥实现按平台选择：
- POSIX：``fcntl.flock``（非阻塞独占锁）；
- Windows：``msvcrt.locking`` 区域锁（等价语义，同进程/跨进程都阻挡）。
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

from app.tools.hooks import ToolExecutionContext, ToolHook, ToolHookDecision

if sys.platform == "win32":  # pragma: no cover - 平台分支
    import msvcrt

    fcntl = None
else:
    import fcntl

    msvcrt = None

if TYPE_CHECKING:
    from .session import ComputerSessionManager

logger = logging.getLogger("taskmind.computer.lease")


def _lock_file_exclusive(handle) -> None:  # noqa: ANN001
    """非阻塞独占文件锁；已被占用时抛 OSError。"""

    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    # Windows：锁定文件头部 1 字节的区域锁（LK_NBLCK 立即返回失败）。
    handle.seek(0)
    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)


def _unlock_file(handle) -> None:  # noqa: ANN001
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return
    handle.seek(0)
    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


class ComputerBusyError(RuntimeError):
    """电脑已被其它 Run 或 Host 占用。"""


@dataclass(frozen=True, slots=True)
class ComputerLeaseSnapshot:
    owner_run_id: str | None
    acquired_at: datetime | None
    process_id: int


class ComputerLeaseManager:
    """以 run_id 为 owner 的非等待、不可抢占机器租约。"""

    def __init__(self, lock_path: str | Path) -> None:
        self.lock_path = Path(lock_path).expanduser().resolve()
        self._guard = Lock()
        self._owner_run_id: str | None = None
        self._acquired_at: datetime | None = None
        self._lock_file = None

    @property
    def snapshot(self) -> ComputerLeaseSnapshot:
        with self._guard:
            return ComputerLeaseSnapshot(
                owner_run_id=self._owner_run_id,
                acquired_at=self._acquired_at,
                process_id=os.getpid(),
            )

    def acquire(self, run_id: str) -> ComputerLeaseSnapshot:
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("computer action requires run context")
        with self._guard:
            if self._owner_run_id == run_id:
                return self.snapshot_unlocked()
            if self._owner_run_id is not None:
                logger.info("computer lease busy for run %s", run_id)
                raise ComputerBusyError(
                    "computer is currently controlled by another run"
                )

            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_file = self.lock_path.open("a+", encoding="utf-8")
            try:
                _lock_file_exclusive(lock_file)
            except OSError as exc:
                lock_file.close()
                logger.info("computer lease busy in another host")
                raise ComputerBusyError(
                    "computer is currently controlled by another run"
                ) from exc

            acquired_at = datetime.now(UTC)
            lock_file.seek(0)
            lock_file.truncate()
            lock_file.write(
                f"pid={os.getpid()}\nrun_id={run_id}\n"
                f"acquired_at={acquired_at.isoformat()}\n"
            )
            lock_file.flush()
            self._lock_file = lock_file
            self._owner_run_id = run_id
            self._acquired_at = acquired_at
            logger.info("computer lease acquired by run %s", run_id)
            return self.snapshot_unlocked()

    def snapshot_unlocked(self) -> ComputerLeaseSnapshot:
        return ComputerLeaseSnapshot(
            owner_run_id=self._owner_run_id,
            acquired_at=self._acquired_at,
            process_id=os.getpid(),
        )

    def release(self, run_id: str) -> bool:
        with self._guard:
            if self._owner_run_id != run_id:
                return False
            self._release_unlocked()
            logger.info("computer lease released by run %s", run_id)
            return True

    def close(self) -> None:
        with self._guard:
            self._release_unlocked()

    def _release_unlocked(self) -> None:
        lock_file = self._lock_file
        self._lock_file = None
        self._owner_run_id = None
        self._acquired_at = None
        if lock_file is not None:
            try:
                _unlock_file(lock_file)
            finally:
                lock_file.close()


class ComputerLeaseHook(ToolHook):
    """只拦截 computer_*，生产链缺 run_id 时 fail closed。

    acquire 成功后同时建立 Run-scoped ComputerSession（V2）：
    Lease 保证单 Run 控制 Computer，Session 负责把 target / snapshot 状态
    归属到该 Run，并在 Run 结束时清除。

    ``session_starter``：由 composition root 注入的异步 callable
    （ComputerHelperRuntime.begin_session_rpc），负责通知 Native helper 显式
    ``begin_session``。缺省时回退到 Python 侧同步 begin。
    """

    critical = True

    def __init__(
        self,
        manager: ComputerLeaseManager,
        session_manager: ComputerSessionManager | None = None,
        session_starter: Callable[[str], Awaitable[object] | object] | None = None,
    ) -> None:
        self.manager = manager
        self.session_manager = session_manager
        self.session_starter = session_starter

    async def before_execute(
        self, context: ToolExecutionContext
    ) -> ToolHookDecision | None:
        if not context.tool_call.name.startswith("computer_"):
            return None
        if not context.run_id:
            return ToolHookDecision(
                denied_reason="computer action requires run context"
            )
        try:
            self.manager.acquire(context.run_id)
        except ComputerBusyError as exc:
            return ToolHookDecision(denied_reason=str(exc))
        if self.session_starter is not None:
            await self.session_starter(context.run_id)
        elif self.session_manager is not None:
            self.session_manager.begin(context.run_id)
        return None


__all__ = [
    "ComputerBusyError",
    "ComputerLeaseHook",
    "ComputerLeaseManager",
    "ComputerLeaseSnapshot",
]
