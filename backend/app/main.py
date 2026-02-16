"""FastAPI application factory (placeholder).

Provides `create_app()` which returns a FastAPI instance with a minimal
`/health` endpoint. This is a non-implementation stub used for scaffolding
and import-time tests.
"""
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and return a FastAPI app (placeholder)."""
    app = FastAPI(title="AI News Aggregator - Backend (placeholder)")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    # Quick manual run for local dev (requires uvicorn installed).
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
