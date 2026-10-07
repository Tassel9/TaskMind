from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from app.sandbox import (
    SandboxBackend,
    SandboxConfig,
    SandboxFilesystemMode,
    SandboxLaunchSpec,
    SandboxNetworkMode,
    SandboxPolicy,
    SandboxPolicyError,
    SandboxSupervisor,
    SandboxUnavailableError,
    UnsupportedSandboxBackend,
)


class RecordingBackend(SandboxBackend):
    def __init__(self) -> None:
        self.policy: SandboxPolicy | None = None

    def prepare(
        self,
        *,
        command: Path,
        args: tuple[str, ...],
        env: dict[str, str],
        policy: SandboxPolicy,
    ) -> SandboxLaunchSpec:
        self.policy = policy
        return SandboxLaunchSpec(
            command=str(command),
            args=args,
            cwd=str(policy.working_directory),
            env=env,
            backend="recording",
            sandboxed=True,
        )


def test_supervisor_compiles_workspace_policy_and_protects_metadata(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    (workspace / ".env").write_text("SECRET=value", encoding="utf-8")
    extra = workspace / "input"
    extra.mkdir()
    backend = RecordingBackend()
    supervisor = SandboxSupervisor(workspace, native_backend=backend)

    launch = supervisor.prepare_launch(
        command=sys.executable,
        args=("-V",),
        env={"PATH": os.environ.get("PATH", "")},
        cwd=None,
        config=SandboxConfig(
            filesystem=SandboxFilesystemMode.WORKSPACE_WRITE,
            network=SandboxNetworkMode.DENIED,
            readable_roots=("input",),
        ),
    )

    assert launch.sandboxed is True
    assert launch.backend == "recording"
    assert backend.policy is not None
    assert workspace in backend.policy.readable_roots
    assert workspace in backend.policy.writable_roots
    assert workspace / ".git" in backend.policy.denied_write_paths
    assert workspace / ".env" in backend.policy.denied_read_paths
    assert backend.policy.network is SandboxNetworkMode.DENIED


def test_supervisor_rejects_relative_path_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    supervisor = SandboxSupervisor(workspace, native_backend=RecordingBackend())

    with pytest.raises(SandboxPolicyError, match="不能越过 workspace"):
        supervisor.prepare_launch(
            command=sys.executable,
            args=(),
            env={"PATH": os.environ.get("PATH", "")},
            cwd=None,
            config=SandboxConfig(readable_roots=("../outside",)),
        )


def test_unsupported_platform_fails_closed(tmp_path: Path) -> None:
    supervisor = SandboxSupervisor(
        tmp_path,
        native_backend=UnsupportedSandboxBackend("unsupported"),
    )

    with pytest.raises(SandboxUnavailableError, match="拒绝降级执行"):
        supervisor.prepare_launch(
            command=sys.executable,
            args=(),
            env={"PATH": os.environ.get("PATH", "")},
            cwd=None,
            config=SandboxConfig(),
        )


def test_explicit_host_mode_is_visible_in_launch_spec(tmp_path: Path) -> None:
    supervisor = SandboxSupervisor(
        tmp_path,
        native_backend=UnsupportedSandboxBackend("unused"),
    )

    launch = supervisor.prepare_launch(
        command=sys.executable,
        args=(),
        env={"PATH": os.environ.get("PATH", "")},
        cwd=None,
        config=SandboxConfig(filesystem=SandboxFilesystemMode.HOST),
    )

    assert launch.sandboxed is False
    assert launch.backend == "host"


@pytest.mark.parametrize("filesystem", ["none", "read_only", "workspace_write"])
def test_default_backend_rejects_native_isolation_without_fallback(
    tmp_path, filesystem
):
    with pytest.raises(SandboxUnavailableError, match="拒绝降级执行"):
        SandboxSupervisor(tmp_path).prepare_launch(
            command=sys.executable,
            args=(),
            env={"PATH": os.environ.get("PATH", "")},
            cwd=None,
            config=SandboxConfig(filesystem=filesystem),
        )
