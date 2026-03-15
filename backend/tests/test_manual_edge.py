import asyncio
import sys

from backend.models.session import SessionState
from backend.services.session_service import analyze_session

def test_manual_edge_case():
    text = "I want to file a disability claim for the first time. I’m filing online. I have my DD214 and private medical records with a diagnosis. My condition began during service. I have not received a VA decision yet."
    
    state = SessionState(
        initial_user_text=text,
    )
    
    print("Running analyze_session...")
    res = analyze_session(state)
    
    print(f"preliminary_route: {res.preliminary_route}")
    print(f"needs_follow_up: {res.needs_follow_up}")
    
    if res.final_packet:
        print(f"final_packet.case_type: {res.final_packet.case_type}")
        print(f"final_packet.possible_forms: {res.final_packet.possible_forms}")
        print(f"final_packet.why_this_path: {res.final_packet.why_this_path}")
        print(f"final_packet.warnings: {res.final_packet.warnings}")
    else:
        print("No final packet generated (probably needed follow-up).")

if __name__ == "__main__":
    test_manual_edge_case()
