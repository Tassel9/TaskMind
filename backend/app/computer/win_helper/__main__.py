"""Windows Computer Helper 入口：标准输入/输出上的 UTF-8 JSON Lines。

协议：

    Python → Helper:  {"id": 1, "method": "ping", "params": {}}
    Helper → Python:  {"id": 1, "result": {"ok": true}}
                     或 {"id": 1, "error": {"code", "...", "message": "..."}}

协议边界：
- stdout 只允许协议 JSON；日志一律写 stderr；
- 非法 JSON / 未知 method / 缺 method 都返回 error，进程不退出；
- 单条请求内部异常 → internal_error 响应，进程不退出；
- stdin EOF 时正常退出（exit 0）。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger("taskmind.computer.win_helper.main")


def _configure_streams() -> None:
    """stdin/stdout/stderr 全部固定 UTF-8（协议数据边界）。"""

    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace", newline="\n")
            except (ValueError, OSError):
                # 管道已被重定向到非常规对象时忽略；后续按默认编码处理。
                continue


def _write_response(payload: dict[str, Any]) -> None:
    try:
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write(line)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        # 父进程已退出；主循环会在下一次读取/写入时结束。
        raise SystemExit(0) from None


def _error_response(
    request_id: Any, code: str, message: str
) -> dict[str, Any]:
    return {"id": request_id, "error": {"code": code, "message": message}}


def main() -> int:
    if sys.platform != "win32":  # pragma: no cover - 防御性
        sys.stderr.write(
            "windows computer helper can only run on win32\n"
        )
        return 2

    _configure_streams()
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # 依赖 import（uiautomation / comtypes / pywin32）可能向 stdout 打印；
    # 在 import 期间把 stdout 临时指向 stderr，保证协议通道纯净。
    real_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        from . import (
            handlers,  # noqa: PLC0415
            windows_api,  # noqa: PLC0415
        )
        from .state import SessionState  # noqa: PLC0415

        windows_api.ensure_dpi_awareness()
        dispatcher = {
            "ping": handlers.handle_ping,
            "system_info": handlers.handle_system_info,
            "begin_session": handlers.handle_begin_session,
            "end_session": handlers.handle_end_session,
            "accessibility_status": handlers.handle_accessibility_status,
            "screen_capture_status": handlers.handle_screen_capture_status,
            "observe": handlers.handle_observe,
            "open_app": handlers.handle_open_app,
            "click_element": handlers.handle_click_element,
            "click_coordinate": handlers.handle_click_coordinate,
            "type_text": handlers.handle_type_text,
            "key_press": handlers.handle_key_press,
            "scroll": handlers.handle_scroll,
            "focus_window": handlers.handle_focus_window,
        }
        state = SessionState()
    finally:
        sys.stdout = real_stdout

    logger.info("windows computer helper started (pid=%s)", os.getpid())

    while True:
        try:
            raw = sys.stdin.readline()
        except (KeyboardInterrupt, OSError):
            return 0
        if not raw:
            return 0
        line = raw.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            _write_response(
                _error_response(None, "invalid_request", "malformed JSON")
            )
            continue
        if not isinstance(payload, dict):
            _write_response(
                _error_response(
                    None, "invalid_request", "request must be a JSON object"
                )
            )
            continue

        request_id = payload.get("id")
        if not isinstance(request_id, int) or isinstance(request_id, bool):
            _write_response(
                _error_response(
                    None, "invalid_request", "request id must be an integer"
                )
            )
            continue

        method = payload.get("method")
        if not isinstance(method, str) or not method:
            _write_response(
                _error_response(request_id, "invalid_request", "missing method")
            )
            continue

        handler = dispatcher.get(method)
        if handler is None:
            _write_response(
                _error_response(
                    request_id, "unknown_method", f"unknown method: {method}"
                )
            )
            continue

        params = payload.get("params")
        if not isinstance(params, dict):
            params = {}
        try:
            result = handler(state, params)
        except handlers.HelperError as exc:
            _write_response(_error_response(request_id, exc.code, exc.message))
            continue
        except Exception as exc:  # noqa: BLE001 - 单请求失败不能杀进程
            logger.exception("handler %s failed", method)
            _write_response(
                _error_response(request_id, "internal_error", str(exc))
            )
            continue
        _write_response({"id": request_id, "result": result})


if __name__ == "__main__":
    sys.exit(main())
