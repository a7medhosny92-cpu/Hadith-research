"""FastAPI application entrypoint.

Run locally:  ``uvicorn app.main:app --reload``
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.routers import health

app = FastAPI(
    title="Hadith Research Backend",
    version=__version__,
    summary="Search, study and verify hadith (RAG, Classical Arabic) over the turath.io corpus.",
)

app.include_router(health.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": "review-backend",
        "version": __version__,
        "docs": "/docs",
        "endpoints_planned": ["/search", "/ask", "/takhrij", "/verify-isnad", "/hadith/{id}"],
    }
