from __future__ import annotations

import json

import pytest

from app.agent.events import AgentEventType
from tests.eval_legacy import harness
from tests.eval_legacy.mocks import fake_registry, model_response, text_tool_call
from tests.eval_legacy.run_prefix_cache_ab import build_stress_scenario


def _tool_response(index: int):
    return model_response(
        tool_calls=(
            text_tool_call(
                f"read-{index}",
                "read_file",
                {"path": f"chain/step-{index}.txt"},
            ),
        )
    )


def _summary_response():
    return model_response(
        content=json.dumps(
            {
                "current_objective": "complete the sequential audit",
                "user_constraints": ["follow NEXT in order"],
                "key_decisions": [],
                "completed_work": [],
                "current_state": ["step 1 was read"],
                "pending_work": ["continue the chain"],
                "important_facts": ["BRAVO-17"],
            }
        )
    )


async def _run_arm(tmp_path, *, prefix_reuse_enabled: bool):
    responses = [_tool_response(1), _tool_response(2)]
    if not prefix_reuse_enabled:
        responses.append(_summary_response())
    responses.extend(
        (
            _tool_response(3),
            _tool_response(4),
            model_response(
                content="BRAVO-17 DELTA-29 KILO-43 SIERRA-61"
            ),
        )
    )
    registry, _ = fake_registry(responses)
    return await harness.run_scenario(
        build_stress_scenario(
            "reuse" if prefix_reuse_enabled else "rebuild"
        ),
        root=tmp_path / ("reuse" if prefix_reuse_enabled else "rebuild"),
        provider="fake",
        model="fake-model",
        registry=registry,
        prefix_reuse_enabled=prefix_reuse_enabled,
    )


@pytest.mark.asyncio
async def test_prefix_cache_ab_fixture_isolates_soft_line_behavior(tmp_path) -> None:
    control = await _run_arm(tmp_path, prefix_reuse_enabled=False)
    treatment = await _run_arm(tmp_path, prefix_reuse_enabled=True)

    control_started = [
        event
        for event in control.events
        if event.type is AgentEventType.MODEL_STARTED
    ]
    treatment_started = [
        event
        for event in treatment.events
        if event.type is AgentEventType.MODEL_STARTED
    ]

    assert control.result is not None and control.result.steps == 5
    assert treatment.result is not None and treatment.result.steps == 5
    assert len(control.result.tool_calls) == 4
    assert len(treatment.result.tool_calls) == 4

    assert control_started[0].requires_compaction is False
    assert treatment_started[0].requires_compaction is False
    control_transition = next(
        event for event in control_started if event.requires_compaction
    )
    treatment_transition = next(
        event for event in treatment_started if event.requires_compaction
    )
    assert control_transition.step == treatment_transition.step
    assert control_transition.prefix_decision == "compact"
    assert control_transition.summary_updated is True
    assert control_transition.cache_prefix_reused is False
    assert treatment_transition.prefix_decision == "defer"
    assert treatment_transition.summary_updated is False
    assert treatment_transition.cache_prefix_reused is True
    assert max(
        event.estimated_input_tokens or 0 for event in treatment_started
    ) < (treatment_started[-1].compact_ceiling_tokens or 0)
