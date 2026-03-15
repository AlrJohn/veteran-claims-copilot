from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError


class Rule(BaseModel):
    rule_id: str
    topic: str
    route: str
    trigger_signals: List[str]
    official_rule: str
    copilot_action: str
    warning: str
    source_title: str
    source_url: str
    source_excerpt: str


RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "rules.json"


@lru_cache(maxsize=1)
def load_rules() -> List[Rule]:
    """
    Load and validate rules from rules.json once.

    This is the only place in the backend that reads official VA process logic.
    """
    with RULES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("rules.json must contain a top-level JSON array of rule objects.")

    rules: List[Rule] = []
    for raw in data:
        try:
            rules.append(Rule(**raw))
        except ValidationError as exc:
            # Surface configuration errors early during app startup.
            raise ValueError(f"Invalid rule entry in rules.json: {exc}") from exc
    return rules


def get_all_rules() -> List[Rule]:
    return load_rules()


def get_rules_by_route(route: str) -> List[Rule]:
    return [r for r in load_rules() if r.route == route]


def search_rules_by_trigger(text: str) -> List[Rule]:
    """
    Simple keyword-based search over trigger_signals.

    This is intentionally lightweight and does not add any new VA logic beyond
    what is already encoded in rules.json.
    """
    text_lower = text.lower()
    matches: List[Rule] = []
    for rule in load_rules():
        for signal in rule.trigger_signals:
            if signal.lower() in text_lower:
                matches.append(rule)
                break
    return matches


def rules_to_prompt_snippets(rules: List[Rule]) -> List[Dict[str, Any]]:
    """
    Convert rules into compact snippets suitable for inclusion in prompts.
    """
    return [
        {
            "rule_id": r.rule_id,
            "topic": r.topic,
            "route": r.route,
            "official_rule": r.official_rule,
            "copilot_action": r.copilot_action,
            "warning": r.warning,
            "source_title": r.source_title,
            "source_url": r.source_url,
        }
        for r in rules
    ]

