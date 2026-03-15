from __future__ import annotations

from pathlib import Path

from backend.data import sample_cases
from backend.models.session import SessionState
from backend.services.session_service import analyze_session


def main() -> None:
  cases = sample_cases.SAMPLE_CASES.get("cases", [])
  print(f"Running {len(cases)} sample cases...")
  for case in cases:
    summary = case.get("summary", "")
    expected_route = case.get("route")
    state = SessionState(initial_user_text=summary)
    result = analyze_session(state)
    print("-" * 40)
    print(f"Case ID: {case.get('id')}")
    print(f"Expected route: {expected_route}")
    print(f"Predicted route: {result.preliminary_route} (confidence={result.preliminary_confidence})")
    print(f"Needs follow up: {result.needs_follow_up}")
    if result.needs_follow_up:
        print(f"Questions: {result.follow_up_questions}")
    elif result.final_packet:
        print(f"Why this path: {result.final_packet.why_this_path}")


if __name__ == "__main__":
  # Allow running via `python -m backend.tests.test_sample_cases`
  main()

