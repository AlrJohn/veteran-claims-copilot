import json
import re
from typing import Dict, Any, List
from backend.models.session import SessionState, AnalyzeResponse, FinalPacket
from backend.services.router_service import classify_route_free_text
from backend.services.explainer_service import generate_explanation, build_explainer_prompt, _rules_for_explainer
from backend.utils import llm_client
from backend.utils.rules_loader import get_all_rules, rules_to_prompt_snippets, search_rules_by_trigger, Rule


CANONICAL_FORMS_BY_ROUTE = {
    "supplemental_claim": "VA Form 20-0995 (Supplemental Claim)",
    "hlr": "VA Form 20-0996 (Higher-Level Review)",
    "board_explainer": "VA Form 10182 (Board Appeal)",
}


def _normalize_text_for_match(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").replace("/", " ").split())


def is_explicit_board_intent(text: str) -> bool:
    normalized = _normalize_text_for_match(text)
    board_terms = [
        "board appeal",
        "board of veterans appeals",
        "bva",
        "veterans law judge",
        "judge review",
        "board judge",
        "board docket",
        "board dockets",
        "docket",
        "direct review",
        "evidence submission",
        "hearing lane",
        "board lane",
        "board lanes",
    ]
    return any(term in normalized for term in board_terms)


def is_same_record_rereview_intent(text: str) -> bool:
    normalized = _normalize_text_for_match(text)
    rereview_terms = [
        "re review",
        "review again",
        "review for error",
        "same record",
        "existing record",
        "higher level review",
        "hlr",
        "made an error",
        "missed evidence",
        "wrong decision",
    ]
    return any(term in normalized for term in rereview_terms)


def is_unsure_next_steps(text: str) -> bool:
    normalized = _normalize_text_for_match(text)
    unsure_terms = [
        "unsure",
        "dont know what to do next",
        "don't know what to do next",
        "do not know what to do next",
        "what should i do next",
        "what do i do next",
        "not sure what to do next",
        "not sure what to do",
        "i dont know what to do",
        "i don't know what to do",
        "i do not know what to do",
        "uncertain what to do next",
    ]
    return any(term in normalized for term in unsure_terms)


def _is_board_deadline_only_context(text: str) -> bool:
    normalized = _normalize_text_for_match(text)
    mentions_deadline = any(
        term in normalized for term in ["within 1 year", "one year", "deadline", "60 days", "sixty days"]
    )
    return mentions_deadline and not is_explicit_board_intent(text)


def _canonicalize_form_label(form_text: str) -> str:
    normalized = form_text.lower().replace(" ", "").replace("-", "")
    if "200995" in normalized or "0995" in normalized:
        return CANONICAL_FORMS_BY_ROUTE["supplemental_claim"]
    if "200996" in normalized or "0996" in normalized:
        return CANONICAL_FORMS_BY_ROUTE["hlr"]
    if "10182" in normalized:
        return CANONICAL_FORMS_BY_ROUTE["board_explainer"]
    return form_text.strip()


def _form_matches_route(form_text: str, route: str) -> bool:
    normalized = form_text.lower().replace(" ", "").replace("-", "")
    if "0995" in normalized:
        return route == "supplemental_claim"
    if "0996" in normalized:
        return route == "hlr"
    if "10182" in normalized:
        return route == "board_explainer"
    return True


def _mentions_board_lane_details(text: str) -> bool:
    normalized = _normalize_text_for_match(text)
    lane_terms = [
        "direct review",
        "evidence submission",
        "hearing lane",
        "board lane",
        "board lanes",
        "board docket",
        "board dockets",
        "veterans law judge",
    ]
    return any(term in normalized for term in lane_terms)


def _load_prompt(filename: str) -> str:
    from pathlib import Path
    return (Path(__file__).resolve().parents[1] / "prompts" / filename).read_text(encoding="utf-8")


def _strip_internal_rule_refs(text: str) -> str:
    """
    Remove internal rule IDs (e.g., RULE_IC_001) from user-facing prose.
    """
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r"\(\s*RULE_[A-Z0-9_]+\s*\)", "", text)
    cleaned = re.sub(r"\bRULE_[A-Z0-9_]+\b", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned


def _clean_user_facing_packet_text(packet_dict: Dict[str, Any]) -> Dict[str, Any]:
    for key in [
        "why_this_path",
        "why_not_other_paths",
        "possible_missing_evidence",
        "warnings",
        "follow_up_questions",
        "possible_forms",
    ]:
        values = packet_dict.get(key, [])
        if isinstance(values, list):
            cleaned_values = []
            for value in values:
                text = _strip_internal_rule_refs(str(value))
                if text:
                    cleaned_values.append(text)
            packet_dict[key] = cleaned_values
    if isinstance(packet_dict.get("safety_note"), str):
        packet_dict["safety_note"] = _strip_internal_rule_refs(packet_dict["safety_note"])
    return packet_dict

def _enforce_route_precedence(route: str, full_text: str, known_facts: Dict[str, Any]) -> str:
    """
    Enforce explicit route precedence based on facts to prevent 'unclear'.
    """
    text_lower = full_text.lower()
    
    # Check for initial claim indicators (first time, no decision)
    is_first_time = known_facts.get("first_time_filer", False) or "first time" in text_lower or "new claim" in text_lower
    has_no_decision = known_facts.get("has_va_decision") is False or "no decision" in text_lower or "not received a va decision yet" in text_lower or "not received a decision" in text_lower
    filing_526 = "526ez" in text_lower or "526" in text_lower

    if is_first_time or has_no_decision or filing_526:
        return "initial_claim"

    # Check for supplemental claim indicators (new evidence, prior decision)
    has_prior_decision = known_facts.get("has_va_decision", False) or "already have a decision" in text_lower or "was denied" in text_lower
    has_new_evidence = known_facts.get("has_new_evidence", False) or "new evidence" in text_lower
    if has_prior_decision and has_new_evidence:
        return "supplemental_claim"

    # Check for HLR (error, prior decision, no new evidence)
    says_error = "made an error" in text_lower or "higher level" in text_lower or "missed evidence" in text_lower
    if has_prior_decision and not has_new_evidence and (says_error or is_same_record_rereview_intent(full_text)):
        return "hlr"

    # Check for explicit Board appeal intent only (not generic appeal/deadline context).
    if is_explicit_board_intent(full_text):
        return "board_explainer"

    return route

def _validate_route_against_known_facts(route: str, known_facts: Dict[str, Any], full_text: str) -> tuple[bool, str]:
    """
    Validate if the selected route is contradicted by known facts.
    Returns (is_valid, reason_if_invalid)
    """
    text_lower = full_text.lower()
    has_va_decision = known_facts.get("has_va_decision")
    has_new_evidence = known_facts.get("has_new_evidence")

    if route == "supplemental_claim":
        if has_va_decision is True and has_new_evidence is False:
            return False, "Supplemental Claim requires new and relevant evidence."
            
    if route == "hlr":
        if has_va_decision is True and has_new_evidence is True:
            return False, "Higher-Level Review does not allow new evidence."
            
    if route == "initial_claim":
        # If user explicitly states they have a decision and are trying to appeal/review the same issue
        if has_va_decision is True and ("denied" in text_lower or "appeal" in text_lower):
            return False, "Initial claim fits a new issue, but user is discussing a prior decision."
            
    if route == "board_explainer":
        # Ensure they actually gave explicit Board intent.
        if not is_explicit_board_intent(full_text):
            return False, "Board appeal was selected, but explicit Board intent was not found."
        # If they are just unsure what to do next with a prior decision and no new evidence, that's not board.
        if is_unsure_next_steps(full_text):
            if has_va_decision and not has_new_evidence and not is_explicit_board_intent(full_text):
                return False, "User is unsure what to do after a decision, NOT explicitly requesting a Board appeal."

    return True, ""


def _reroute_if_conflicted(invalid_route: str, known_facts: Dict[str, Any], full_text: str) -> str:
    """
    Attempt to reroute if a conflict was detected.
    """
    text_lower = full_text.lower()
    
    if invalid_route == "supplemental_claim":
        # Supplemental was invalid because they have NO new evidence.
        if (
            "error" in text_lower
            or "missed" in text_lower
            or "higher level" in text_lower
            or is_same_record_rereview_intent(full_text)
        ):
            return "hlr"
        return "unclear"
        
    if invalid_route == "hlr":
        # HLR was invalid because they DO have new evidence.
        return "supplemental_claim"
        
    if invalid_route == "initial_claim":
        if known_facts.get("has_new_evidence"):
            return "supplemental_claim"
        if "error" in text_lower.replace("-", " ") or is_same_record_rereview_intent(full_text):
            return "hlr"
        return "unclear"
        
    if invalid_route == "board_explainer":
        if known_facts.get("has_va_decision") is True and known_facts.get("has_new_evidence") is False:
            if is_same_record_rereview_intent(full_text):
                return "hlr"
        return "unclear"
        
    return "unclear"

def _final_packet_consistency_check(packet_dict: Dict[str, Any], route: str, known_facts: Dict[str, Any], full_text: str) -> Dict[str, Any]:
    """
    Check the final packet to assure the LLM didn't spit out contradictory arrays.
    """
    case_type = packet_dict.get("case_type", route)
    
    # 1. Ensure the emitted case_type itself is legally valid
    is_valid, _ = _validate_route_against_known_facts(case_type, known_facts, full_text)
    if not is_valid:
         packet_dict["case_type"] = "unclear"
         packet_dict["warnings"].append(f"The system detected a conflict: the initially chosen {case_type} path is invalid based on your facts.")
         packet_dict["confidence"] = 0.0
         return packet_dict
         
    # 2. Check if the LLM hallucinated a direct negation in why_not_other_paths
    for reason in packet_dict.get("why_not_other_paths", []):
         if "does not fit" in reason.lower() and case_type.lower().replace("_", " ") in reason.lower():
              packet_dict["case_type"] = "unclear"
              packet_dict["warnings"].append("The system explanation generated conflicting logic regarding the path.")
              packet_dict["confidence"] = 0.0
              return packet_dict
              
    return packet_dict

def analyze_session(state: SessionState) -> AnalyzeResponse:
    """
    Unified entry point for multi-step session analysis.
    """
    # 1. Compile the full context text
    full_text = f"Initial user input: {state.initial_user_text}\n"
    for turn in state.conversation_history:
        role = "User" if turn.get("role") == "user" else "Assistant"
        full_text += f"{role}: {turn.get('content')}\n"

    # Gather known facts
    known_facts = state.known_facts.copy()

    # 2. Determine preliminary route if we don't have one, or if we want to confirm
    routing = classify_route_free_text(full_text)
    route = routing.route
    confidence = routing.confidence

    # Execute code-level route precedence overrides
    enforced_route = _enforce_route_precedence(route, full_text, known_facts)
    # If we overrode standard routing, give it high confidence
    if enforced_route != route:
        route = enforced_route
        confidence = 0.95

    # Deterministic route guardrails for Board and HLR.
    if route == "board_explainer" and not is_explicit_board_intent(full_text):
        route = "unclear"
        confidence = 0.0
    if _is_board_deadline_only_context(full_text) and route == "board_explainer":
        route = "unclear"
        confidence = 0.0
    if known_facts.get("has_va_decision") is True and known_facts.get("has_new_evidence") is False:
        if is_same_record_rereview_intent(full_text):
            route = "hlr"
            confidence = 0.95

    # 3. Determine if we need follow-up
    # We will build a prompt to decide on follow-up questions ONLY if not highly confident
    rules = search_rules_by_trigger(full_text) or get_all_rules()
    
    needs_follow_up = False
    follow_up_qs = []
    missing_facts = []
    warnings = []

    # Deterministic targeted follow-up for ambiguous post-decision/no-new-evidence "what next?" cases.
    if (
        known_facts.get("has_va_decision") is True
        and known_facts.get("has_new_evidence") is False
        and is_unsure_next_steps(full_text)
        and not is_explicit_board_intent(full_text)
        and not is_same_record_rereview_intent(full_text)
    ):
        return AnalyzeResponse(
            needs_follow_up=True,
            follow_up_questions=[
                "Do you want VA to re-review the same record for a possible error (Higher-Level Review), or do you want to add new and relevant evidence (Supplemental Claim)?"
            ],
            preliminary_route="unclear",
            preliminary_confidence=0.0,
            known_facts=known_facts,
            missing_facts=["review_intent"],
            citations=[],
            warnings=warnings,
            final_packet=None,
        )

    # Skip follow up if route is clear and confident
    if route != "unclear" and confidence > 0.85:
        needs_follow_up = False
    else:
        follow_up_prompt = json.dumps({
            "instructions": _load_prompt("follow_up.txt"),
            "route": route,
            "full_conversation": full_text,
            "known_facts": known_facts,
            "rules": rules_to_prompt_snippets(rules),
            "output_schema": {
                "needs_follow_up": "boolean",
                "follow_up_questions": "list of 1-3 targeted follow-up questions to ask the user, or empty list if confident",
                "known_facts": "dictionary of currently known useful facts",
                "missing_facts": "list of key facts we still need to know based on rules",
                "warnings": "list of warnings"
            }
        }, indent=2)

        try:
            raw_fu = llm_client.call_llm(follow_up_prompt)
            fu_data = json.loads(raw_fu)
            needs_follow_up = fu_data.get("needs_follow_up", False)
            follow_up_qs = fu_data.get("follow_up_questions", [])
            extracted_facts = fu_data.get("known_facts", fu_data.get("extracted_facts", {}))
            missing_facts = fu_data.get("missing_facts", [])
            warnings = fu_data.get("warnings", [])
            if isinstance(extracted_facts, dict):
                known_facts.update(extracted_facts)
        except Exception:
            # Fallback if LLM fails
            needs_follow_up = False
            follow_up_qs = []
            missing_facts = []
            warnings = []

    # NEW: Validate conflicts AFTER follow-up facts are extracted
    # Doing this locally limits LLM drift on rule adherence
    is_valid, validation_reason = _validate_route_against_known_facts(route, known_facts, full_text)
    
    if not is_valid:
        new_route = _reroute_if_conflicted(route, known_facts, full_text)
        
        # If we safely rerouted to a new path entirely
        if new_route != "unclear":
             route = new_route
             confidence = 0.8
             needs_follow_up = False # we have resolved it
        else:
             route = "unclear"
             confidence = 0.0
             
             if len(follow_up_qs) == 0:
                  needs_follow_up = True
                  if "supplemental" in validation_reason.lower():
                       follow_up_qs.append("Do you want VA to re-review the same record because you think there was an error, or are you trying to add new evidence?")
                  elif "higher-level" in validation_reason.lower():
                       follow_up_qs.append("Are you sure you have new evidence? HLR does not allow new evidence to be considered.")
                  elif "unsure" in validation_reason.lower() and "board" in validation_reason.lower():
                       follow_up_qs.append("Since you already have a decision, do you have new evidence to add, or do you want VA to re-review the same record for an error?")
                  else:
                       follow_up_qs.append(f"There's a conflict: {validation_reason}. Can you clarify?")

    # If follow-up is needed, return early
    if needs_follow_up and follow_up_qs:
        return AnalyzeResponse(
            needs_follow_up=True,
            follow_up_questions=follow_up_qs,
            preliminary_route=route,
            preliminary_confidence=confidence,
            known_facts=known_facts,
            missing_facts=missing_facts,
            citations=[],  # For intermediate steps, citations can be deferred
            warnings=warnings,
            final_packet=None
        )

    # 4. If no follow-up needed, generate the final packet
    rules_subset = _rules_for_explainer(route)
    explainer_prompt = json.dumps({
        "instructions": _load_prompt("explainer.txt"),
        "route": route,
        "full_conversation": full_text,
        "known_facts": known_facts,
        "decision_context": {"known_facts": known_facts},
        "rules": rules_to_prompt_snippets(rules_subset),
        "output_schema": {
            "case_type": "string, usually equal to the route",
            "confidence": "number between 0 and 1 reflecting how well the rules fit",
            "why_this_path": "list of strings explaining why, grounded in rules",
            "why_not_other_paths": "list of strings explaining why other paths were ruled out",
            "possible_forms": "list of VA form numbers/names that appear in the provided rules, if any",
            "possible_missing_evidence": "list of evidence gaps described using rule language only",
            "known_facts": "dictionary of the confirmed facts from the conversation",
            "follow_up_questions": "empty list (as we decided not to follow up, but keep for schema)",
            "warnings": "list of cautionary notes grounded in rule warnings",
            "safety_note": "short reminder about educational, non-representative scope",
            "needs_accredited_help": "boolean, true if case is complex or user mentioned Board/denials/unclear path"
        }
    }, indent=2)

    try:
        raw_ex = llm_client.call_llm(explainer_prompt)
        ex_data = json.loads(raw_ex)
    except Exception:
        ex_data = {
            "case_type": route or "unclear",
            "confidence": confidence,
            "why_this_path": ["Explanation service could not complete the final packet."],
            "why_not_other_paths": [],
            "possible_forms": [],
            "possible_missing_evidence": [],
            "known_facts": known_facts,
            "follow_up_questions": [],
            "warnings": ["LLM fallback"],
            "safety_note": "This tool is educational and organizational only.",
            "needs_accredited_help": True
        }

    # Extract rule IDs and build full citations via citation_service
    from backend.services.citation_service import extract_rule_ids_from_packet, build_citations
    rule_ids = extract_rule_ids_from_packet(ex_data)
    citations_data = build_citations(rule_ids)

    # Convert citations to Citation objects
    citations = []
    for c in citations_data:
        citations.append({
            "rule_id": c.get("rule_id", ""),
            "source_title": c.get("source_title", ""),
            "source_url": c.get("source_url", ""),
            "source_excerpt": c.get("source_excerpt", "")
        })

    ex_data["citations"] = citations

    # Post processing: Ensure a valid route is NOT downgraded to unclear in the final output
    if route != "unclear" and ex_data.get("case_type") == "unclear":
         ex_data["case_type"] = route
    # Note: If facts *explicitly* conflicted, code route precedence already set it to unclear, 
    # but here we prevent the explainer LLM from doing it purely out of caution.

    # Form Filtering & Prioritization
    raw_forms = ex_data.get("possible_forms", [])
    filtered_forms = []
    for f in raw_forms:
         if "21-22" in f and not ex_data.get("needs_accredited_help", False) and "represent" not in full_text.lower():
              continue # Skip 21-22 if uncalled for
         filtered_forms.append(_canonicalize_form_label(f))

    if ex_data.get("case_type") == "initial_claim":
         # Prioritize 526EZ to the very top
         filtered_forms.sort(key=lambda x: "526ez" not in x.lower())
         
    # Enforce correct forms based on final case_type
    final_case_type = ex_data.get("case_type")
    strict_forms = []
    for f in filtered_forms:
         if not _form_matches_route(f, final_case_type):
              continue
         strict_forms.append(f)

    # Add canonical mapped form first for decision-review routes.
    canonical_form = CANONICAL_FORMS_BY_ROUTE.get(final_case_type)
    if canonical_form:
         strict_forms = [f for f in strict_forms if _canonicalize_form_label(f) != canonical_form]
         strict_forms.insert(0, canonical_form)

    # Deduplicate while preserving order.
    deduped_forms = []
    seen_forms = set()
    for form in strict_forms:
         canonical = _canonicalize_form_label(form)
         if canonical in seen_forms:
              continue
         seen_forms.add(canonical)
         deduped_forms.append(canonical)
    strict_forms = deduped_forms

    ex_data["possible_forms"] = strict_forms

    # Keep board lane details scoped to board route.
    final_case_type = ex_data.get("case_type")
    if final_case_type != "board_explainer":
        for key in ["why_this_path", "why_not_other_paths", "warnings"]:
            values = ex_data.get(key, [])
            if isinstance(values, list):
                ex_data[key] = [v for v in values if not _mentions_board_lane_details(str(v))]

    # Remove internal rule IDs from user-facing prose.
    ex_data = _clean_user_facing_packet_text(ex_data)
    
    # NEW: Final packet validation logic
    ex_data = _final_packet_consistency_check(ex_data, route, known_facts, full_text)

    try:
        final_packet = FinalPacket(**ex_data)
    except Exception as e:
        print("FinalPacket validation error:", e)
        # Fallback on valid packet
        final_packet = FinalPacket(
            case_type=route or "unclear",
            confidence=0.0,
            why_this_path=["Validation error on final packet."],
            why_not_other_paths=[],
            possible_forms=[],
            possible_missing_evidence=[],
            known_facts=known_facts,
            follow_up_questions=[],
            warnings=[],
            citations=[],
            safety_note="This tool is educational and organizational only.",
            needs_accredited_help=True
        )

    return AnalyzeResponse(
        needs_follow_up=False,
        follow_up_questions=[],
        preliminary_route=route,
        preliminary_confidence=confidence,
        known_facts=known_facts,
        missing_facts=missing_facts,
        citations=citations,
        warnings=warnings,
        final_packet=final_packet
    )
