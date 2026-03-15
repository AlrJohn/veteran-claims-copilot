import sys
from backend.models.session import SessionState
from backend.services.session_service import analyze_session

def test_board_unsure_case():
    text = "I received a denial decision. I don't have new evidence and I am unsure what to do next."
    state = SessionState(
        initial_user_text=text,
        known_facts={"has_va_decision": True, "has_new_evidence": False},
        current_route="board_explainer"
    )
    res = analyze_session(state)
    print("--- Board Unsure Case ---")
    print(f"Post-followup route: {res.preliminary_route}")
    print(f"needs_follow_up: {res.needs_follow_up}")
    if res.needs_follow_up:
        print(f"follow_up_qs: {res.follow_up_questions}")

def test_form_mapping_case():
    text = "I want to file a supplemental claim. I have a prior decision and new evidence."
    state = SessionState(
        initial_user_text=text,
        known_facts={"has_va_decision": True, "has_new_evidence": True},
        current_route="supplemental_claim"
    )
    res = analyze_session(state)
    print("--- Form Mapping Case (Supplemental) ---")
    if res.final_packet:
        print(f"case_type: {res.final_packet.case_type}")
        print(f"forms: {res.final_packet.possible_forms}")
    else:
        print("No final packet generated.")

if __name__ == "__main__":
    test_board_unsure_case()
    test_form_mapping_case()
