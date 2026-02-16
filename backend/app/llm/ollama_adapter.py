"""Ollama adapter stub.

Implements the `LLMAdapter` interface but does not call any runtime.
"""
from .interface import LLMAdapter


class OllamaAdapter(LLMAdapter):
    def summarize(self, text: str) -> str:
        """Stub — raise to indicate not yet implemented."""
        raise NotImplementedError("OllamaAdapter.summarize is a scaffold stub")
