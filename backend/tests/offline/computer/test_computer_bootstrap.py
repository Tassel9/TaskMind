"""Windows Computer bootstrap：开关、解释器优先级、依赖与平台边界。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import app.computer.bootstrap as bootstrap
from app.computer import ComputerHelperRuntime, build_computer, computer_enabled


@pytest.fixture
def windows_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(bootstrap, "_windows_helper_missing_modules", lambda: [])
    monkeypatch.delenv("TASKMIND_COMPUTER_ENABLED", raising=False)
    monkeypatch.delenv("TASKMIND_WIN_HELPER_PYTHON", raising=False)


def _interpreter(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.write_text("test interpreter", encoding="utf-8")
    path.chmod(0o755)
    return path.resolve()


def test_explicit_interpreter_takes_priority(windows_platform, monkeypatch, tmp_path):
    explicit = _interpreter(tmp_path, "explicit.exe")
    fallback = _interpreter(tmp_path, "fallback.exe")
    monkeypatch.setenv("TASKMIND_WIN_HELPER_PYTHON", str(fallback))
    runtime, status = build_computer(helper_path=explicit)
    assert isinstance(runtime, ComputerHelperRuntime)
    assert runtime.helper_client.helper_path == explicit
    assert runtime.helper_client.helper_args == ("-m", "app.computer.win_helper")
    assert runtime.helper_client.cwd == str(bootstrap._BACKEND_ROOT)
    assert status.available and status.runtime == "windows"


def test_environment_interpreter_fallback(windows_platform, monkeypatch, tmp_path):
    fallback = _interpreter(tmp_path, "fallback.exe")
    monkeypatch.setenv("TASKMIND_WIN_HELPER_PYTHON", str(fallback))
    runtime, status = build_computer()
    assert runtime is not None and status.available
    assert runtime.helper_client.helper_path == fallback


def test_current_interpreter_fallback(windows_platform):
    runtime, status = build_computer()
    assert runtime is not None and status.available
    assert runtime.helper_client.helper_path == Path(sys.executable)


def test_missing_interpreter_is_unavailable(windows_platform, tmp_path):
    runtime, status = build_computer(helper_path=tmp_path / "missing.exe")
    assert runtime is None
    assert status.enabled and not status.available
    assert status.reason == "helper_not_found"


def test_missing_dependency_is_unavailable(windows_platform, monkeypatch):
    monkeypatch.setattr(
        bootstrap, "_windows_helper_missing_modules", lambda: ["uiautomation"]
    )
    runtime, status = build_computer()
    assert runtime is None and status.reason == "helper_dependency_missing"


def test_disabled_does_not_inspect_dependencies(windows_platform, monkeypatch):
    def unexpected_check():
        pytest.fail("disabled Computer must not inspect helper dependencies")
    monkeypatch.setattr(bootstrap, "_windows_helper_missing_modules", unexpected_check)
    runtime, status = build_computer(enabled=False)
    assert runtime is None and not status.enabled and status.reason == "disabled"


def test_unsupported_platform_is_unavailable(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    runtime, status = build_computer(enabled=True)
    assert runtime is None and status.platform == "linux"
    assert status.reason == "unsupported_platform"


def test_computer_enabled_switch_and_environment(monkeypatch):
    monkeypatch.delenv("TASKMIND_COMPUTER_ENABLED", raising=False)
    assert computer_enabled() is True
    monkeypatch.setenv("TASKMIND_COMPUTER_ENABLED", "false")
    assert computer_enabled() is False
    assert computer_enabled(enabled=True) is True
    monkeypatch.setenv("TASKMIND_COMPUTER_ENABLED", "true")
    assert computer_enabled() is True
    assert computer_enabled(enabled=False) is False


def test_current_platform_reports_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert bootstrap.current_platform() == "win32"
