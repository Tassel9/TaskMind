"""协议方法实现：与 Swift helper（ProtocolHandlers/AppBackend/ObservationBuilder）
逐方法对齐，Python 端（app.computer.macos.MacOSComputerRuntime）无需感知平台。

错误以 ``HelperError(code, message)`` 抛出，由 ``__main__`` 统一转为
``{"error": {"code", "message"}}`` 响应；结构化错误码与 macOS 版一致
（session_not_active / session_mismatch / stale_observation /
element_not_found / action_not_supported / editable_target_required /
element_not_editable / focus_failed / input_event_failed / ...）。
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from . import HELPER_VERSION, keys, windows_api
from .capture import CaptureError, capture_window_screenshot
from .state import SESSION_NOT_ACTIVE, SESSION_OK, SessionState
from .uia_tree import TEXT_ENTRY_ROLES, collect_elements, read_runtime_id

logger = logging.getLogger("taskmind.computer.win_helper.handlers")

__all__ = [
    "HelperError",
    "handle_begin_session",
    "handle_click_coordinate",
    "handle_click_element",
    "handle_end_session",
    "handle_focus_window",
    "handle_key_press",
    "handle_observe",
    "handle_open_app",
    "handle_ping",
    "handle_scroll",
    "handle_screen_capture_status",
    "handle_accessibility_status",
    "handle_system_info",
    "handle_type_text",
]


class HelperError(Exception):
    """协议级结构化错误（code 与 macOS 版词表一致）。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# 公共校验
# ---------------------------------------------------------------------------


def _require_str(
    params: dict[str, Any],
    key: str,
    *,
    message: str | None = None,
) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HelperError(
            "invalid_params", message or f"missing or empty '{key}'"
        )
    return value.strip() if key in ("element_ref", "app") else value


def _require_int(params: dict[str, Any], key: str) -> int:
    value = params.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise HelperError("invalid_params", f"'{key}' must be an integer")
    return value


def _check_session(state: SessionState, session_id: str) -> None:
    result = state.check_session(session_id)
    if result == SESSION_OK:
        return
    if result == SESSION_NOT_ACTIVE:
        raise HelperError(
            "session_not_active",
            "no active computer session; begin_session required",
        )
    raise HelperError(
        "session_mismatch",
        "session mismatch; does not match the active run",
    )


def _stale(state: SessionState, message: str = "stale observation") -> HelperError:
    state.clear_cache()
    return HelperError("stale_observation", message)


# ---------------------------------------------------------------------------
# 基础
# ---------------------------------------------------------------------------


def handle_ping(state: SessionState, params: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True}


