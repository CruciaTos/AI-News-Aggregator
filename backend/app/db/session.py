"""Database session/engine stubs.

This file contains minimal helpers to create an engine and session factory.
Replace with full SQLAlchemy configuration during implementation.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

engine = None
SessionLocal: Optional[sessionmaker] = None


def init_db(url: str):
    """Initialize engine and sessionmaker (placeholder)."""
    global engine, SessionLocal
    engine = create_engine(url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
