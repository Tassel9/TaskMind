"""Computer Machine Lease 与 Tool Hook 的纯离线测试。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.computer import (
    ComputerBusyError,
    ComputerLeaseHook,
    ComputerLeaseManager,
    ComputerObserveTool,
    FakeComputerRuntime,
    register_computer_tools,
)
from app.models.types import ToolCall, ToolDefinition
from app.tools import (
    AutoApproveGate,
    BaseTool,
    ToolExecutionContext,
    ToolExecutor,
    ToolRegistry,
)


def test_machine_lease_blocks_another_host_process(tmp_path) -> None:
    """独立子进程持有租约时，当前 Host 必须拒绝抢占。"""

    lock_path = tmp_path / "machine.lock"
    child_code = (
        "import sys; from app.computer import ComputerLeaseManager; "
        "lease = ComputerLeaseManager(sys.argv[1]); lease.acquire('child-run'); "
        "print('ready', flush=True); sys.stdin.readline(); lease.close()"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", child_code, str(lock_path)],
        cwd=Path(__file__).resolve().parents[3],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    contender = ComputerLeaseManager(lock_path)
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
        with pytest.raises(ComputerBusyError):
            contender.acquire("parent-run")
    finally:
        process.communicate("release\n", timeout=10)
        contender.close()
    assert process.returncode == 0
    assert contender.acquire("parent-run").owner_run_id == "parent-run"
    contender.close()


def test_machine_lease_owner_lifecycle(tmp_path) -> None:
    manager = ComputerLeaseManager(tmp_path / "machine.lock")
    first = manager.acquire("run-a")
    again = manager.acquire("run-a")
    assert first.owner_run_id == again.owner_run_id == "run-a"
    assert first.acquired_at == again.acquired_at
    with pytest.raises(ComputerBusyError, match="another run"):
        manager.acquire("run-b")
    assert manager.release("run-b") is False
    assert manager.snapshot.owner_run_id == "run-a"
    assert manager.release("run-a") is True
    assert manager.acquire("run-b").owner_run_id == "run-b"
    manager.close()
    manager.close()
    assert manager.snapshot.owner_run_id is None


def test_flock_blocks_second_manager(tmp_path) -> None:
    path = tmp_path / "machine.lock"
    first = ComputerLeaseManager(path)
    second = ComputerLeaseManager(path)
    first.acquire("run-a")
    with pytest.raises(ComputerBusyError):
        second.acquire("run-b")
    first.close()
    assert second.acquire("run-b").owner_run_id == "run-b"
    second.close()




class PlainTool(BaseTool):
    definition = ToolDefinition(name="plain", description="普通工具")

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, arguments: dict[str, Any]) -> str:
        self.calls += 1
        return "ok"


async def test_computer_hook_requires_run_context_but_plain_tool_does_not(
    tmp_path,
) -> None:
    lease = ComputerLeaseManager(tmp_path / "machine.lock")
    fake = FakeComputerRuntime()
    plain = PlainTool()
    registry = ToolRegistry()
    registry.register(ComputerObserveTool(fake))
    registry.register(plain)
    executor = ToolExecutor(registry, hooks=(ComputerLeaseHook(lease),))

    computer = await executor.execute(
        ToolCall(id="c", name="computer_observe", arguments={})
    )
    normal = await executor.execute(ToolCall(id="p", name="plain", arguments={}))
    assert computer.success is False
    assert "requires run context" in (computer.error or "")
    assert normal.success is True and plain.calls == 1


async def test_busy_run_does_not_call_computer_runtime(tmp_path) -> None:
    lease = ComputerLeaseManager(tmp_path / "machine.lock")
    fake = FakeComputerRuntime()
    registry = ToolRegistry()
    registry.register(ComputerObserveTool(fake))
    executor = ToolExecutor(registry, hooks=(ComputerLeaseHook(lease),))
    call_a = ToolCall(id="a", name="computer_observe", arguments={})
    call_b = ToolCall(id="b", name="computer_observe", arguments={})

    first = await executor.execute(
        call_a, context=ToolExecutionContext(tool_call=call_a, run_id="run-a")
    )
    second = await executor.execute(
        call_b, context=ToolExecutionContext(tool_call=call_b, run_id="run-b")
    )
    assert first.success is True
    assert second.success is False
    assert "another run" in (second.error or "")
    assert lease.snapshot.owner_run_id == "run-a"
    lease.close()


async def test_same_run_reuses_lease_for_observe_and_action(tmp_path) -> None:
    lease = ComputerLeaseManager(tmp_path / "machine.lock")
    fake = FakeComputerRuntime()
    registry = ToolRegistry()
    register_computer_tools(registry, fake)
    executor = ToolExecutor(registry, hooks=(ComputerLeaseHook(lease),))
    observe = ToolCall(id="o", name="computer_observe", arguments={})
    scroll = ToolCall(id="s", name="computer_scroll", arguments={"delta_y": -1})
    assert (
        await executor.execute(
            observe,
            context=ToolExecutionContext(tool_call=observe, run_id="run-a"),
        )
    ).success
    assert (
        await executor.execute(
            scroll,
            context=ToolExecutionContext(tool_call=scroll, run_id="run-a"),
        )
    ).success
    assert lease.snapshot.owner_run_id == "run-a"
    assert [item.action.value for item in fake.action_history] == ["scroll"]
    lease.close()


async def test_busy_denial_overrides_human_approval_decision(tmp_path) -> None:
    """Lease denial must not be hidden by PermissionHook's approval request."""

    lease = ComputerLeaseManager(tmp_path / "machine.lock")
    lease.acquire("run-a")
    fake = FakeComputerRuntime()
    registry = ToolRegistry()
    register_computer_tools(registry, fake)
    executor = ToolExecutor(
        registry,
        approval_gate=AutoApproveGate(),
        hooks=(ComputerLeaseHook(lease),),
    )
    click = ToolCall(
        id="c",
        name="computer_click",
        arguments={"observation_id": "obs-1", "element_ref": "e1"},
    )
    result = await executor.execute(
        click,
        context=ToolExecutionContext(tool_call=click, run_id="run-b"),
    )
    assert result.success is False
    assert "another run" in (result.error or "")
    assert fake.action_history == []
    lease.close()
