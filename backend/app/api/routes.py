"""API routes registration (placeholders).

This module exposes routers to be mounted in `create_app()`.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
