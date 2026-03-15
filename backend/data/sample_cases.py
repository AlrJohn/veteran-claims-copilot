"""
In-code view of sample cases for easy import by the FastAPI application.

This module simply mirrors backend/data/sample_cases.json without adding any
new VA logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


SAMPLE_CASES_PATH = Path(__file__).with_suffix(".json")


def _load_sample_cases() -> Dict[str, Any]:
    with SAMPLE_CASES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SAMPLE_CASES: Dict[str, Any] = _load_sample_cases()

