"""win_helper 纯逻辑单元测试（跨平台可跑；系统交互部分不在此覆盖）。

覆盖范围：
- keys：键名 / 修饰键规范（Windows 修饰键与快捷键）；
- uia_tree：角色映射 / 语义优先级 / 输出预算选择；
- png：PNG 编码结构（zlib 往返校验）；
- capture：截图坐标映射（越界拒绝）；
- windows_api：PE 子系统解析（控制台 / GUI 启动分支的纯逻辑）；
- state：Session 生命周期（begin/end fail closed）。
"""

from __future__ import annotations

import struct
import zlib

from app.computer.win_helper import keys, windows_api
from app.computer.win_helper.capture import ScreenshotMapping
from app.computer.win_helper.handlers import HelperError, _delta_to_clicks
from app.computer.win_helper.png import (
    encode_png_from_bgra,
    encode_png_rgb,
)
from app.computer.win_helper.state import SessionState
from app.computer.win_helper.uia_tree import (
    ElementInfo,
    element_priority,
    is_useful_element,
    normalize_role,
    select_semantic_elements,
)

# ---------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------


def test_key_normalization_and_vk_lookup() -> None:
    assert keys.normalize_key("Enter") == "return"
    assert keys.normalize_key("TAB") == "tab"
    assert keys.key_vk("return") == 0x0D
    assert keys.key_vk("a") == 0x41
    assert keys.key_vk("7") == 0x37
    assert keys.key_vk("pagedown") is None  # 未支持的键明确拒绝
    assert keys.is_extended_key(0x25) is True  # left
    assert keys.is_extended_key(0x41) is False  # A


def test_modifier_aliases_and_windows_mapping() -> None:
    assert keys.normalize_modifiers(["ctrl", "SHIFT", "alt"]) == [
        "control",
        "shift",
        "alt",
    ]
    # 重复项去重且保持首次出现顺序
    assert keys.normalize_modifiers(["ctrl", "control"]) == ["control"]
    assert keys.normalize_modifiers(["bogus"]) is None
    # 修饰键直接映射到 Windows 虚拟键。
    assert keys.modifier_vk("control") == 0x11
    assert keys.modifier_vk("alt") == 0x12
    assert keys.modifier_vk("win") == 0x5B


# ---------------------------------------------------------------------------
# uia_tree：角色与语义选择
# ---------------------------------------------------------------------------


def _make_element(
    ref: str,
    role: str,
    *,
    title: str | None = None,
    value: str | None = None,
    focused: bool = False,
    editable: bool = False,
    actions: tuple[str, ...] = (),
) -> ElementInfo:
    return ElementInfo(
        ref=ref,
        role=role,
        title=title,
        value=value,
        enabled=True,
        focused=focused,
        editable=editable,
        bounds={"x": 0, "y": 0, "width": 10, "height": 10},
        actions=actions,
        control=None,
    )


def test_normalize_role_mapping() -> None:
    assert normalize_role("ButtonControl") == "button"
    assert normalize_role("EditControl") == "text_field"
    assert normalize_role("DocumentControl") == "text_area"
    assert normalize_role("CheckBoxControl") == "checkbox"
    assert normalize_role("TreeItemControl") == "outline_row"
    assert normalize_role("DataGridControl") == "table"
    assert normalize_role("SomeFancyControl") == "some_fancy"
    assert normalize_role("") == ""


def test_is_useful_element_rules() -> None:
    # 纯容器且无信息 → 丢弃
    assert is_useful_element("group", None, None, False) is False
    # 有文本信息 → 保留
    assert is_useful_element("group", "标题", None, False) is True
    assert is_useful_element("group", None, "value", False) is True
    # 非容器角色 → 保留
    assert is_useful_element("button", None, None, False) is True
    # 焦点元素永远保留
    assert is_useful_element("group", None, None, True) is True


def test_element_priority_order() -> None:
    focused = _make_element("e1", "group", focused=True)
    text_entry = _make_element("e2", "text_field", editable=True)
    editable = _make_element("e3", "slider", editable=True)
    actionable = _make_element("e4", "button", actions=("press",))
    meaningful = _make_element("e5", "image")
    repetitive = _make_element("e6", "list_item")
    priorities = [element_priority(item) for item in (
        focused, text_entry, editable, actionable, meaningful, repetitive,
    )]
    assert priorities == [0, 1, 2, 3, 4, 5]


def test_select_semantic_elements_respects_budgets() -> None:
    candidates = [
        _make_element(f"e{i}", "row", title=f"row {i}") for i in range(10)
    ]
    candidates.append(_make_element("e99", "text_field", editable=True))
    selected, dropped = select_semantic_elements(
        candidates, max_elements=4, max_repetitive_elements=2
    )
    refs = [item.ref for item in selected]
    # 可编辑元素优先，重复行受限
    assert "e99" in refs
    assert dropped >= 5
    assert len(selected) <= 4


