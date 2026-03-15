import json

from backend.models.session import SessionState
from backend.services.session_service import analyze_session


def _fake_call_llm(prompt: str) -> str:
    payload = json.loads(prompt)
    instructions = payload.get("instructions", "")

    if "routing assistant" in instructions:
        text = payload.get("user_text", "").lower()
        if any(term in text for term in ["board docket", "veterans law judge", "board lane", "board appeal"]):
            route = "board_explainer"
        elif "first time" in text or "no decision" in text:
            route = "initial_claim"
        elif "new evidence" in text and any(term in text for term in ["decision", "denied", "prior"]):
            route = "supplemental_claim"
        elif any(term in text for term in ["higher-level review", "same record", "existing record", "error"]):
            route = "hlr"
        elif "appeal" in text or "deadline" in text:
            # Intentionally over-select board to verify deterministic guardrails.
            route = "board_explainer"
        else:
            route = "unclear"
        return json.dumps(
            {
                "route": route,
                "confidence": 0.9 if route != "unclear" else 0.2,
                "rule_hits": [],
                "notes": "test stub",
            }
        )

    if "follow-up assistant" in instructions:
        return json.dumps(
            {
                "needs_follow_up": False,
                "follow_up_questions": [],
                "known_facts": payload.get("known_facts", {}),
                "missing_facts": [],
                "warnings": [],
            }
        )

    if "packet-generation assistant" in instructions:
        route = payload.get("route", "unclear")
        forms_by_route = {
            "supplemental_claim": [
                "VA Form 20-0996 = Supplemental Claim",
                "VA Form 10182",
                "VA Form 20-0995",
            ],
            "hlr": [
                "VA Form 20-0995",
                "VA Form 20-0996 = Supplemental Claim",
                "VA Form 10182",
            ],
            "board_explainer": [
                "VA Form 20-0996",
                "VA Form 10182",
                "VA Form 20-0995",
            ],
            "initial_claim": ["VA Form 21-526EZ"],
            "unclear": [],
        }
        return json.dumps(
            {
                "case_type": route,
                "confidence": 0.9,
                "why_this_path": ["This route fits.", "Board lanes include Direct Review."],
                "why_not_other_paths": ["Other routes do not fit."],
                "possible_forms": forms_by_route.get(route, []),
                "possible_missing_evidence": [],
                "known_facts": payload.get("known_facts", {}),
                "follow_up_questions": [],
                "warnings": ["Board dockets differ by lane."],
                "citations": [],
                "safety_note": "Educational only.",
                "needs_accredited_help": False,
            }
        )

    raise AssertionError("Unexpected prompt type for test stub.")


def _run_case(text: str, known_facts: dict) -> object:
    state = SessionState(initial_user_text=text, known_facts=known_facts)
    return analyze_session(state)


def test_unsure_after_decision_no_new_evidence_asks_single_targeted_follow_up(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)
    res = _run_case(
        "I got denied, I have no new evidence, and I don't know what to do next with this appeal.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert res.needs_follow_up is True
    assert res.preliminary_route != "board_explainer"
    assert len(res.follow_up_questions) == 1
    assert "same record" in res.follow_up_questions[0].lower()


def test_explicit_board_intent_routes_to_board_explainer(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)
    res = _run_case(
        "I want to understand Board dockets and whether I should ask for a Veterans Law Judge hearing lane.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert res.preliminary_route == "board_explainer"
    assert res.needs_follow_up is False
    assert res.final_packet is not None
    assert res.final_packet.case_type == "board_explainer"


def test_deadline_context_alone_does_not_route_to_board(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)
    res = _run_case(
        "My decision letter is within one year of the deadline and I am not sure what to do next.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert res.preliminary_route != "board_explainer"
    assert res.needs_follow_up is True
    assert len(res.follow_up_questions) == 1


def test_same_record_rereview_no_new_evidence_routes_to_hlr(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)
    res = _run_case(
        "I have a prior denial, no new evidence, and I want VA to re-review the same record for error.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert res.preliminary_route == "hlr"
    assert res.needs_follow_up is False
    assert res.final_packet is not None
    assert res.final_packet.case_type == "hlr"


def test_form_normalization_and_route_consistency(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)

    supplemental = _run_case(
        "I have a prior decision and new evidence for a supplemental claim.",
        {"has_va_decision": True, "has_new_evidence": True},
    )
    assert supplemental.final_packet is not None
    supp_forms = supplemental.final_packet.possible_forms
    assert supp_forms[0] == "VA Form 20-0995 (Supplemental Claim)"
    assert not any("0996" in f.replace("-", "") for f in supp_forms)
    assert not any("10182" in f.replace("-", "") for f in supp_forms)
    assert all("direct review" not in s.lower() for s in supplemental.final_packet.why_this_path + supplemental.final_packet.warnings)

    hlr = _run_case(
        "I want higher-level review on the existing record and have no new evidence.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert hlr.final_packet is not None
    hlr_forms = hlr.final_packet.possible_forms
    assert hlr_forms[0] == "VA Form 20-0996 (Higher-Level Review)"
    assert not any("0995" in f.replace("-", "") for f in hlr_forms)
    assert not any("10182" in f.replace("-", "") for f in hlr_forms)

    board = _run_case(
        "Explain the Board appeal hearing lane and board docket options.",
        {"has_va_decision": True, "has_new_evidence": False},
    )
    assert board.final_packet is not None
    board_forms = board.final_packet.possible_forms
    assert board_forms[0] == "VA Form 10182 (Board Appeal)"
    assert not any("0995" in f.replace("-", "") for f in board_forms)
    assert not any("0996" in f.replace("-", "") for f in board_forms)


def test_regression_initial_and_supplemental_routes(monkeypatch):
    monkeypatch.setattr("backend.utils.llm_client.call_llm", _fake_call_llm)

    initial = _run_case(
        "I am filing for the first time and have not received a VA decision yet.",
        {"has_va_decision": False},
    )
    assert initial.preliminary_route == "initial_claim"
    assert initial.needs_follow_up is False
    assert initial.final_packet is not None
    assert initial.final_packet.case_type == "initial_claim"

    supplemental = _run_case(
        "I already have a VA decision and now I have new evidence.",
        {"has_va_decision": True, "has_new_evidence": True},
    )
    assert supplemental.preliminary_route == "supplemental_claim"
    assert supplemental.needs_follow_up is False
    assert supplemental.final_packet is not None
    assert supplemental.final_packet.case_type == "supplemental_claim"
