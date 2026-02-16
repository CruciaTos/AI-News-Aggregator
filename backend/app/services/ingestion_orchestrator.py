"""Orchestrator stub for ingestion and summarization.

Expose method signatures for `run_once()` and `schedule()` to be
implemented later.
"""


class IngestionOrchestrator:
    def __init__(self):
        pass

    def run_once(self):
        """Run a single ingestion + summarization cycle (stub)."""
        raise NotImplementedError("run_once is a scaffold stub")

    def schedule(self):
        """Register scheduled jobs (stub)."""
        raise NotImplementedError("schedule is a scaffold stub")
