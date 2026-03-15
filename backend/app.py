from typing import Any, Dict


def initial_claim(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder handler for the initial claim workflow.
    """
    return {
        "route": "initial_claim",
        "status": "not_implemented",
        "message": "Initial claim workflow is not implemented yet.",
        "input": payload,
    }


def supplemental_claim(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder handler for the supplemental claim workflow.
    """
    return {
        "route": "supplemental_claim",
        "status": "not_implemented",
        "message": "Supplemental claim workflow is not implemented yet.",
        "input": payload,
    }


def hlr(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder handler for the Higher-Level Review workflow.
    """
    return {
        "route": "hlr",
        "status": "not_implemented",
        "message": "Higher-Level Review workflow is not implemented yet.",
        "input": payload,
    }


def board_explainer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder handler for explaining Board of Veterans' Appeals options.
    """
    return {
        "route": "board_explainer",
        "status": "not_implemented",
        "message": "Board explainer workflow is not implemented yet.",
        "input": payload,
    }


def unclear(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder handler when the user's intent is unclear.
    """
    return {
        "route": "unclear",
        "status": "not_implemented",
        "message": "The copilot could not confidently route this request.",
        "input": payload,
    }


ROUTE_HANDLERS = {
    "initial_claim": initial_claim,
    "supplemental_claim": supplemental_claim,
    "hlr": hlr,
    "board_explainer": board_explainer,
    "unclear": unclear,
}


def handle_route(route: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple router entry point for the backend MVP.

    This does NOT expose any web framework yet; it just provides a
    Python-level dispatch function for the five MVP routes.
    """
    handler = ROUTE_HANDLERS.get(route, unclear)
    return handler(payload)

