from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.api import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Veteran Disability Claims Journey Copilot",
        version="0.1.0",
        description=(
            "Educational and organizational assistant for understanding VA disability "
            "claims and decision review options. This app does not file claims, act as "
            "a representative, or provide legal advice."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()

