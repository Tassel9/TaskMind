"""UI Automation 元素树采集与语义选择。

将 ControlType 转换为稳定角色，基于 ValuePattern 判定可编辑性，
优先保留焦点元素与有用信息，并限制深度、节点数和输出预算。
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("taskmind.computer.win_helper.uia")

__all__ = [
    "CollectionResult",
    "ElementInfo",
    "MAX_DEPTH",
    "MAX_ELEMENTS",
    "MAX_REPETITIVE_ELEMENTS",
    "MAX_VALUE_LENGTH",
    "MAX_VISITED_NODES",
    "collect_elements",
    "element_priority",
    "is_useful_element",
    "normalize_role",
    "read_runtime_id",
    "select_semantic_elements",
]

# ---------------------------------------------------------------------------
# 预算（对齐 Windows AccessibilityBackend）
# ---------------------------------------------------------------------------

MAX_ELEMENTS = 300
MAX_DEPTH = 12
MAX_VISITED_NODES = 3000
MAX_REPETITIVE_ELEMENTS = 80
MAX_VALUE_LENGTH = 1000
#: Windows 特有：跨进程 COM 遍历的时间预算（秒）。
MAX_TRAVERSAL_SECONDS = 6.0

# ---------------------------------------------------------------------------
# 角色 / 动作 / 可编辑判定
# ---------------------------------------------------------------------------

TEXT_ENTRY_ROLES = frozenset({"text_area", "text_field", "combo_box"})
REPETITIVE_ROLES = frozenset(
    {"row", "cell", "list_item", "outline_row", "static_text"}
)
CONTAINER_ROLES = frozenset(
    {
        "group",
        "split_group",
        "scroll_area",
        "splitter",
        "layout_area",
        "drawer",
        "tab_group",
    }
)

_ROLE_MAP: dict[str, str] = {
    "ButtonControl": "button",
    "SplitButtonControl": "button",
    "EditControl": "text_field",
    "DocumentControl": "text_area",
    "CheckBoxControl": "checkbox",
    "RadioButtonControl": "radio_button",
    "ComboBoxControl": "combo_box",
    "MenuControl": "menu",
    "MenuItemControl": "menu_item",
    "MenuBarControl": "menu_bar",
    "TabControl": "tab_group",
    "TabItemControl": "tab",
    "HyperlinkControl": "link",
    "SliderControl": "slider",
    "TableControl": "table",
    "DataGridControl": "table",
    "DataItemControl": "cell",
    "ListControl": "list",
    "ListItemControl": "list_item",
    "TreeControl": "outline",
    "TreeItemControl": "outline_row",
    "TextControl": "static_text",
    "ImageControl": "image",
    "GroupControl": "group",
    "PaneControl": "group",
    "ScrollBarControl": "scroll_bar",
    "ToolBarControl": "tool_bar",
    "WindowControl": "window",
    "StatusBarControl": "status_bar",
    "TitleBarControl": "title_bar",
    "ProgressBarControl": "progress_bar",
    "SpinnerControl": "spinner",
    "CalendarControl": "calendar",
    "ToolTipControl": "tool_tip",
    "CustomControl": "custom",
}

_SNAKE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def normalize_role(control_type_name: str) -> str:
    """"ButtonControl" → "button"；未映射角色去 Control 后缀并 snake_case。"""

    if not control_type_name:
        return ""
    if control_type_name in _ROLE_MAP:
        return _ROLE_MAP[control_type_name]
    base = (
        control_type_name[: -len("Control")]
        if control_type_name.endswith("Control")
        else control_type_name
    )
    return _SNAKE_BOUNDARY.sub("_", base).lower()


def _safe(getter, default=None):  # noqa: ANN001, ANN202
    try:
        value = getter()
    except Exception:  # noqa: BLE001 - UIA 元素可能已消失
        return default
    return value if value is not None else default


def _truncate(text: str, limit: int = MAX_VALUE_LENGTH) -> str:
    return text if len(text) <= limit else text[:limit]


@dataclass
class ElementInfo:
    """一次观察中的一个 UIA 元素（ref 仅在本 Observation 内有效）。"""

    ref: str
    role: str
    title: str | None
    value: str | None
    enabled: bool
    focused: bool
    editable: bool
    bounds: dict[str, int]
    actions: tuple[str, ...]
    control: Any = field(repr=False)

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ref": self.ref,
            "role": self.role,
            "enabled": self.enabled,
            "focused": self.focused,
            "editable": self.editable,
            "bounds": dict(self.bounds),
            "actions": list(self.actions),
        }
        if self.title:
            payload["title"] = self.title
        if self.value:
            payload["value"] = self.value
        return payload


def _read_patterns(control) -> dict[str, Any]:  # noqa: ANN001
    """按需探测 UIA pattern（每个元素最多一次获取）。"""

    patterns: dict[str, Any] = {}
    for name in (
        "Invoke",
        "Toggle",
        "SelectionItem",
        "ExpandCollapse",
        "Value",
    ):
        getter = getattr(control, f"Get{name}Pattern", None)
        if getter is None:
            patterns[name] = None
            continue
        try:
            patterns[name] = getter()
        except Exception:  # noqa: BLE001
            patterns[name] = None
    return patterns


def _value_from_pattern(patterns: dict[str, Any]) -> str | None:
    value_pattern = patterns.get("Value")
    if value_pattern is None:
        return None
    text = _safe(lambda: value_pattern.Value)
    if text is None:
        return None
    return _truncate(str(text))


def _is_editable(
    patterns: dict[str, Any], role: str, control, focused: bool  # noqa: ANN001
) -> bool:
    """按 UI Automation 的 ValuePattern、角色和焦点判断可输入性。

    - UIA ValuePattern 明确可写 → 可编辑（原生 Edit / ComboBox 等）；
    - Chromium / Electron 的编辑区域（网页 contenteditable、VS Code 编辑器）
      没有可靠的可写标志（ValuePattern 只读或缺失），但它们是文本角色且
      声明可键盘聚焦；此时按可输入处理（聚焦后 SendInput 可以生效）。
    """

    value_pattern = patterns.get("Value")
    if (
        value_pattern is not None
        and _safe(lambda: value_pattern.IsReadOnly, default=None) is False
    ):
        return True
    if role not in TEXT_ENTRY_ROLES:
        return False
    focusable = _safe(lambda: control.IsKeyboardFocusable, default=False)
    return bool(focusable) or focused


def _actions_from_patterns(patterns: dict[str, Any]) -> tuple[str, ...]:
    """pattern 可用性 → 动作词表（press/toggle/select/...，对齐 AX 词表风格）。"""

    actions: list[str] = []
    if patterns.get("Invoke") is not None:
        actions.append("press")
    if patterns.get("Toggle") is not None:
        actions.append("toggle")
    if patterns.get("SelectionItem") is not None:
        actions.append("select")
    if patterns.get("ExpandCollapse") is not None:
        actions.append("expand_collapse")
    value_pattern = patterns.get("Value")
    if (
        value_pattern is not None
        and _safe(lambda: value_pattern.IsReadOnly, default=True) is False
    ):
        actions.append("set_value")
    return tuple(sorted(actions))


def read_runtime_id(control) -> tuple | None:  # noqa: ANN001
    """读取 UIA RuntimeId（元素身份）；不可用时返回 None。"""

    runtime_id = _safe(lambda: control.GetRuntimeId())
    if runtime_id is None:
        return None
    try:
        return tuple(int(part) for part in runtime_id)
    except TypeError:
        return None


def _read_bounds(control) -> dict[str, int]:  # noqa: ANN001
    rect = _safe(lambda: control.BoundingRectangle)
    if rect is None:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    left = int(getattr(rect, "left", 0) or 0)
    top = int(getattr(rect, "top", 0) or 0)
    right = int(getattr(rect, "right", 0) or 0)
    bottom = int(getattr(rect, "bottom", 0) or 0)
    return {
        "x": left,
        "y": top,
        "width": max(0, right - left),
        "height": max(0, bottom - top),
    }


# ---------------------------------------------------------------------------
# 语义选择（纯逻辑，对齐 Windows selectSemanticElements）
# ---------------------------------------------------------------------------


def is_useful_element(
    role: str,
    title: str | None,
    value: str | None,
    focused: bool,
) -> bool:
    """有信息的元素 / 非容器元素保留。"""

    if focused:
        return True
    if (title or "").strip() or (value or "").strip():
        return True
    if role in CONTAINER_ROLES:
        return False
    return True


def element_priority(element: ElementInfo) -> int:
    """模型消费顺序：焦点 > 文本输入 > 可写 > 可操作 > 其它 > 重复项。"""

    if element.focused:
        return 0
    if element.editable and element.role in TEXT_ENTRY_ROLES:
        return 1
    if element.editable:
        return 2
    if element.actions:
        return 3
    if element.role in REPETITIVE_ROLES:
        return 5
    return 4


def _ref_number(ref: str) -> int:
    try:
        return int(ref[1:])
    except (ValueError, IndexError):
        return 2**31


def semantic_element_order(elements: list[ElementInfo]) -> list[ElementInfo]:
    return sorted(
        elements,
        key=lambda item: (element_priority(item), _ref_number(item.ref)),
    )


def select_semantic_elements(
    candidates: list[ElementInfo],
    max_elements: int = MAX_ELEMENTS,
    max_repetitive_elements: int = MAX_REPETITIVE_ELEMENTS,
) -> tuple[list[ElementInfo], int]:
    """在输出预算内优先保留焦点 / 可编辑 / 可操作元素，限制重复列表项。"""

    ordered = semantic_element_order(candidates)
    selected: list[ElementInfo] = []
    repetitive_kept = 0
    repetitive_dropped = 0
    for candidate in ordered:
        repetitive = candidate.role in REPETITIVE_ROLES
        if repetitive and repetitive_kept >= max_repetitive_elements:
            repetitive_dropped += 1
            continue
        if len(selected) >= max_elements:
            if repetitive:
                repetitive_dropped += 1
            continue
        selected.append(candidate)
        if repetitive:
            repetitive_kept += 1
    return selected, repetitive_dropped


# ---------------------------------------------------------------------------
# 采集（UIA）
# ---------------------------------------------------------------------------


@dataclass
class CollectionResult:
    elements: list[ElementInfo]
    truncated: bool
    observed: int
    editable_count: int
    actionable_count: int
    repetitive_elements_dropped: int


def _build_element_info(
    control,  # noqa: ANN001
    ref: str,
    *,
    force_focused: bool,
    allow_reported_focus: bool,
) -> ElementInfo | None:
    control_type = _safe(lambda: control.ControlTypeName, default="") or ""
    role = normalize_role(control_type)
    title_raw = _safe(lambda: control.Name)
    title = _truncate(str(title_raw)) if title_raw else None
    patterns = _read_patterns(control)
    value = _value_from_pattern(patterns)
    enabled = bool(_safe(lambda: control.IsEnabled, default=True))
    if force_focused:
        focused = True
    elif allow_reported_focus:
        focused = bool(_safe(lambda: control.HasKeyboardFocus, default=False))
    else:
        focused = False
    editable = _is_editable(patterns, role, control, focused)

    if not is_useful_element(role, title, value, focused):
        return None

    return ElementInfo(
        ref=ref,
        role=role,
        title=title,
        value=value,
        enabled=enabled,
        focused=focused,
        editable=editable,
        bounds=_read_bounds(control),
        actions=_actions_from_patterns(patterns),
        control=control,
    )


def _focused_runtime_id(target_pid: int) -> tuple | None:
    """读取全局焦点控件（仅当它属于目标进程时）。"""

    try:
        import uiautomation as auto  # noqa: PLC0415
    except ImportError:  # pragma: no cover - Windows-only 依赖缺失
        return None
    focused = _safe(auto.GetFocusedControl)
    if focused is None:
        return None
    process_id = _safe(lambda: focused.ProcessId)
    if process_id and int(process_id) != int(target_pid):
        return None
    return read_runtime_id(focused)


def collect_elements(root_hwnd: int, target_pid: int) -> CollectionResult:
    """从目标窗口根开始遍历 UIA 树并按语义预算选择输出。

    遍历预算（节点数 / 深度 / 时间）与输出预算（元素数 / 重复项）分离，
    真实焦点元素优先进入候选集。
    """

    try:
        import uiautomation as auto  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "uiautomation package is required for Windows computer helper"
        ) from exc

    root = _safe(lambda: auto.ControlFromHandle(root_hwnd))
    if root is None:
        return CollectionResult([], False, 0, 0, 0, 0)

    focused_id = _focused_runtime_id(target_pid)
    candidates: list[ElementInfo] = []
    visited: set[tuple | str] = set()
    next_ref = 1
    traversal_truncated = False
    deadline = time.monotonic() + MAX_TRAVERSAL_SECONDS

    def append_candidate(control, *, force_focused: bool) -> None:  # noqa: ANN001
        nonlocal next_ref
        ref = f"e{next_ref}"
        next_ref += 1
        info = _build_element_info(
            control,
            ref,
            force_focused=force_focused,
            allow_reported_focus=focused_id is None,
        )
        if info is not None:
            candidates.append(info)

    def visit(control, depth: int) -> None:  # noqa: ANN001
        nonlocal traversal_truncated
        if traversal_truncated or depth > MAX_DEPTH:
            return
        if len(visited) >= MAX_VISITED_NODES:
            traversal_truncated = True
            return
        if (len(visited) & 0x3F) == 0 and time.monotonic() > deadline:
            traversal_truncated = True
            return

        runtime_id = read_runtime_id(control)
        key: tuple | str = (
            runtime_id
            if runtime_id is not None
            else (
                _safe(lambda: control.ControlTypeName, default=""),
                _safe(lambda: control.Name, default=""),
            )
        )
        if key in visited:
            return
        visited.add(key)

        is_focused = (
            focused_id is not None
            and runtime_id is not None
            and runtime_id == focused_id
        )
        if not is_focused:
            append_candidate(control, force_focused=False)
        else:
            append_candidate(control, force_focused=True)
            # 焦点元素已作为最高优先级候选加入，仍继续遍历其 children。

        children = _safe(lambda: control.GetChildren(), default=None) or []
        for child in children:
            visit(child, depth + 1)

    visit(root, 0)

    selected, repetitive_dropped = select_semantic_elements(candidates)
    return CollectionResult(
        elements=selected,
        truncated=traversal_truncated or len(candidates) > len(selected),
        observed=len(candidates),
        editable_count=sum(1 for item in candidates if item.editable),
        actionable_count=sum(1 for item in candidates if item.actions),
        repetitive_elements_dropped=repetitive_dropped,
    )