def handle_system_info(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    import platform  # noqa: PLC0415

    return {
        "platform": "windows",
        "helper_version": HELPER_VERSION,
        "process_id": os.getpid(),
        "windows_version": platform.version(),
        "windows_release": platform.release(),
    }


def handle_begin_session(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    session_id = _require_str(params, "session_id")
    if not state.begin_session(session_id):
        raise HelperError(
            "session_mismatch", "another computer session is already active"
        )
    return {"accepted": True}


def handle_end_session(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    session_id = _require_str(params, "session_id")
    return {"ended": state.end_session(session_id)}


def handle_accessibility_status(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    """Windows 没有辅助功能授权门槛，UIA 始终可用。"""

    return {"trusted": True}


def handle_screen_capture_status(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    """Windows 没有屏幕录制授权门槛。"""

    return {"granted": True}


# ---------------------------------------------------------------------------
# 应用信息
# ---------------------------------------------------------------------------


def _app_dict_from_pid(pid: int) -> dict[str, Any]:
    exe = windows_api.process_exe_path(pid)
    name = None
    if exe:
        base = os.path.basename(exe)
        name = base[:-4] if base.lower().endswith(".exe") else base
    payload: dict[str, Any] = {"name": name or f"pid:{pid}"}
    if exe:
        payload["bundle_id"] = exe
    payload["process_id"] = pid
    return payload


def _foreground_app_dict() -> dict[str, Any] | None:
    foreground = windows_api.get_foreground_window()
    if not foreground:
        return None
    pid = windows_api.get_window_pid(foreground)
    if not pid:
        return None
    return _app_dict_from_pid(pid)


def _ordered_windows(pid: int) -> list[windows_api.WindowInfo]:
    infos = windows_api.windows_of_pid(pid)
    foreground = windows_api.get_foreground_window()
    if foreground and any(info.hwnd == foreground for info in infos):
        infos.sort(key=lambda info: 0 if info.hwnd == foreground else 1)
    return infos


# ---------------------------------------------------------------------------
# observe（V3 对齐：目标绑定 + 语义元素 + 截图）
# ---------------------------------------------------------------------------


def handle_observe(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    observation_id = _require_str(params, "observation_id")
    session_id = _require_str(params, "session_id")
    _check_session(state, session_id)

    # Target：已绑定则校验存活；未绑定则显式以当前前台为初始 Target。
    if state.target_pid is not None:
        if not state.target_alive():
            state.clear_target()
            raise HelperError(
                "target_not_running",
                "computer target exited; open the target app again",
            )
        target_pid = state.target_pid
    else:
        foreground = windows_api.get_foreground_window()
        target_pid = (
            windows_api.get_window_pid(foreground) if foreground else None
        )
        if target_pid:
            exe = windows_api.process_exe_path(target_pid)
            name = None
            if exe:
                base = os.path.basename(exe)
                name = base[:-4] if base.lower().endswith(".exe") else base
            state.set_target(target_pid, exe, name)
            # set_target 只写身份；clear 由 begin_session / 显式失败路径负责。

    user_frontmost = _foreground_app_dict()
    target_app = state.target_app_dict()

    target_is_frontmost = False
    win_infos: list[windows_api.WindowInfo] = []
    if target_pid:
        foreground = windows_api.get_foreground_window()
        target_is_frontmost = bool(
            foreground and windows_api.get_window_pid(foreground) == target_pid
        )
        win_infos = _ordered_windows(target_pid)

    windows: list[dict[str, Any]] = []
    window_refs: dict[str, int] = {}
    for index, info in enumerate(win_infos):
        ref = f"w{index + 1}"
        x, y, width, height = info.bounds
        windows.append(
            {
                "ref": ref,
                "title": info.title,
                "bounds": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                },
            }
        )
        window_refs[ref] = info.hwnd

    active_window: dict[str, Any] | None = windows[0] if windows else None
    active_window_ref = "w1" if windows else None

    # 元素树：只从主窗口采集（对齐 macOS：focused window 为根）。
    elements: list[dict[str, Any]] = []
    focused_element_ref: str | None = None
    truncated = False
    element_stats = {
        "observed": 0,
        "returned": 0,
        "editable_count": 0,
        "actionable_count": 0,
        "repetitive_elements_dropped": 0,
    }
    element_map = {}
    if win_infos and target_pid:
        collection = collect_elements(win_infos[0].hwnd, target_pid)
        element_map = {item.ref: item for item in collection.elements}
        elements = [item.to_json() for item in collection.elements]
        focused_item = next(
            (item for item in collection.elements if item.focused), None
        )
        focused_element_ref = focused_item.ref if focused_item else None
        truncated = collection.truncated
        element_stats = {
            "observed": collection.observed,
            "returned": len(collection.elements),
            "editable_count": collection.editable_count,
            "actionable_count": collection.actionable_count,
            "repetitive_elements_dropped": collection.repetitive_elements_dropped,
        }

    # 截图（目标窗口，写入 Python 指定的路径）。
    screenshot_ref: str | None = None
    screenshot_error: dict[str, Any] | None = None
    screenshot_mapping = None
    include_screenshot = params.get("include_screenshot", False)
    screenshot_path = params.get("screenshot_path")
    if (
        include_screenshot is True
        and isinstance(screenshot_path, str)
        and screenshot_path
        and win_infos
    ):
        try:
            capture = capture_window_screenshot(
                win_infos[0].hwnd, screenshot_path
            )
            screenshot_ref = capture.png_path
            screenshot_mapping = capture.mapping
        except CaptureError as exc:
            screenshot_error = {"code": exc.code, "message": exc.message}
        except Exception as exc:  # noqa: BLE001 - 截图失败不能阻断 observe
            logger.exception("screenshot failed")
            screenshot_error = {
                "code": "screenshot_capture_failed",
                "message": str(exc),
            }

    state.attach_observation(
        observation_id=observation_id,
        elements=element_map,
        windows=window_refs,
        screenshot_mapping=screenshot_mapping,
        target_pid=target_pid,
        focused_window=win_infos[0].hwnd if win_infos else None,
        focused_window_bounds=win_infos[0].bounds if win_infos else None,
        focused_element_ref=focused_element_ref,
    )

    return {
        "active_app": target_app,
        "target": target_app,
        "target_is_frontmost": target_is_frontmost,
        "user_frontmost_app": user_frontmost,
        "active_window": active_window,
        "active_window_ref": active_window_ref,
        "windows": windows,
        "elements": elements,
        "focused_element_ref": focused_element_ref,
        "truncated": truncated,
        "element_stats": element_stats,
        "screenshot_ref": screenshot_ref,
        "screenshot_error": screenshot_error,
    }


# ---------------------------------------------------------------------------
# open_app（V7 对齐：启动 + 目标身份 + 激活确认）
# ---------------------------------------------------------------------------


def _activate_pid_window(
    pid: int, *, timeout: float = 3.0, hwnd: int | None = None
) -> bool:
    """等待目标窗口出现并带到前台。

    ``hwnd`` 为启动时精确发现的新窗口（共享进程 / Packaged App 场景下
    比"按 pid 找第一个窗口"更可信）。
    """

    deadline = time.monotonic() + timeout
    target_hwnd = hwnd
    while target_hwnd is None and time.monotonic() < deadline:
        infos = windows_api.windows_of_pid(pid)
        if infos:
            target_hwnd = infos[0].hwnd
            break
        time.sleep(0.15)
    if target_hwnd is None:
        return False
    windows_api.set_foreground_window(target_hwnd)
    confirm_deadline = time.monotonic() + 1.5
    while time.monotonic() < confirm_deadline:
        foreground = windows_api.get_foreground_window()
        if foreground and windows_api.get_window_pid(foreground) == pid:
            return True
        time.sleep(0.05)
    return False


def handle_open_app(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    app = _require_str(params, "app", message="missing or empty 'app'")
    session_id = _require_str(params, "session_id")
    _check_session(state, session_id)

    try:
        launch = windows_api.launch_app(app)
    except FileNotFoundError:
        raise HelperError(
            "app_not_found", f"application not found: {app}"
        ) from None
    except Exception as exc:  # noqa: BLE001
        logger.exception("open_app failed for %r", app)
        raise HelperError(
            "app_launch_failed", f"failed to launch {app}: {exc}"
        ) from exc

    state.clear_cache()
    pid = launch.pid
    exe = launch.exe
    name = None
    if exe:
        base = os.path.basename(exe)
        name = base[:-4] if base.lower().endswith(".exe") else base
    if pid:
        state.set_target(pid, exe, name)

    activation_confirmed = bool(
        pid
        and _activate_pid_window(pid, hwnd=launch.window_hwnd)
    )
    return {
        "app": app,
        "bundle_id": exe,
        "process_id": pid,
        "method": launch.method,
        "launch_status": "running",
        "activation_status": (
            "frontmost" if activation_confirmed else "not_frontmost"
        ),
        "frontmost_verified": activation_confirmed,
    }


# ---------------------------------------------------------------------------
# 语义点击（V4 对齐：press 语义 + background-first + foreground fallback）
# ---------------------------------------------------------------------------


def _try_press(control) -> tuple[bool, str | None]:  # noqa: ANN001
    """按 Invoke → Toggle → SelectionItem → Legacy 顺序执行 press 语义。

    返回 (ok, method)；method 为 None 表示元素不携带任何可按模式
    （对应 action_not_supported）。
    """

    attempts = (
        ("uia_invoke", "GetInvokePattern", "Invoke"),
        ("uia_toggle", "GetTogglePattern", "Toggle"),
        ("uia_select", "GetSelectionItemPattern", "Select"),
        (
            "legacy_default_action",
            "GetLegacyIAccessiblePattern",
            "DoDefaultAction",
        ),
    )
    for method, getter_name, action_name in attempts:
        getter = getattr(control, getter_name, None)
        if getter is None:
            continue
        try:
            pattern = getter()
        except Exception:  # noqa: BLE001
            pattern = None
        if pattern is None:
            continue
        try:
            getattr(pattern, action_name)()
        except Exception:  # noqa: BLE001 - 元素存在目标动作但执行失败
            logger.exception("press action failed via %s", method)
            return False, method
        return True, method
    return False, None


def handle_click_element(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    observation_id = _require_str(params, "observation_id")
    element_ref = _require_str(params, "element_ref")
    session_id = _require_str(params, "session_id")
    _check_session(state, session_id)

    if not state.require_background_fresh(
        observation_id, session_id, allow_foreground_restore=True
    ):
        raise _stale(state, "desktop state changed since observation")

    info = state.cache.elements.get(element_ref)
    if info is None:
        raise HelperError(
            "element_not_found", f"element not found: {element_ref}"
        )

    ok, method = _try_press(info.control)
    if ok:
        execution_mode = "background"
    elif method is None:
        raise HelperError(
            "action_not_supported",
            f"element {element_ref} has no actionable UIA pattern",
        )
    else:
        # 后台失败 → 恢复已批准目标到前台后重试一次（对齐 macOS）。
        if not state.restore_recorded_target():
            raise HelperError(
                "background_action_failed",
                "press failed and target could not be brought to foreground",
            )
        ok, method = _try_press(info.control)
        if not ok:
            raise HelperError(
                "background_action_failed",
                f"press failed for {element_ref} in both modes",
            )
        execution_mode = "foreground_fallback"

    state.clear_cache()
    return {
        "observation_id": observation_id,
        "element_ref": element_ref,
        "action": "press",
        "method": method,
        "execution_mode": execution_mode,
    }


# ---------------------------------------------------------------------------
# 坐标点击（V7 对齐：严格 freshness + 截图坐标映射）
# ---------------------------------------------------------------------------


def handle_click_coordinate(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    observation_id = _require_str(params, "observation_id")
    x = _require_int(params, "x")
    y = _require_int(params, "y")
    session_id = _require_str(params, "session_id")
    _check_session(state, session_id)

    if observation_id != state.cache.observation_id:
        raise _stale(state)
    if not state.require_fresh_observation(
        observation_id, require_stable_bounds=True
    ):
        raise _stale(state, "desktop state changed since observation")

    mapping = state.cache.screenshot_mapping
    if mapping is None:
        raise HelperError(
            "screenshot_unavailable",
            "current observation has no screenshot mapping",
        )
    point = mapping.global_point(x, y)
    if point is None:
        raise HelperError(
            "coordinate_out_of_bounds", "coordinate is outside screenshot"
        )
    if not windows_api.click_screen_point(round(point[0]), round(point[1])):
        raise HelperError(
            "input_event_failed", "failed to post coordinate click"
        )
    state.clear_cache()
    return {"method": "coordinate", "x": x, "y": y}


# ---------------------------------------------------------------------------
# 输入目标准备（type / key 共用；对齐 macOS prepareExactInputTarget）
# ---------------------------------------------------------------------------


def _is_focused_control(control) -> bool:  # noqa: ANN001
    try:
        import uiautomation as auto  # noqa: PLC0415

        focused = auto.GetFocusedControl()
        if focused is None:
            return False
        runtime_id = read_runtime_id(control)
        return runtime_id is not None and read_runtime_id(focused) == runtime_id
    except Exception:  # noqa: BLE001
        return False


def _focus_and_verify(control) -> bool:  # noqa: ANN001
    try:
        control.SetFocus()
    except Exception:  # noqa: BLE001
        return False
    return _is_focused_control(control)


def _prepare_exact_input_target(
    state: SessionState,
    *,
    observation_id: str,
    session_id: str,
    requested_element_ref: str | None,
    require_editable: bool,
) -> tuple[str | None, str]:
    """确定精确输入目标并确保可输入（前台 + 元素焦点）。

    返回 (element_ref, execution_mode)。任何不确定都 fail closed。
    """

    _check_session(state, session_id)
    if not state.target_snapshot_is_fresh(observation_id, session_id):
        raise _stale(state)

    cache = state.cache
    element_ref = requested_element_ref or cache.focused_element_ref
    info = None
    if element_ref is not None:
        info = cache.elements.get(element_ref)
        if info is None:
            raise HelperError(
                "element_not_found", f"element not found: {element_ref}"
            )
        if require_editable and not (
            info.editable and info.role in TEXT_ENTRY_ROLES
        ):
            raise HelperError(
                "element_not_editable",
                "element_ref must refer to a text-entry element with "
                "editable=true",
            )
    elif require_editable:
        raise HelperError(
            "editable_target_required",
            "type_text requires an editable element_ref",
        )

    # 1) 前台保障：Windows 键盘注入落在前台窗口，必须先把目标带回前台。
    execution_mode = "background"
    if not state._foreground_matches_target():
        execution_mode = "foreground_fallback"
        if not state.restore_recorded_target():
            raise HelperError("focus_failed", "focus_failed")

    # 2) 元素焦点 + 真实焦点验证；失败允许恢复目标后重试一次。
    if info is not None and not _focus_and_verify(info.control):
        if not state.restore_recorded_target() or not _focus_and_verify(
            info.control
        ):
            raise HelperError("focus_failed", "focus_failed")
        execution_mode = "foreground_fallback"

    return element_ref, execution_mode


# ---------------------------------------------------------------------------
# 文本输入（V5 对齐：UTF-16 分块 Unicode 注入；delivery vs verification）
# ---------------------------------------------------------------------------


def handle_type_text(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    text = params.get("text")
    if not isinstance(text, str):
        raise HelperError(
            "invalid_params",
            "missing 'text' / 'expected_observation_id' / 'session_id'",
        )
    expected_observation_id = _require_str(params, "expected_observation_id")
    session_id = _require_str(params, "session_id")
    element_ref_param = params.get("element_ref")
    if element_ref_param is not None:
        if not isinstance(element_ref_param, str) or not element_ref_param.strip():
            raise HelperError(
                "invalid_params", "'element_ref' must be a non-empty string"
            )
        element_ref_param = element_ref_param.strip()

    target_ref, execution_mode = _prepare_exact_input_target(
        state,
        observation_id=expected_observation_id,
        session_id=session_id,
        requested_element_ref=element_ref_param,
        require_editable=True,
    )

    if not text:
        return {
            "characters": 0,
            "method": "none",
            "execution_mode": execution_mode,
        }

    if target_ref is None or target_ref not in state.cache.elements:
        raise HelperError(
            "editable_target_required",
            "type_text requires an editable element_ref",
        )

    # SetFocus 之后给目标应用一个极短的处理窗口，避免首批字符
    # 与焦点切换竞态（实测 WinForms / Electron 在高频注入下会丢字符）。
    time.sleep(0.03)
    if not windows_api.send_unicode_text(text):
        raise HelperError(
            "input_event_failed", "failed to post unicode input events"
        )

    state.clear_cache()
    return {
        "characters": len(text),
        "element_ref": target_ref,
        "delivery_status": "delivered",
        "verification_status": "unverified",
        "evidence": {
            "note": "delivery_only; final verification requires fresh observe"
        },
        "method": "send_input_unicode",
        "execution_mode": execution_mode,
    }


# ---------------------------------------------------------------------------
# 按键（V6 对齐：VK 映射 + 修饰键组合）
# ---------------------------------------------------------------------------


def handle_key_press(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    key = params.get("key")
    if not isinstance(key, str) or not key:
        raise HelperError(
            "invalid_params",
            "missing or empty 'key' / 'expected_observation_id' / 'session_id'",
        )
    expected_observation_id = _require_str(params, "expected_observation_id")
    session_id = _require_str(params, "session_id")
    element_ref_param = params.get("element_ref")
    if element_ref_param is not None:
        if not isinstance(element_ref_param, str) or not element_ref_param.strip():
            raise HelperError(
                "invalid_params", "'element_ref' must be a non-empty string"
            )
        element_ref_param = element_ref_param.strip()

    vk = keys.key_vk(key)
    if vk is None:
        raise HelperError("unsupported_key", f"unsupported key: {key}")

    raw_modifiers = params.get("modifiers", [])
    if not isinstance(raw_modifiers, list) or not all(
        isinstance(item, str) for item in raw_modifiers
    ):
        raise HelperError(
            "invalid_params", "'modifiers' must be an array of strings"
        )
    modifiers = keys.normalize_modifiers(raw_modifiers)
    if modifiers is None:
        raise HelperError(
            "invalid_modifier", f"unknown modifier in {raw_modifiers}"
        )

    _, execution_mode = _prepare_exact_input_target(
        state,
        observation_id=expected_observation_id,
        session_id=session_id,
        requested_element_ref=element_ref_param,
        require_editable=False,
    )

    modifier_vks = [
        vk_value
        for vk_value in (keys.modifier_vk(name) for name in modifiers)
        if vk_value is not None
    ]
    if not windows_api.send_key_combo(
        vk, modifier_vks, extended=keys.is_extended_key(vk)
    ):
        raise HelperError(
            "input_event_failed", "failed to post key events"
        )

    state.clear_cache()
    return {
        "key": keys.normalize_key(key),
        "modifiers": modifiers,
        "method": "send_input_key",
        "execution_mode": execution_mode,
    }


# ---------------------------------------------------------------------------
# 滚动（V7 对齐：像素 delta → 滚轮档位）
# ---------------------------------------------------------------------------

_PIXELS_PER_WHEEL_STEP = 100


def _delta_to_clicks(delta: int) -> int:
    """像素 delta → WHEEL_DELTA 档位（非零方向保底一档）。"""

    if delta == 0:
        return 0
    clicks = int(delta / _PIXELS_PER_WHEEL_STEP)
    if clicks == 0:
        clicks = 1 if delta > 0 else -1
    return clicks


def handle_scroll(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    dx = _require_int(params, "delta_x")
    dy = _require_int(params, "delta_y")
    expected_observation_id = _require_str(params, "expected_observation_id")
    session_id = _require_str(params, "session_id")
    if dx == 0 and dy == 0:
        raise HelperError(
            "invalid_params",
            "scroll deltas must contain a non-zero integer",
        )
    _check_session(state, session_id)
    if not state.require_background_fresh(
        expected_observation_id, session_id, allow_foreground_restore=True
    ):
        raise _stale(state, "desktop state changed since observation")

    # 滚轮事件跟随光标位置：先把光标移到目标窗口中心（不点击）。
    cache = state.cache
    if cache.focused_window is not None:
        bounds = windows_api.get_window_bounds(cache.focused_window)
        if bounds is not None:
            x, y, width, height = bounds
            windows_api.move_cursor(x + width // 2, y + height // 2)

    clicks_y = _delta_to_clicks(dy)
    clicks_x = _delta_to_clicks(dx)
    if clicks_y and not windows_api.send_mouse_wheel(clicks=clicks_y):
        raise HelperError(
            "input_event_failed", "failed to post scroll events"
        )
    if clicks_x and not windows_api.send_mouse_wheel(
        clicks=clicks_x, horizontal=True
    ):
        raise HelperError(
            "input_event_failed", "failed to post scroll events"
        )

    state.clear_cache()
    return {
        "delta_x": dx,
        "delta_y": dy,
        "method": "send_input_wheel",
        "execution_mode": "background",
    }


# ---------------------------------------------------------------------------
# 窗口聚焦（V7 对齐：ax_raise → win32 set foreground）
# ---------------------------------------------------------------------------


def handle_focus_window(
    state: SessionState, params: dict[str, Any]
) -> dict[str, Any]:
    observation_id = _require_str(params, "observation_id")
    window_ref = _require_str(params, "window_ref")
    session_id = _require_str(params, "session_id")
    _check_session(state, session_id)

    if observation_id != state.cache.observation_id:
        raise _stale(state)
    if not state.require_fresh_observation(observation_id):
        if not (
            state.restore_recorded_target()
            and state.require_fresh_observation(observation_id)
        ):
            raise _stale(state, "desktop state changed since observation")

    hwnd = state.cache.windows.get(window_ref)
    if hwnd is None:
        raise HelperError(
            "window_not_found", f"window not found: {window_ref}"
        )
    if not windows_api.set_foreground_window(hwnd):
        raise HelperError("focus_window_failed", "SetForegroundWindow failed")

    state.clear_cache()
    return {
        "window_ref": window_ref,
        "method": "win32_set_foreground",
        "execution_mode": "foreground_fallback",
    }
