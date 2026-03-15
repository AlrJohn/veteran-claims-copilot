from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.data import sample_cases  # type: ignore[import-not-found]
from backend.services.document_parser import extract_text_from_pdf, parse_decision_letter
from backend.services.explainer_service import ExplanationResult, generate_explanation
from backend.services.router_service import RoutingResult, classify_route_free_text
from backend.services.safety_service import SafetyResult, run_safety_check
from backend.services.citation_service import build_citations, extract_rule_ids_from_packet
from backend.utils.rules_loader import get_all_rules
from backend.models.session import SessionState, AnalyzeResponse
from backend.services.session_service import analyze_session


router = APIRouter(prefix="/api")


class ClassifyRequest(BaseModel):
    user_text: str


class ExplainRequest(BaseModel):
    user_text: str
    route: Optional[str] = None
    decision_context: Optional[Dict[str, Any]] = None


@router.post("/classify/route/", response_model=RoutingResult)
async def classify_route_endpoint(payload: ClassifyRequest) -> RoutingResult:
    """
    Route classification endpoint backed by router_service.
    """
    return classify_route_free_text(payload.user_text)


@router.post("/explain/", response_model=ExplanationResult)
async def explain_endpoint(payload: ExplainRequest) -> ExplanationResult:
    """
    Explanation endpoint: generate explanation and apply safety pass.
    """
    route = payload.route or "unclear"
    explanation = generate_explanation(
        user_text=payload.user_text,
        route=route,
        decision_context=payload.decision_context,
    )

    packet_dict: Dict[str, Any] = explanation.dict()
    safety: SafetyResult = run_safety_check(packet_dict)
    if safety.revised_response:
        # Preserve schema if possible; otherwise, fall back to original explanation.
        try:
            explanation = ExplanationResult(**safety.revised_response)
        except Exception:  # noqa: BLE001
            pass

    # Ensure citations map to rules.json.
    rule_ids = extract_rule_ids_from_packet(explanation.dict())
    explanation.citations = build_citations(rule_ids)

    return explanation


@router.post("/session/analyze", response_model=AnalyzeResponse)
async def session_analyze_endpoint(state: SessionState) -> AnalyzeResponse:
    """
    Unified endpoint for multi-step session analysis.
    """
    result = analyze_session(state)
    
    if result.final_packet:
        safety = run_safety_check(result.final_packet.dict())
        if safety.revised_response:
            result.final_packet.safety_note = safety.revised_response.get("safety_note", result.final_packet.safety_note)
            if "warnings" in safety.revised_response:
                result.final_packet.warnings = safety.revised_response["warnings"]
                
    return result


@router.post("/decision-letter/")
async def decision_letter_endpoint(
    file: UploadFile = File(...),
    user_text: str = Body("", embed=True),
) -> Dict[str, Any]:
    """
    Decision-letter endpoint: extract text, build a basic profile, route, explain, and run safety.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported for decision letters.")

    content = await file.read()
    raw_text, ocr_used, text_conf = extract_text_from_pdf(content)
    parsed = parse_decision_letter(raw_text)

    profile = {
        "user_text": user_text,
        "parsed_letter": parsed,
    }

    state = SessionState(
        initial_user_text=user_text or raw_text,
        uploaded_letter_present=True,
        known_facts={"parsed_letter": parsed}
    )
    result = analyze_session(state)
    
    if result.final_packet:
        safety = run_safety_check(result.final_packet.dict())
        if safety.revised_response:
            result.final_packet.safety_note = safety.revised_response.get("safety_note", result.final_packet.safety_note)
            if "warnings" in safety.revised_response:
                result.final_packet.warnings = safety.revised_response["warnings"]

    return {
        "parse_confidence": parsed.get("parse_confidence", text_conf),
        "ocr_used": ocr_used,
        "parse_notes": parsed.get("parse_notes"),
        "user_case_profile": profile,
        "session_response": result.dict()
    }


@router.get("/sample-cases/")
async def sample_cases_endpoint() -> Dict[str, Any]:
    """
    Expose sample cases for frontend demo/testing.
    """
    return sample_cases.SAMPLE_CASES  # type: ignore[attr-defined]


@router.post("/sample-cases/run/")
async def sample_cases_run_endpoint() -> Dict[str, Any]:
    """
    Run session analysis for each sample case.
    """
    cases = sample_cases.SAMPLE_CASES.get("cases", [])  # type: ignore[attr-defined]
    results = []
    for case in cases:
        text = case.get("summary", "")
        expected_route = case.get("route")
        
        state = SessionState(
            initial_user_text=text,
            known_facts={"sample_case": case}
        )
        result = analyze_session(state)
        
        results.append(
            {
                "case_id": case.get("id"),
                "expected_route": expected_route,
                "session_response": result.dict(),
            }
        )
    return {"results": results}


@router.get("/health/")
async def healthcheck() -> Dict[str, Any]:
    """
    Lightweight healthcheck to verify FastAPI is running and rules.json loads.
    """
    try:
        rules = get_all_rules()
        rules_loaded = len(rules)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to load rules.json: {exc}") from exc

    return {"status": "ok", "rules_loaded": rules_loaded}


