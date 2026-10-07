"""Windows 凭据管理器适配：密钥往返、缺失、失败与平台边界。"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.model_settings.secrets import WindowsCredentialSecretStore


class CredentialError(Exception):
    def __init__(self, code: int) -> None:
        self.winerror = code


@pytest.fixture
def credential_api(monkeypatch):
    api = SimpleNamespace(
        CRED_TYPE_GENERIC=1,
        CRED_PERSIST_LOCAL_MACHINE=2,
        CredRead=Mock(),
        CredWrite=Mock(),
    )
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "win32cred", api)
    monkeypatch.setitem(
        sys.modules, "pywintypes", SimpleNamespace(error=CredentialError)
    )
    return api


def test_credential_round_trip_uses_provider_scoped_unicode(credential_api):
    store = WindowsCredentialSecretStore()
    store.set("openai", "  fixture-key-测试  ")
    stored = credential_api.CredWrite.call_args.args[0]
    assert stored["TargetName"] == f"{store.service}/openai"
    assert stored["UserName"] == "openai"
    assert stored["CredentialBlob"] == "fixture-key-测试"
    assert stored["Type"] == 1 and stored["Persist"] == 2
    credential_api.CredRead.return_value = stored
    assert store.get("openai") == "fixture-key-测试"
    credential_api.CredRead.assert_called_once_with(stored["TargetName"], 1)


def test_binary_credential_is_read_as_windows_unicode(credential_api):
    credential_api.CredRead.return_value = {
        "CredentialBlob": "fixture-key-测试".encode("utf-16-le")
    }
    assert WindowsCredentialSecretStore().get("openai") == "fixture-key-测试"


def test_missing_credential_returns_none(credential_api):
    credential_api.CredRead.side_effect = CredentialError(1168)
    assert WindowsCredentialSecretStore().get("openai") is None


def test_read_failure_does_not_look_like_missing_key(credential_api):
    credential_api.CredRead.side_effect = CredentialError(5)
    with pytest.raises(RuntimeError, match="读取失败"):
        WindowsCredentialSecretStore().get("openai")


def test_write_failure_never_includes_secret(credential_api):
    credential_api.CredWrite.side_effect = CredentialError(5)
    with pytest.raises(RuntimeError, match="写入失败") as captured:
        WindowsCredentialSecretStore().set("openai", "fixture-key")
    assert "fixture-key" not in str(captured.value)


def test_empty_key_is_rejected_before_write(credential_api):
    with pytest.raises(ValueError, match="empty"):
        WindowsCredentialSecretStore().set("openai", " ")
    credential_api.CredWrite.assert_not_called()


def test_non_windows_keeps_environment_configuration_available(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    store = WindowsCredentialSecretStore()
    assert store.get("openai") is None
    with pytest.raises(RuntimeError, match="环境变量"):
        store.set("openai", "fixture-key")