def test_select_prefers_focused_over_budget_fillers() -> None:
    candidates = [
        _make_element(f"e{i}", "button", title=f"b{i}") for i in range(5)
    ]
    candidates.append(_make_element("e50", "text_area", focused=True))
    selected, _ = select_semantic_elements(
        candidates, max_elements=2, max_repetitive_elements=2
    )
    assert selected[0].ref == "e50"


# ---------------------------------------------------------------------------
# png 编码
# ---------------------------------------------------------------------------


def _decode_png_rows(data: bytes) -> tuple[int, int, bytes]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = bytearray()
    width = height = 0
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        tag = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", chunk[:10])
            assert depth == 8 and color == 2
        elif tag == b"IDAT":
            idat.extend(chunk)
        pos += 12 + length
    return width, height, zlib.decompress(bytes(idat))


def test_encode_png_rgb_structure() -> None:
    rows = [bytes([255, 0, 0] * 2), bytes([0, 255, 0] * 2)]
    data = encode_png_rgb(2, 2, rows)
    width, height, raw = _decode_png_rows(data)
    assert (width, height) == (2, 2)
    # 每行 filter=0 前缀，像素顺序保持 top-down
    assert raw == b"\x00" + rows[0] + b"\x00" + rows[1]


def test_encode_png_from_bgra_keeps_row_order() -> None:
    # width=1, height=2；pywin32 GetBitmapBits 返回 top-down：首行即顶部（红）
    bits = bytes([0, 0, 255, 255]) + bytes([255, 0, 0, 255])
    data = encode_png_from_bgra(1, 2, bits)
    width, height, raw = _decode_png_rows(data)
    assert (width, height) == (1, 2)
    # 顶部在前：红, 蓝（与输入行序一致，不做翻转）
    assert raw == b"\x00\xff\x00\x00\x00\x00\x00\xff"


# ---------------------------------------------------------------------------
# 截图坐标映射
# ---------------------------------------------------------------------------


def test_screenshot_mapping_global_point() -> None:
    mapping = ScreenshotMapping(
        pixel_width=1600, pixel_height=1200, x=100, y=80, width=800, height=600
    )
    assert mapping.global_point(800, 600) == (500.0, 380.0)
    assert mapping.global_point(0, 0) == (100.0, 80.0)
    # 越界（对齐 Windows 版语义）
    assert mapping.global_point(1600, 0) is None
    assert mapping.global_point(0, 1200) is None
    assert mapping.global_point(-1, 5) is None


# ---------------------------------------------------------------------------
# PE 子系统解析（控制台 / GUI 启动分支）
# ---------------------------------------------------------------------------


def _write_fake_pe(tmp_path, subsystem: int):
    header = bytearray(0x200)
    header[0:2] = b"MZ"
    struct.pack_into("<I", header, 0x3C, 0x80)
    header[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H", header, 0x80 + 0x18 + 0x44, subsystem)
    path = tmp_path / "fake.exe"
    path.write_bytes(bytes(header))
    return path


def test_pe_subsystem_console_and_gui(tmp_path) -> None:
    console = _write_fake_pe(tmp_path, windows_api._PE_SUBSYSTEM_CONSOLE)
    assert windows_api._pe_subsystem(str(console)) == 3
    gui = _write_fake_pe(tmp_path, windows_api._PE_SUBSYSTEM_GUI)
    assert windows_api._pe_subsystem(str(gui)) == 2
    not_pe = tmp_path / "notpe.exe"
    not_pe.write_bytes(b"hello")
    assert windows_api._pe_subsystem(str(not_pe)) is None


# ---------------------------------------------------------------------------
# scroll 换算
# ---------------------------------------------------------------------------


def test_delta_to_clicks() -> None:
    assert _delta_to_clicks(0) == 0
    assert _delta_to_clicks(250) == 2
    assert _delta_to_clicks(30) == 1
    assert _delta_to_clicks(-30) == -1
    assert _delta_to_clicks(-250) == -2


# ---------------------------------------------------------------------------
# Session 生命周期（fail closed；不触碰系统 API）
# ---------------------------------------------------------------------------


def test_session_lifecycle_fail_closed() -> None:
    state = SessionState()
    assert state.check_session("s1") == "not_active"
    assert state.begin_session("s1") is True
    # 幂等
    assert state.begin_session("s1") is True
    # 绝不被第二个 session 接管
    assert state.begin_session("s2") is False
    assert state.check_session("s2") == "mismatch"
    assert state.check_session("s1") == "ok"
    # 不匹配的 end 不生效
    assert state.end_session("s2") is False
    assert state.active_session_id == "s1"
    assert state.end_session("s1") is True
    assert state.check_session("s1") == "not_active"


def test_clear_target_clears_cache() -> None:
    state = SessionState()
    state.begin_session("s1")
    state.cache.observation_id = "obs-1"
    state.cache.windows["w1"] = 12345
    state.set_target(4242, "C:/x/y.exe", "y")
    assert state.target_pid == 4242
    state.clear_target()
    assert state.target_pid is None
    assert state.cache.is_empty() is True


def test_helper_error_carries_code() -> None:
    error = HelperError("stale_observation", "stale")
    assert error.code == "stale_observation"
    assert isinstance(error, Exception)
