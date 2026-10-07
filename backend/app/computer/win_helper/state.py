"""Session / Target / Observation 缓存与 freshness 状态机。

状态约束：

- ``begin_session`` 是唯一可建立 native session 的入口，已有其它 session
  时拒绝（绝不隐式接管）；
- Target（Agent 正在操作的应用）与 User Frontmost 分离，Target 不随
  前台漂移；observe 首次以当前前台窗口为初始 Target；
- 新 observe 整体替换旧缓存（observation_id / 元素 / 窗口 / 截图映射 /
  focused window / focused element）；
- 任何副作用动作成功后清空 Observation 缓存（UI 可能已变化）；
- 三级 freshness：targetSnapshotIsFresh（不要求前台）→
  requireBackgroundFresh（漂移时允许恢复已记录 Target 到前台）→
  requireFreshObservation（要求 Target 位于前台 + 窗口 bounds 稳定）。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from . import windows_api
from .capture import ScreenshotMapping
from .uia_tree import ElementInfo

logger = logging.getLogger("taskmind.computer.win_helper.state")

__all__ = ["ObservationCache", "SessionState", "SessionCheck"]

SESSION_OK = "ok"
SESSION_NOT_ACTIVE = "not_active"
SESSION_MISMATCH = "mismatch"

SessionCheck = str  # "ok" / "not_active" / "mismatch"

_BOUNDS_TOLERANCE = 2  # 像素


@dataclass
class ObservationCache:
    observation_id: str | None = None
    elements: dict[str, ElementInfo] = field(default_factory=dict)
    windows: dict[str, int] = field(default_factory=dict)  # ref -> hwnd
    screenshot_mapping: ScreenshotMapping | None = None
    target_pid: int | None = None
    focused_window: int | None = None
    focused_window_bounds: tuple[int, int, int, int] | None = None
    focused_element_ref: str | None = None

    def is_empty(self) -> bool:
        return (
            self.observation_id is None
            and not self.elements
            and not self.windows
            and self.screenshot_mapping is None
            and self.target_pid is None
            and self.focused_window is None
        )


class SessionState:
    """helper 进程内唯一的运行期状态（单线程使用）。"""

    def __init__(self) -> None:
        self.active_session_id: str | None = None
        self.target_pid: int | None = None
        self.target_exe: str | None = None
        self.target_name: str | None = None
        self.cache = ObservationCache()

    # ------------------------------------------------------------------
    # Session 生命周期
    # ------------------------------------------------------------------

    def begin_session(self, session_id: str) -> bool:
        """显式 begin_session；已有其它 session 时拒绝。"""

        if self.active_session_id is not None:
            return self.active_session_id == session_id
        self.clear_target()
        self.clear_cache()
        self.active_session_id = session_id
        logger.info("computer session begun (native): %s", session_id)
        return True

    def end_session(self, session_id: str) -> bool:
        if self.active_session_id != session_id:
            return False
        self.clear_target()
        self.clear_cache()
        self.active_session_id = None
        logger.info("computer session ended (native): %s", session_id)
        return True

    def check_session(self, session_id: str) -> SessionCheck:
        if self.active_session_id is None:
            return SESSION_NOT_ACTIVE
        if self.active_session_id != session_id:
            return SESSION_MISMATCH
        return SESSION_OK

    # ------------------------------------------------------------------
    # Target
    # ------------------------------------------------------------------

    def set_target(self, pid: int, exe: str | None, name: str | None) -> None:
        self.target_pid = pid
        self.target_exe = exe
        self.target_name = name

    def clear_target(self) -> None:
        self.clear_cache()
        self.target_pid = None
        self.target_exe = None
        self.target_name = None

    def target_alive(self) -> bool:
        return self.target_pid is not None and windows_api.process_alive(
            self.target_pid
        )

    def target_app_dict(self) -> dict | None:
        if self.target_pid is None:
            return None
        payload: dict = {
            "name": self.target_name or f"pid:{self.target_pid}",
            "process_id": self.target_pid,
        }
        if self.target_exe:
            payload["bundle_id"] = self.target_exe
        return payload

    # ------------------------------------------------------------------
    # Observation 缓存
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        self.cache = ObservationCache()

    def attach_observation(
        self,
        *,
        observation_id: str,
        elements: dict[str, ElementInfo],
        windows: dict[str, int],
        screenshot_mapping: ScreenshotMapping | None,
        target_pid: int | None,
        focused_window: int | None,
        focused_window_bounds: tuple[int, int, int, int] | None,
        focused_element_ref: str | None,
    ) -> None:
        self.cache = ObservationCache(
            observation_id=observation_id,
            elements=elements,
            windows=windows,
            screenshot_mapping=screenshot_mapping,
            target_pid=target_pid,
            focused_window=focused_window,
            focused_window_bounds=focused_window_bounds,
            focused_element_ref=focused_element_ref,
        )

    # ------------------------------------------------------------------
    # Freshness
    # ------------------------------------------------------------------

    def target_snapshot_is_fresh(
        self, expected_observation_id: str, session_id: str
    ) -> bool:
        """Freshness A：不要求前台；校验 session / observation / target /
        窗口仍属于目标进程且存活。"""

        cache = self.cache
        if self.check_session(session_id) != SESSION_OK:
            return False
        if expected_observation_id != cache.observation_id:
            return False
        expected_pid = cache.target_pid
        if expected_pid is None or self.target_pid != expected_pid:
            return False
        if not windows_api.process_alive(expected_pid):
            return False
        focused_window = cache.focused_window
        if focused_window is None or not windows_api.is_window(focused_window):
            return False
        return windows_api.get_window_pid(focused_window) == expected_pid

    def _foreground_matches_target(self) -> bool:
        expected_pid = self.cache.target_pid
        if expected_pid is None:
            return False
        foreground = windows_api.get_foreground_window()
        if not foreground:
            return False
        return windows_api.get_window_pid(foreground) == expected_pid

    def _bounds_are_stable(self) -> bool:
        cache = self.cache
        if cache.focused_window is None or cache.focused_window_bounds is None:
            return False
        bounds = windows_api.get_window_bounds(cache.focused_window)
        if bounds is None:
            return False
        expected = cache.focused_window_bounds
        return all(
            abs(bounds[index] - expected[index]) <= _BOUNDS_TOLERANCE
            for index in range(4)
        )

    def require_fresh_observation(
        self,
        expected_observation_id: str,
        *,
        require_stable_bounds: bool = False,
    ) -> bool:
        """Freshness B：target 必须位于前台（+ 可选 bounds 稳定）。

        验证 observation 新鲜度；调用方负责在失败时清缓存并
        返回结构化 stale_observation。
        """

        session_id = self.active_session_id or ""
        if not self.target_snapshot_is_fresh(
            expected_observation_id, session_id
        ):
            return False
        if not self._foreground_matches_target():
            return False
        if require_stable_bounds and not self._bounds_are_stable():
            return False
        return True

    def restore_recorded_target(self, *, timeout: float = 0.5) -> bool:
        """把已记录的目标窗口恢复到前台，并确认 Snapshot 仍一致。

        只恢复当前 Session 记录的精确窗口，绝不读取当前前台作为替代目标；
        任何不确定都返回 False（调用方按 stale 安全失败）。
        """

        cache = self.cache
        if cache.observation_id is None or cache.focused_window is None:
            return False
        expected_pid = cache.target_pid
        if expected_pid is None or self.target_pid != expected_pid:
            return False
        if not windows_api.is_window(cache.focused_window):
            return False
        windows_api.set_foreground_window(cache.focused_window)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._foreground_matches_target():
                return True
            time.sleep(0.05)
        return self._foreground_matches_target()

    def require_background_fresh(
        self,
        expected_observation_id: str,
        session_id: str,
        *,
        allow_foreground_restore: bool = True,
    ) -> bool:
        """Background-first freshness：Target 与 Snapshot 一致即可执行语义
        动作（如 UIA Invoke）；漂移时允许恢复已批准目标后继续。"""

        if self.target_snapshot_is_fresh(
            expected_observation_id, session_id
        ):
            return True
        if allow_foreground_restore and self.restore_recorded_target():
            return self.target_snapshot_is_fresh(
                expected_observation_id, session_id
            )
        return False
