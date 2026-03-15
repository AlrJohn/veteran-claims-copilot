from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SessionState(BaseModel):
    conversation_history: List[Dict[str, str]] = []
    initial_user_text: str = ""
    uploaded_letter_present: bool = False
    current_route: Optional[str] = None
    route_confidence: Optional[float] = None
    known_facts: Dict[str, Any] = {}
    missing_facts: List[str] = []
    follow_up_questions: List[str] = []
    candidate_routes: List[str] = []
    final_packet_ready: bool = False

class Citation(BaseModel):
    rule_id: str
    source_title: str
    source_url: str
    source_excerpt: Optional[str] = None

class FinalPacket(BaseModel):
    case_type: str
    confidence: float
    why_this_path: List[str]
    why_not_other_paths: List[str]
    possible_forms: List[str]
    possible_missing_evidence: List[str]
    known_facts: Dict[str, Any]
    follow_up_questions: List[str]
    warnings: List[str]
    citations: List[Citation]
    safety_note: str
    needs_accredited_help: bool

class AnalyzeResponse(BaseModel):
    needs_follow_up: bool
    follow_up_questions: List[str]
    preliminary_route: str
    preliminary_confidence: float
    known_facts: Dict[str, Any]
    missing_facts: List[str]
    citations: List[Citation]
    warnings: List[str]
    final_packet: Optional[FinalPacket] = None
