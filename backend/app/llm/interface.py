"""LLM adapter interface (placeholder).

Define a simple protocol that concrete adapters must follow.
"""
from typing import Protocol


class LLMAdapter(Protocol):
    def summarize(self, text: str) -> str:
        """Return a summary of the given text."""
        ...
