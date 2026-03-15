from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, bool, float]:
    """
    Extract text from a PDF file.

    This MVP implementation uses a text-based PDF reader only and sets
    ocr_used=False. If future documents require OCR, that can be added later.
    """
    reader = PdfReader(BytesIO(file_bytes))
    pages_text: List[str] = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    text = "\n".join(pages_text)
    # Heuristic confidence: 1.0 if we got any text, else 0.0
    confidence = 1.0 if text.strip() else 0.0
    return text, False, confidence


def parse_decision_letter(text: str) -> Dict[str, Any]:
    """
    Placeholder parser for VA decision letters.

    This does NOT attempt to infer any new VA rules. It only returns a basic
    structure and leaves deeper understanding to the conversational flow.
    """
    # TODO: Add light heuristics or LLM-assisted extraction that remain
    # strictly descriptive (e.g., finding dates and issue headings) without
    # adding ungrounded VA process logic.
    return {
        "raw_text": text,
        "decision_date": None,
        "issues": [],
        "possible_denial_signals": [],
        "possible_favorable_findings": [],
        "parse_notes": "Structured parsing not yet implemented; using raw text only.",
        "parse_confidence": 0.0,
    }

