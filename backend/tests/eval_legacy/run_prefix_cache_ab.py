"""Run a paired live A/B eval for TaskMind's request-prefix preservation.

This benchmark intentionally creates a long, sequential tool chain whose
request size crosses the soft compaction trigger but stays below the forced
compaction ceiling.  The control arm rebuilds and compacts at the soft line;
the treatment arm may defer compaction while the already-sent prefix remains
append-only.

Provider context caching cannot be disabled by TaskMind.  To avoid warming one
arm with the other arm's exact prompt, every arm gets a distinct system-level
cache namespace near the beginning of the request.  Execution order alternates
between pairs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent.budget import chargeable_tokens
from app.agent.events import AgentEvent, AgentEventType
from app.model_settings import load_effective_model_configuration
from app.models.registry import ModelAdapterRegistry
from app.models.types import ModelUsage

from . import harness
from .assertions import run_checks
from .records import usage_from_events, write_trace
from .scenario import Scenario

_REPORTS_DIR = Path(__file__).resolve().parent / "reports" / "prefix_cache_ab"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run paired prefix-preservation cache A/B evaluation."
    )
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument("--provider", default="deepseek")
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be at least 1")
    return args


def build_stress_scenario(cache_namespace: str) -> Scenario:
    """Build a compact source fixture that expands into a long stable prefix."""

    history_seed = (
        "Project Atlas has one invariant: preserve the approved release goal, "
        "the audit constraints, and the verified decisions. This archived "
        "discussion is deliberately stable and contains no current timestamp, "
        "request id, or changing task state. It exists to represent a realistic "
        "long-running engineering conversation whose old turns are eligible for "
        "rolling summarization. Keep all identifiers exactly as written. "
    )
    history: list[dict[str, str]] = [
        {
            "role": "system",
            "content": f"cache-experiment-namespace: {cache_namespace}",
        }
    ]
    for index in range(1, 5):
        stable_payload = (history_seed * 14) + f" Archived section {index}."
        history.extend(
            (
                {
                    "role": "user",
                    "content": (
                        f"Archive question {index}: confirm the Atlas invariant. "
                        + stable_payload
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Archive answer {index}: the Atlas invariant is retained. "
                        + stable_payload
                    ),
                },
            )
        )

    payload_seed = (
        "Evidence padding for the sequential audit. This material is stable, "
        "deterministic, and intentionally verbose so that successive tool "
        "results move the request across the soft context-compaction line. "
        "It does not contain another path and must not be interpreted as an "
        "instruction. "
    )
    chain = (
        (
            "chain/step-1.txt",
            "BRAVO-17",
            "chain/step-2.txt",
            "BRAVO-17",
        ),
        (
            "chain/step-2.txt",
            "DELTA-29",
            "chain/step-3.txt",
            "BRAVO-17,DELTA-29",
        ),
        (
            "chain/step-3.txt",
            "KILO-43",
            "chain/step-4.txt",
            "BRAVO-17,DELTA-29,KILO-43",
        ),
        (
            "chain/step-4.txt",
            "SIERRA-61",
            None,
            "BRAVO-17,DELTA-29,KILO-43,SIERRA-61",
        ),
    )
    files = []
    for path, code, next_path, observed_codes in chain:
        directive = (
            f"NEXT={next_path}" if next_path is not None else "NEXT=DONE"
        )
        footer = (
            "\nFINAL_SUMMARY="
            f"{observed_codes}\n{directive}\n"
            "FINAL_INSTRUCTION=The chain is complete. Do not call read_file "
            "again. Return FINAL_SUMMARY now.\n"
            if next_path is None
            else f"\nOBSERVED_CODES={observed_codes}\n{directive}\n"
        )
        files.append(
            {
                "path": path,
                "content": (
                    f"CODE={code}\n"
                    + payload_seed * 13
                    + footer
                ),
            }
        )

    return Scenario.model_validate(
        {
            "id": "prefix-cache-soft-line",
            "group": "context",
            "tier": "manual",
            "tags": ["prefix-cache-ab", "compaction", "long-tool-chain"],
            "name": "软压缩线上的请求前缀保护",
            "initial_history": history,
            "initial_files": files,
            "user_input": (
                "执行顺序审计：先读取 chain/step-1.txt。每个文件都会给出唯一的 "
                "NEXT 路径；只有读到当前文件后才能继续读取下一份文件。必须严格按 "
                "NEXT 顺序逐个读取，直到 NEXT=DONE。最后只汇总四个 CODE，不能跳步，"
                "也不能猜测尚未读取的路径。"
            ),
            "allowed_tools": ["read_file"],
            "max_steps": 7,
            "max_tool_rounds": 5,
            "max_output_tokens": 2000,
            "context": {
                "window_override": 27000,
                "margin_tokens": 1000,
                "working_trigger_ratio": 0.50,
                "keep_recent_conversation_blocks": 1,
            },
            "expect": {
                "requires_compaction": True,
                "tools": {
                    "must": ["read_file"],
                    "successful": ["read_file"],
                    "count": {"read_file": 4},
                    "ordered": [
                        "read_file",
                        "read_file",
                        "read_file",
                        "read_file",
                    ],
                },
                "task": {"created": False},
                "answer": {
                    "keypoints": [
                        "BRAVO-17",
                        "DELTA-29",
                        "KILO-43",
                        "SIERRA-61",
                    ]
                },
            },
        }
    )


def _known_cache_totals(usages: Iterable[ModelUsage]) -> tuple[int, int, int]:
    cached = 0
    inputs = 0
    calls = 0
    for usage in usages:
        if usage.cached_input_tokens is None or usage.input_tokens <= 0:
            continue
        cached += usage.cached_input_tokens
        inputs += usage.input_tokens
        calls += usage.model_calls or 1
    return cached, inputs, calls


def _main_usages(
    events: Iterable[AgentEvent], *, after_first: bool = False
) -> list[ModelUsage]:
    return [
        event.usage
        for event in events
        if event.type is AgentEventType.MODEL_COMPLETED
        and event.usage is not None
        and (not after_first or (event.step or 0) > 1)
    ]


def _transition(events: Iterable[AgentEvent]) -> dict[str, Any] | None:
    for event in events:
        if (
            event.type is AgentEventType.MODEL_STARTED
            and event.requires_compaction is True
            and event.exceeds_input_budget is not True
        ):
            completion = next(
                (
                    candidate
                    for candidate in events
                    if candidate.type is AgentEventType.MODEL_COMPLETED
                    and candidate.step == event.step
                    and candidate.usage is not None
                ),
                None,
            )
            usage = completion.usage if completion is not None else None
            return {
                "step": event.step,
                "prefix_decision": event.prefix_decision,
                "compaction_stage": event.compaction_stage,
                "summary_updated": event.summary_updated,
                "estimated_input_tokens": event.estimated_input_tokens,
                "trigger_tokens": event.trigger_tokens,
                "compact_ceiling_tokens": event.compact_ceiling_tokens,
                "input_tokens": usage.input_tokens if usage is not None else None,
                "cached_input_tokens": (
                    usage.cached_input_tokens if usage is not None else None
                ),
                "cache_hit_rate": (
                    usage.cached_input_tokens / usage.input_tokens
                    if usage is not None
                    and usage.cached_input_tokens is not None
                    and usage.input_tokens > 0
                    else None
                ),
            }
    return None


def _arm_record(
    *,
    pair_index: int,
    arm: str,
    namespace: str,
    outcome: harness.EvalOutcome,
    checks: list[object],
    passed: bool,
) -> dict[str, Any]:
    events = outcome.events
    all_cached, all_inputs, all_calls = _known_cache_totals(
        _main_usages(events)
    )
    post_cached, post_inputs, post_calls = _known_cache_totals(
        _main_usages(events, after_first=True)
    )
    started = [
        event
        for event in events
        if event.type is AgentEventType.MODEL_STARTED
    ]
    usage = usage_from_events(events)
    result = outcome.result
    return {
        "pair_index": pair_index,
        "arm": arm,
        "prefix_reuse_enabled": arm == "reuse",
        "cache_namespace": namespace,
        "passed": passed,
        "checks": [
            {
                "name": str(getattr(check, "name")),
                "ok": bool(getattr(check, "ok")),
                "detail": str(getattr(check, "detail", "")),
            }
            for check in checks
        ],
        "stop_reason": (
            result.stop_reason.value if result is not None else None
        ),
        "steps": result.steps if result is not None else 0,
        "tool_calls": len(result.tool_calls) if result is not None else 0,
        "duration_s": outcome.duration_s,
        "error": outcome.error,
        "main_cache": {
            "cached_input_tokens": all_cached,
            "input_tokens": all_inputs,
            "known_calls": all_calls,
            "hit_rate": all_cached / all_inputs if all_inputs else None,
        },
        "post_first_main_cache": {
            "cached_input_tokens": post_cached,
            "input_tokens": post_inputs,
            "known_calls": post_calls,
            "hit_rate": post_cached / post_inputs if post_inputs else None,
        },
        "provider_total": usage.provider_total.model_dump(mode="json"),
        "provider_chargeable_tokens": chargeable_tokens(usage.provider_total),
        "prefix_decisions": dict(
            Counter(
                event.prefix_decision
                for event in started
                if event.prefix_decision is not None
            )
        ),
        "transition": _transition(events),
        "trace_path": str(outcome.environment.root / "trace.json"),
        "workspace_path": str(outcome.environment.workspace),
    }


def _aggregate(records: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    selected = [record for record in records if record["arm"] == arm]
    post_cached = sum(
        record["post_first_main_cache"]["cached_input_tokens"]
        for record in selected
    )
    post_inputs = sum(
        record["post_first_main_cache"]["input_tokens"]
        for record in selected
    )
    transition_rows = [
        record["transition"]
        for record in selected
        if record["transition"] is not None
        and record["transition"]["cache_hit_rate"] is not None
    ]
    transition_cached = sum(
        row["cached_input_tokens"] for row in transition_rows
    )
    transition_inputs = sum(row["input_tokens"] for row in transition_rows)
    return {
        "runs": len(selected),
        "passed_runs": sum(record["passed"] for record in selected),
        "transition_observed_runs": sum(
            record["transition"] is not None for record in selected
        ),
        "post_first_main_cached_input_tokens": post_cached,
        "post_first_main_input_tokens": post_inputs,
        "post_first_main_cache_hit_rate": (
            post_cached / post_inputs if post_inputs else None
        ),
        "transition_cached_input_tokens": transition_cached,
        "transition_input_tokens": transition_inputs,
        "transition_cache_hit_rate": (
            transition_cached / transition_inputs if transition_inputs else None
        ),
        "provider_chargeable_tokens": sum(
            record["provider_chargeable_tokens"] for record in selected
        ),
        "duration_s": sum(record["duration_s"] for record in selected),
        "prefix_decisions": dict(
            sum(
                (
                    Counter(record["prefix_decisions"])
                    for record in selected
                ),
                Counter(),
            )
        ),
    }


def _percent(value: float | None) -> str:
    return "未知" if value is None else f"{value * 100:.1f}%"


def render_report(payload: dict[str, Any]) -> str:
    control = payload["aggregates"]["rebuild"]
    treatment = payload["aggregates"]["reuse"]
    valid_pairs = payload["valid_pairs"]
    control_passed = f"{control['passed_runs']}/{control['runs']}"
    treatment_passed = f"{treatment['passed_runs']}/{treatment['runs']}"
    control_transitions = (
        f"{control['transition_observed_runs']}/{control['runs']}"
    )
    treatment_transitions = (
        f"{treatment['transition_observed_runs']}/{treatment['runs']}"
    )
    control_post_rate = _percent(
        control["post_first_main_cache_hit_rate"]
    )
    treatment_post_rate = _percent(
        treatment["post_first_main_cache_hit_rate"]
    )
    control_transition_rate = _percent(
        control["transition_cache_hit_rate"]
    )
    treatment_transition_rate = _percent(
        treatment["transition_cache_hit_rate"]
    )
    post_lift_pp = (
        treatment["post_first_main_cache_hit_rate"]
        - control["post_first_main_cache_hit_rate"]
    ) * 100
    transition_lift_pp = (
        treatment["transition_cache_hit_rate"]
        - control["transition_cache_hit_rate"]
    ) * 100
    chargeable_reduction = 1 - (
        treatment["provider_chargeable_tokens"]
        / control["provider_chargeable_tokens"]
    )
    lines = [
        "# TaskMind 前缀保护专项 A/B 评测",
        "",
        f"- Provider：`{payload['provider']}`",
        f"- Model：`{payload['model']}`",
        f"- 配对数：{payload['pairs']}",
        f"- 生成时间：{payload['generated_at']}",
        "",
        "## 评测口径",
        "",
        "- 场景：长历史 + 4 轮顺序依赖文件读取，输入跨过软压缩线但尽量不越过强制线。",
        "- 对照组：关闭 TaskMind Run 内请求前缀复用，软线处允许立即压缩。",
        "- 实验组：开启前缀复用，前缀稳定时允许 defer。",
        "- 隔离：每个实验臂使用不同的早期 cache namespace；每对交替执行顺序。",
        "- 主指标：排除第一次模型调用后，主模型输入 token 的加权缓存命中率。",
        "- 诊断指标：首次软压缩压力转折点的加权缓存命中率。",
        "",
        "## 结果",
        "",
        "| 指标 | 对照组（rebuild） | 实验组（reuse） |",
        "|---|---:|---:|",
        f"| 完整通过 | {control_passed} | {treatment_passed} |",
        f"| 观察到软线转折 | {control_transitions} | {treatment_transitions} |",
        "| 第二次及后续主调用缓存命中率 | "
        f"{control_post_rate} | {treatment_post_rate} |",
        "| 第二次及后续 cached/input tokens | "
        f"{control['post_first_main_cached_input_tokens']}/"
        f"{control['post_first_main_input_tokens']} | "
        f"{treatment['post_first_main_cached_input_tokens']}/"
        f"{treatment['post_first_main_input_tokens']} |",
        "| 软线转折调用缓存命中率 | "
        f"{control_transition_rate} | {treatment_transition_rate} |",
        "| 软线转折 cached/input tokens | "
        f"{control['transition_cached_input_tokens']}/"
        f"{control['transition_input_tokens']} | "
        f"{treatment['transition_cached_input_tokens']}/"
        f"{treatment['transition_input_tokens']} |",
        "| Provider 可计费 token 近似值 | "
        f"{control['provider_chargeable_tokens']} | "
        f"{treatment['provider_chargeable_tokens']} |",
        f"| 总耗时 | {control['duration_s']:.1f}s | {treatment['duration_s']:.1f}s |",
        "",
        f"- 有效配对：{valid_pairs}/{payload['pairs']}。",
        f"- 对照组决策计数：`{control['prefix_decisions']}`。",
        f"- 实验组决策计数：`{treatment['prefix_decisions']}`。",
        "",
        "## 观察结论",
        "",
        f"- 第二次及后续主调用缓存命中率提高 {post_lift_pp:.1f} 个百分点。",
        f"- 软线转折调用缓存命中率提高 {transition_lift_pp:.1f} 个百分点。",
        f"- Provider 可计费 token 近似值减少 {chargeable_reduction * 100:.1f}%。",
        "",
        "## 解释边界",
        "",
        "只有两组都完成工具链、都观察到软线转折，并且实验组出现 defer、"
        "对照组出现 compact/rebuild，才能把命中率差异用于支持前缀保护机制。"
        "Provider 缓存是尽力而为，三对样本仍属于专项离线证据，不代表生产流量。",
        "",
        "## 逐次运行",
        "",
        "| Pair | Arm | Pass | Steps | Transition | Post-first cache | Chargeable |",
        "|---:|---|---:|---:|---|---:|---:|",
    ]
    for record in payload["records"]:
        transition = record["transition"] or {}
        transition_label = (
            f"step={transition.get('step')}, "
            f"decision={transition.get('prefix_decision')}, "
            f"cache={_percent(transition.get('cache_hit_rate'))}"
            if transition
            else "未观察到"
        )
        lines.append(
            f"| {record['pair_index']} | {record['arm']} | "
            f"{'PASS' if record['passed'] else 'FAIL'} | {record['steps']} | "
            f"{transition_label} | "
            f"{_percent(record['post_first_main_cache']['hit_rate'])} | "
            f"{record['provider_chargeable_tokens']} |"
        )
    return "\n".join(lines) + "\n"


async def main(args: argparse.Namespace) -> int:
    effective = load_effective_model_configuration()
    registry = ModelAdapterRegistry(effective.settings)
    invocation = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    root = (
        args.root / f"prefix-cache-ab-{invocation}"
        if args.root
        else Path(tempfile.mkdtemp(prefix="taskmind-prefix-cache-ab-"))
    )
    output = args.out_dir or _REPORTS_DIR / invocation
    records: list[dict[str, Any]] = []
    try:
        for pair_index in range(1, args.pairs + 1):
            order = ("rebuild", "reuse") if pair_index % 2 else ("reuse", "rebuild")
            for arm in order:
                namespace = f"{invocation}-pair-{pair_index}-{arm}"
                scenario = build_stress_scenario(namespace)
                run_root = root / f"pair-{pair_index}" / arm
                outcome = await harness.run_scenario(
                    scenario,
                    root=run_root,
                    provider=args.provider,
                    model=args.model,
                    registry=registry,
                    prefix_reuse_enabled=arm == "reuse",
                )
                checks, _ = await run_checks(scenario, outcome=outcome)
                # The treatment is expected to *defer* at the soft line, so the
                # generic "requires_compaction" assertion is intentionally not
                # a functional failure for that arm.  It remains required in
                # the control arm to prove that the baseline actually rewrote
                # context instead of merely rebuilding an identical request.
                passed = all(
                    bool(getattr(check, "ok"))
                    for check in checks
                    if bool(getattr(check, "applicable", True))
                    and not (arm == "reuse" and getattr(check, "name") == "compaction")
                )
                write_trace(outcome.events, run_root / "trace.json")
                record = _arm_record(
                    pair_index=pair_index,
                    arm=arm,
                    namespace=namespace,
                    outcome=outcome,
                    checks=checks,
                    passed=passed,
                )
                records.append(record)
                print(
                    f"pair={pair_index} arm={arm} pass={passed} "
                    f"steps={record['steps']} "
                    f"post_cache={_percent(record['post_first_main_cache']['hit_rate'])}"
                )
    finally:
        await registry.close()

    by_pair: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        by_pair.setdefault(record["pair_index"], []).append(record)
    valid_pairs = sum(
        len(pair_records) == 2
        and all(record["passed"] for record in pair_records)
        and all(record["transition"] is not None for record in pair_records)
        and any(
            record["arm"] == "reuse"
            and record["transition"]["prefix_decision"] == "defer"
            for record in pair_records
        )
        and any(
            record["arm"] == "rebuild"
            and record["transition"]["prefix_decision"] in {"compact", "rebuild"}
            for record in pair_records
        )
        for pair_records in by_pair.values()
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": args.provider,
        "model": args.model,
        "pairs": args.pairs,
        "valid_pairs": valid_pairs,
        "run_root": str(root),
        "git_commit": os.environ.get("TASKMIND_EVAL_GIT_COMMIT")
        or os.environ.get("GITHUB_SHA"),
        "aggregates": {
            "rebuild": _aggregate(records, "rebuild"),
            "reuse": _aggregate(records, "reuse"),
        },
        "records": records,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown = render_report(payload)
    (output / "report.md").write_text(markdown, encoding="utf-8")
    print(f"报告：{output / 'report.md'}")
    if args.print:
        print("\n" + markdown)
    return 0 if valid_pairs == args.pairs else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(_parse_args())))
