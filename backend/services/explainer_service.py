from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from backend.utils import llm_client
from backend.utils.rules_loader import Rule, get_rules_by_route, rules_to_prompt_snippets


class ExplanationResult(BaseModel):
    case_type: str
    confidence: float
    why_this_path: str
    possible_forms: List[str]
    possible_missing_evidence: List[str]
    follow_up_questions: List[str]
    warnings: List[str]
    citations: List[Dict[str, Any]]
    safety_note: str


def _load_explainer_instructions() -> str:
    from pathlib import Path

    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    explainer_path = prompts_dir / "explainer.txt"
    return explainer_path.read_text(encoding="utf-8")


def _rules_for_explainer(route: str, extra_rules: Optional[List[Rule]] = None) -> List[Rule]:
    base = get_rules_by_route(route) if route else []
    if extra_rules:
        known_ids = {r.rule_id for r in base}
        for r in extra_rules:
            if r.rule_id not in known_ids:
                base.append(r)
    return base


def build_explainer_prompt(
    user_text: str,
    route: str,
    rules_subset: List[Rule],
    decision_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build an explanation prompt that is grounded only in rules.json.
    """
    instructions = _load_explainer_instructions()
    snippets = rules_to_prompt_snippets(rules_subset)
    payload = {
        "instructions": instructions,
        "route": route,
        "user_text": user_text,
        "decision_context": decision_context or {},
        "rules": snippets,
        "output_schema": {
            "case_type": "string, usually equal to the route",
            "confidence": "number between 0 and 1 reflecting how well the rules fit",
            "why_this_path": "short explanation grounded in the provided rules only",
            "possible_forms": "list of VA form numbers or names that appear in the provided rules, if any",
            "possible_missing_evidence": "list of evidence gaps described using rule language only",
            "follow_up_questions": "list of clarifying questions",
            "warnings": "list of cautionary notes grounded in rule warnings",
            "citations": "list of {rule_id, source_title, source_url} drawn from the provided rules",
            "safety_note": "short reminder about educational, non-representative scope",
        },
    }
    return json.dumps(payload, indent=2)


def generate_explanation(
    user_text: str,
    route: str,
    decision_context: Optional[Dict[str, Any]] = None,
) -> ExplanationResult:
    """
    Generate a structured explanation for a selected route.

    If the LLM client is unavailable or output is invalid, return a conservative,
    rules-light explanation that clearly marks its limitations.
    """
    rules_subset = _rules_for_explainer(route)
    prompt = build_explainer_prompt(user_text, route, rules_subset, decision_context)

    try:
        raw = llm_client.call_llm(prompt)
    except llm_client.LLMClientError as exc:
        return ExplanationResult(
            case_type=route or "unclear",
            confidence=0.0,
            why_this_path="Explanation service could not contact the language model.",
            possible_forms=[],
            possible_missing_evidence=[],
            follow_up_questions=[],
            warnings=[f"LLM client is not configured: {exc}"],
            citations=[],
            safety_note=(
                "This tool is educational and organizational only. It does not provide legal advice, "
                "cannot predict outcomes, and is not a representative."
            ),
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ExplanationResult(
            case_type=route or "unclear",
            confidence=0.0,
            why_this_path="Explanation fell back to a safe default because the model did not return valid JSON.",
            possible_forms=[],
            possible_missing_evidence=[],
            follow_up_questions=[],
            warnings=["Model output was not valid JSON."],
            citations=[],
            safety_note=(
                "This tool is educational and organizational only. It does not provide legal advice."
            ),
        )

    try:
        return ExplanationResult(**data)
    except ValidationError:
        return ExplanationResult(
            case_type=route or "unclear",
            confidence=0.0,
            why_this_path="Explanation fell back to a safe default because the model output did not match the expected schema.",
            possible_forms=[],
            possible_missing_evidence=[],
            follow_up_questions=[],
            warnings=["Model output did not match the expected schema."],
            citations=[],
            safety_note=(
                "This tool is educational and organizational only. It does not provide legal advice."
            ),
        )

