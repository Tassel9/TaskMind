"""模型 API Key 的 Windows 凭据管理器存储边界。"""

from __future__ import annotations

import sys
from typing import Protocol


class ModelSecretStore(Protocol):
    """测试可替换的最小密钥存储接口。"""

    def get(self, provider: str) -> str | None: ...

    def set(self, provider: str, value: str) -> None: ...


class WindowsCredentialSecretStore:
    """将密钥保存在当前 Windows 用户的凭据管理器，不写入项目或 JSON。"""

    service = "com.taskmind.desktop.model-api-key"

    def get(self, provider: str) -> str | None:
        if sys.platform != "win32":
            return None
        import pywintypes
        import win32cred

        try:
            credential = win32cred.CredRead(
                f"{self.service}/{provider}", win32cred.CRED_TYPE_GENERIC
            )
        except pywintypes.error as exc:
            if exc.winerror == 1168:  # ERROR_NOT_FOUND
                return None
            raise RuntimeError("Windows 凭据管理器读取失败") from None
        blob = credential["CredentialBlob"]
        if isinstance(blob, bytes):
            return blob.decode("utf-16-le") or None
        return str(blob) or None

    def set(self, provider: str, value: str) -> None:
        if sys.platform != "win32":
            raise RuntimeError(
                "模型密钥保存需要 Windows 凭据管理器；其他环境请使用环境变量"
            )
        normalized = value.strip()
        if not normalized:
            raise ValueError("api key cannot be empty")
        import pywintypes
        import win32cred

        try:
            win32cred.CredWrite({
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": f"{self.service}/{provider}",
                "UserName": provider,
                "CredentialBlob": normalized,
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            })
        except pywintypes.error:
            raise RuntimeError("Windows 凭据管理器写入失败") from None


__all__ = ["ModelSecretStore", "WindowsCredentialSecretStore"]
