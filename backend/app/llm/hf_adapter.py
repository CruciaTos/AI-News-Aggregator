"""HuggingFace adapter stub (fallback).

Implements the `LLMAdapter` interface as a placeholder for HF-based inference.
"""
from .interface import LLMAdapter


class HFAdapter(LLMAdapter):
    def summarize(self, text: str) -> str:
        raise NotImplementedError("HFAdapter.summarize is a scaffold stub")
