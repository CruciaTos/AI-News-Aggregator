"""Configuration helpers (placeholder).

This module provides a minimal `Config` dataclass that loads values from
environment variables. Replace with Pydantic `BaseSettings` or similar
in implementation.
"""
from dataclasses import dataclass
import os


@dataclass
class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_USER: str = os.getenv("SMTP_USER", "")


def get_config() -> Config:
    """Return a Config instance (placeholder)."""
    return Config()
