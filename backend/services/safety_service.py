from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from backend.utils import llm_client


class SafetyResult(BaseModel):
    approved: bool
    issues: List[str]
    revised_response: Optional[Dict[str, Any]] = None


def _load_safety_instructions() -> str:
    from pathlib import Path

    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    safety_path = prompts_dir / "safety.txt"
    return safety_path.read_text(encoding="utf-8")


def build_safety_prompt(candidate_packet: Dict[str, Any]) -> str:
    """
    Build a safety-review prompt around a structured packet.
    """
    instructions = _load_safety_instructions()
    payload = {
        "instructions": instructions,
        "candidate_packet": candidate_packet,
        "output_schema": {
            "approved": "boolean; false if any strong safety issues are found",
            "notes": "short explanation of any concerns, including legal-advice-like language or guarantees",
            "suggested_revision": "optional revised packet text or structure that removes unsafe language",
        },
    }
    return json.dumps(payload, indent=2)


def run_safety_check(packet: Dict[str, Any]) -> SafetyResult:
    """
    Run the safety layer on a structured response packet.

    If the LLM client is unavailable or output is invalid, fall back to
    approving the packet but add a conservative note to the issues list.
    """
    prompt = build_safety_prompt(packet)

    try:
        raw = llm_client.call_llm(prompt)
    except llm_client.LLMClientError as exc:
        return SafetyResult(
            approved=True,
            issues=[
                "Safety model is not configured; defaulting to basic safety checks only.",
                f"LLM client error: {exc}",
            ],
            revised_response=None,
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return SafetyResult(
            approved=True,
            issues=["Safety model returned non-JSON output; passing through original packet."],
            revised_response=None,
        )

    class _RawSafety(BaseModel):
        approved: bool
        notes: str
        suggested_revision: Optional[Dict[str, Any]] = None

    try:
        parsed = _RawSafety(**data)
    except ValidationError:
        return SafetyResult(
            approved=True,
            issues=["Safety model output did not match expected schema; passing through original packet."],
            revised_response=None,
        )

    issues: List[str] = []
    if parsed.notes:
        issues.append(parsed.notes)

    return SafetyResult(
        approved=parsed.approved,
        issues=issues,
        revised_response=parsed.suggested_revision,
    )

