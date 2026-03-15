import asyncio
import sys

from backend.models.session import SessionState
from backend.services.session_service import analyze_session

def test_manual_conflict_case():
    text = "I have a prior decision that was denied. I am hoping to file a supplemental claim."
    
    # 1. State where the user just submitted the answer "No" to a follow-up about new evidence
    state = SessionState(
        initial_user_text=text,
        conversation_history=[
            {"role": "assistant", "content": "Do you have any new and relevant evidence that VA hasn't seen before?"},
            {"role": "user", "content": "No, I don't have anything new. They just missed my records."}
        ],
        known_facts={"has_va_decision": True, "has_new_evidence": False},
        current_route="supplemental_claim"
    )
    
    print("Running analyze_session...")
    res = analyze_session(state)
    
    print(f"Post-followup route: {res.preliminary_route}")
    print(f"needs_follow_up: {res.needs_follow_up}")
    
    if res.needs_follow_up:
         print(f"follow_up_questions: {res.follow_up_questions}")
    
    if res.final_packet:
        print(f"final_packet.case_type: {res.final_packet.case_type}")
        print(f"final_packet.warnings: {res.final_packet.warnings}")
    else:
        print("No final packet generated.")

if __name__ == "__main__":
    test_manual_conflict_case()
