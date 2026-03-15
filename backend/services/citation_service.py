from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from backend.utils.rules_loader import Rule, get_all_rules


def build_citations(rule_ids: Sequence[str]) -> List[Dict[str, Any]]:
    """
    Build citation objects from rule_ids, strictly using rules.json.
    """
    rules_by_id = {r.rule_id: r for r in get_all_rules()}
    citations: List[Dict[str, Any]] = []
    for rid in rule_ids:
        rule: Rule | None = rules_by_id.get(rid)
        if not rule:
            continue
        citations.append(
            {
                "rule_id": rule.rule_id,
                "topic": rule.topic,
                "source_title": rule.source_title,
                "source_url": rule.source_url,
                "source_excerpt": rule.source_excerpt,
            }
        )
    return citations


def extract_rule_ids_from_packet(packet: Dict[str, Any]) -> List[str]:
    """
    Helper to collect rule_ids from a packet's existing citations list, if any.
    """
    ids: List[str] = []
    for citation in packet.get("citations", []):
        rid = citation.get("rule_id")
        if isinstance(rid, str):
            ids.append(rid)
    return ids

