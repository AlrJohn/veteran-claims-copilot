from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from pydantic import BaseModel, ValidationError

from backend.utils import llm_client
from backend.utils.rules_loader import (
    Rule,
    get_all_rules,
    rules_to_prompt_snippets,
    search_rules_by_trigger,
)


ALLOWED_ROUTES = {"initial_claim", "supplemental_claim", "hlr", "board_explainer", "unclear"}


class RoutingResult(BaseModel):
    route: str
    confidence: float
    rule_hits: List[str]
    notes: str | None = None


@dataclass
class RouterPromptContext:
    user_text: str
    candidate_rules: List[Rule]
    system_instructions: str


def build_router_prompt(ctx: RouterPromptContext) -> str:
    """
    Build a routing prompt that includes only rules from rules.json.
    """
    rules_snippets = rules_to_prompt_snippets(ctx.candidate_rules)
    payload = {
        "instructions": ctx.system_instructions,
        "user_text": ctx.user_text,
        "candidate_rules": rules_snippets,
        "allowed_routes": sorted(ALLOWED_ROUTES),
        "output_schema": {
            "route": "one of the allowed routes",
            "confidence": "number between 0 and 1",
            "rule_hits": "list of rule_id strings from candidate_rules you relied on",
            "notes": "optional short note; do not add new VA rules here",
        },
    }
    return json.dumps(payload, indent=2)


def _load_router_instructions() -> str:
    from pathlib import Path

    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    router_path = prompts_dir / "router.txt"
    return router_path.read_text(encoding="utf-8")


def classify_route_free_text(user_text: str) -> RoutingResult:
    """
    Classify free-text user input into one of the allowed routes.

    If the LLM client is not configured or returns an invalid structure, this
    falls back to the conservative 'unclear' route.
    """
    # Start from all rules but bias candidate list with trigger matches.
    triggered = search_rules_by_trigger(user_text)
    candidate_rules = triggered or get_all_rules()

    ctx = RouterPromptContext(
        user_text=user_text,
        candidate_rules=candidate_rules,
        system_instructions=_load_router_instructions(),
    )
    prompt = build_router_prompt(ctx)

    try:
        raw = llm_client.call_llm(prompt)
    except llm_client.LLMClientError as exc:
        return RoutingResult(
            route="unclear",
            confidence=0.0,
            rule_hits=[],
            notes=f"Routing fell back to 'unclear' because LLM client is not configured: {exc}",
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return RoutingResult(
            route="unclear",
            confidence=0.0,
            rule_hits=[],
            notes="Routing fell back to 'unclear' because LLM output was not valid JSON.",
        )

    # Pydantic validation plus guardrails on route label.
    try:
        result = RoutingResult(**data)
    except ValidationError:
        return RoutingResult(
            route="unclear",
            confidence=0.0,
            rule_hits=[],
            notes="Routing fell back to 'unclear' because LLM output did not match the expected schema.",
        )

    if result.route not in ALLOWED_ROUTES:
        result.route = "unclear"
        result.confidence = 0.0
        result.notes = "Route label was not allowed; normalized to 'unclear'."

    return result

