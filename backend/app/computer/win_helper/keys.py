"""Windows 键名与修饰键规范化。

支持 control/ctrl、alt、shift 和 win/super/meta；enter 归一为 return。
未知键和修饰键明确拒绝，避免把无效快捷键静默转换成其他操作。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Virtual-Key codes（Win32）
# ---------------------------------------------------------------------------

VK_RETURN = 0x0D
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B

#: 支持的键名与 Windows Virtual-Key code。
_SUPPORTED_KEYS: dict[str, int] = {
    "return": VK_RETURN,
    "tab": VK_TAB,
    "escape": VK_ESCAPE,
    "space": VK_SPACE,
    "backspace": VK_BACK,
    "delete": VK_DELETE,
    "left": VK_LEFT,
    "right": VK_RIGHT,
    "up": VK_UP,
    "down": VK_DOWN,
}
for _ch in "abcdefghijklmnopqrstuvwxyz":
    _SUPPORTED_KEYS[_ch] = ord(_ch.upper())
for _digit in "0123456789":
    _SUPPORTED_KEYS[_digit] = ord(_digit)

#: 需要 KEYEVENTF_EXTENDEDKEY 标志的键（方向键 / delete）。
_EXTENDED_KEYS = frozenset(
    {VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN, VK_DELETE}
)


def normalize_key(raw: str) -> str:
    """enter/return 统一为 return，其余转小写。"""

    key = raw.lower()
    return "return" if key == "enter" else key


def key_vk(raw: str) -> int | None:
    """key → VK code；未知键返回 None，不做静默降级。"""

    return _SUPPORTED_KEYS.get(normalize_key(raw))


def is_extended_key(vk: int) -> bool:
    return vk in _EXTENDED_KEYS


# ---------------------------------------------------------------------------
# Modifiers
# ---------------------------------------------------------------------------

#: raw 别名 → 稳定词表（control/shift/alt/win）。
_MODIFIER_ALIASES: dict[str, str] = {
    "shift": "shift",
    "alt": "alt",
    "control": "control",
    "ctrl": "control",
    "win": "win",
    "super": "win",
    "meta": "win",
}

#: 稳定修饰键名称 → Windows Virtual-Key code。
_MODIFIER_VK: dict[str, int] = {
    "control": VK_CONTROL,
    "shift": VK_SHIFT,
    "alt": VK_MENU,
    "win": VK_LWIN,
}


def normalize_modifier(raw: str) -> str | None:
    return _MODIFIER_ALIASES.get(raw.lower())


def normalize_modifiers(raw: list[str]) -> list[str] | None:
    """按首次出现顺序去重；含未知值返回 None。"""

    seen: set[str] = set()
    normalized: list[str] = []
    for item in raw:
        value = normalize_modifier(item)
        if value is None:
            return None
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def modifier_vk(normalized: str) -> int | None:
    return _MODIFIER_VK.get(normalized)


__all__ = [
    "VK_RETURN",
    "is_extended_key",
    "key_vk",
    "modifier_vk",
    "normalize_key",
    "normalize_modifier",
    "normalize_modifiers",
]
