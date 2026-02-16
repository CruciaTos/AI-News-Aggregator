Plan: AI News Aggregator

TL;DR — What, how, why:
- Build a modular, portfolio-grade desktop app with a Python 3.11+ FastAPI backend (scrapers, ingestion, LLM summarization, SQLite+SQLAlchemy persistence, APScheduler jobs) and a React+Electron frontend (Axios comms, Tailwind/MUI). Target Ollama local LLMs as primary for offline summaries with HuggingFace as a fallback; deploy via Docker for reproducible desktop builds.

Discovery Notes
- Files inspected: main.py, pyproject.toml, README.md
- Current state: `main.py` is a placeholder that prints a greeting; `pyproject.toml` contains only project metadata and no dependencies; `README.md` is empty.
- Decisions captured: Ollama preferred (with HuggingFace fallback); support All data sources (RSS, web scraping, YouTube, social); use SQLite + SQLAlchemy local DB; prefer Dockerized deployment.

Architecture (high level)
- Backend (Python 3.11+)
  - FastAPI ASGI app served by Uvicorn
  - Ingestion modules: RSS, website scraper (requests + BeautifulSoup4 / lxml), `newspaper3k` parser
  - YouTube module: YouTube Data API client + `youtube-transcript-api` + optional `pytube`/`yt-dlp`
  - Summarization: pluggable `llm_adapter` supporting Ollama (local) primary + HuggingFace/transformers fallback
  - Persistence: SQLite via SQLAlchemy + Alembic migrations
  - Scheduling: APScheduler for periodic ingestion jobs
  - Caching: optional `diskcache` or in-memory LRU cache
  - Email notifications: built-in `smtplib` + `email` for HTML messages
  - Reliability: `tenacity` retry wrappers, structured logging
- Frontend (Node.js 18+ / React)
  - React app with Axios for API calls
  - Styling: TailwindCSS or Material UI (choose one)
  - State: React Context or Zustand
  - Desktop shell: Electron + electron-builder
  - Dev helpers: concurrently to run backend + frontend in dev
- DevOps / Distribution
  - Dockerfile for backend and frontend, docker-compose for local orchestration
  - Packaging via `electron-builder`
  - Linting/formatting: Black + Ruff for Python, Prettier + ESLint for frontend
  - Use `python-dotenv` for environment variables, `.env.example` for templates

File structure (suggested)
- `README.md`
- `PLAN.md` (this file)
- `.env.example`
- `docker-compose.yml`
- `backend/`
  - `pyproject.toml` (backend-specific) or reuse root
  - `backend/app/__init__.py`
  - `backend/app/main.py` (FastAPI app)
  - `backend/app/api/` (routes)
  - `backend/app/core/` (config, logging)
  - `backend/app/db/` (models.py, session.py, alembic/)
  - `backend/app/services/` (ingestion orchestrator)
  - `backend/app/ingest/` (rss.py, scraper.py, newspaper.py)
  - `backend/app/youtube/` (youtube_api.py, transcripts.py)
  - `backend/app/llm/` (ollama_adapter.py, hf_adapter.py, interface.py)
  - `backend/app/scheduler/` (jobs.py)
  - `backend/app/email/` (notifier.py)
  - `backend/app/cache/` (optional)
  - `backend/tests/`
- `frontend/`
  - `package.json`
  - `frontend/public/`
  - `frontend/src/` (App.tsx, api/, components/, ui/)
  - `frontend/electron/` (electron main process, preload)
  - `frontend/tests/`
- `scripts/` (dev helpers)
- `docker/` (Dockerfiles)
- `migrations/` (Alembic migration scripts)

All requested packages & tools (features list)
- Backend core: FastAPI, Uvicorn, Pydantic, python-dotenv
- Scraping/ingestion: requests, BeautifulSoup4 (bs4), newspaper3k, lxml, feedparser (optional)
- YouTube: google-api-python-client (YouTube Data API), youtube-transcript-api, optional pytube / yt-dlp
- LLM & text processing: Ollama (local runtime) + adapters for Llama/Mistral/Qwen models; HuggingFace/transformers fallback; langchain (optional), tiktoken (optional), plus `re`, `textwrap`
- DB & migrations: sqlite3 (builtin), SQLAlchemy, Alembic
- Scheduling: APScheduler
- Email: smtplib (builtin), email (builtin) for HTML
- Caching: diskcache (optional)
- Reliability/logging: logging, tenacity
- Frontend: React, Axios, TailwindCSS or Material UI, React Context or Zustand
- Desktop packaging: Electron, electron-builder, concurrently, cross-env, dotenv
- Dev: Docker, Git, pip/venv, npm/yarn, Black, Ruff, Prettier, ESLint

Chronological implementation steps (what to do first — ordered)
1. Project bootstrap
   - Initialize Git repo and CI hints.
   - Create top-level files: `README.md`, `PLAN.md` (this file), `.env.example`.
   - Create `backend/` and `frontend/` scaffolds and `docker-compose.yml`.
2. Backend environment & core
   - Set up Python environment (use `pyproject.toml` + Poetry or `pip` with `requirements.txt`).
   - Add FastAPI, Uvicorn, Pydantic, python-dotenv, SQLAlchemy, Alembic, logging, tenacity.
   - Create `backend/app/main.py` FastAPI app with health endpoint.
   - Wire `config.py` to load `.env`.
3. Persistence layer
   - Design DB schema for `sources`, `articles`, `media`, `summaries`, `jobs`, `users` (if needed).
   - Implement SQLAlchemy models in `backend/app/db/models.py`.
   - Configure DB sessions and Alembic migrations.
   - Add basic CRUD repository functions and unit tests.
4. Ingestion: RSS + Website scraping
   - Implement `backend/app/ingest/rss.py` (feedparser); `scraper.py` using `requests` + `BeautifulSoup` + `lxml`.
   - Add article parsing with `newspaper3k` as fallback.
   - Normalize and persist raw content and metadata.
5. YouTube ingestion
   - Implement `backend/app/youtube/youtube_api.py` (YouTube Data API client) and `transcripts.py` using `youtube-transcript-api`.
   - Persist video metadata and transcripts; map to `articles`/`media`.
6. LLM summarization pipeline
   - Implement LLM adapter interface `backend/app/llm/interface.py`.
   - Build `ollama_adapter.py` to call local Ollama runtime (primary).
   - Add `hf_adapter.py` fallback using HuggingFace transformers or inference API.
   - Provide prompt templates and sanitization in `backend/app/llm/prompts.py`.
   - Add token counting (optional `tiktoken`) and chunking helpers.
7. Orchestration & jobs
   - Create `services/ingestion_orchestrator.py` to coordinate ingestion → cleaning → summarization → persistence.
   - Add APScheduler jobs in `scheduler/jobs.py` with cron-style config to run feeds and channel ingestion.
   - Add tenacity-based retries where network calls happen.
8. API layer & endpoints
   - Add REST endpoints: `GET /articles`, `GET /articles/{id}`, `POST /sources`, `GET /sources`, `GET /summaries`, `POST /summaries/generate`.
   - Add pagination, filters, and admin endpoints for job control.
   - Add authentication hooks (optional).
9. Email notifications
   - Implement `email/notifier.py` to send digests via SMTP (templated HTML).
   - Add endpoint or scheduled job to trigger digests.
10. Frontend skeleton
    - Bootstrap React app with routing and sample pages: Dashboard, Feed list, Article view, Settings.
    - Implement Axios API client and sample calls to backend endpoints.
    - Add basic Electron integration: `frontend/electron/main.js` and `preload.js`.
11. Packaging & Docker
    - Add `Dockerfile` for backend and frontend and `docker-compose.yml` to run services.
    - Create `electron-builder` config for packaging desktop app (with backend bundled or run as separate process).
12. Testing & linters
    - Add unit tests for ingestion, DB repositories, and LLM adapters.
    - Configure Black + Ruff for Python and Prettier + ESLint for frontend.
13. Documentation & examples
    - Fill `README.md` with setup, dev run commands, and architecture diagrams.
    - Add `.env.example` with required keys (YouTube API key, SMTP settings) and instructions for Ollama setup.
14. Optional improvements
    - Add offline-first sync strategies, disk caching, background worker with Celery if scaling needed, user accounts, and GUI preferences.

Verification (how to test & verify)
- Local dev run: run `docker-compose up --build` then open Electron (or run React dev server + backend Uvicorn).
- API smoke tests: `GET /health` and `GET /articles`.
- Ingestion test: add a sample RSS feed + a YouTube channel in `.env`/admin UI and confirm entries appear in DB.
- LLM test: run `POST /summaries/generate` on a long article and confirm summary is returned and stored.
- Run unit tests: `pytest backend/` and frontend test runner (e.g., `npm test`).
- Verify packaging: build Electron artifact with `electron-builder` and run installer.

Critical file paths to implement (quick list)
- main.py — existing placeholder (replace or move into backend later)
- backend/app/main.py
- backend/app/api/routes.py
- backend/app/db/models.py
- backend/app/ingest/rss.py
- backend/app/ingest/scraper.py
- backend/app/youtube/youtube_api.py
- backend/app/llm/ollama_adapter.py
- backend/app/scheduler/jobs.py
- frontend/src/App.tsx
- frontend/electron/main.js
- docker-compose.yml
- .env.example

Decisions & rationale
- Ollama primary + HF fallback: satisfies offline-first goal while keeping a cloud fallback for machines that cannot run models locally.
- SQLite + SQLAlchemy: lightweight, portable, and portfolio-appropriate.
- Dockerized deployment: reproducible developer environment and packaging pathway; Electron handles desktop UX.
- FastAPI: modern async backend with excellent developer ergonomics and easy API surface for React.

Next actions (pick one)
- Scaffold files & manifests now (backend + frontend minimal skeleton).
- Begin backend skeleton implementation (FastAPI app, config, DB session).
- Or: make any edits to this plan before saving it into a permanent file.

Backend scaffolding (non-implementation)
- Purpose: provide a clear, minimal skeleton of modules and placeholder files so implementation can proceed in a structured way. These files are placeholders and must NOT contain production logic yet — only imports, docstrings, and small stubs where appropriate.
- Recommended minimal backend skeleton (placeholders only):
   - `backend/app/__init__.py`  — package marker
   - `backend/app/main.py`  — FastAPI app factory and `create_app()` stub with a `/health` endpoint
   - `backend/app/core/config.py`  — `Config` dataclass to load env vars with `python-dotenv`
   - `backend/app/core/logging.py`  — logging config helper
   - `backend/app/db/__init__.py`
   - `backend/app/db/session.py`  — DB session/engine creation stub
   - `backend/app/db/models.py`  — SQLAlchemy Base and placeholder models (Source, Article, Summary)
   - `backend/app/api/__init__.py`
   - `backend/app/api/routes.py`  — API route registration with placeholder routers
   - `backend/app/ingest/__init__.py`
   - `backend/app/ingest/rss.py`  — stub functions: `fetch_feed(url)` and `parse_entries(entries)` (no network calls)
   - `backend/app/ingest/scraper.py`  — placeholder `fetch_html(url)` and `extract_text(html)`
   - `backend/app/ingest/newspaper_adapter.py` — placeholder wrapper for `newspaper3k` usage
   - `backend/app/youtube/__init__.py`
   - `backend/app/youtube/youtube_api.py`  — placeholder client class with method signatures only
   - `backend/app/youtube/transcripts.py`  — placeholder for transcript extraction interface
   - `backend/app/llm/interface.py`  — abstract adapter interface (synchronous signatures)
   - `backend/app/llm/ollama_adapter.py`  — stub implementing interface that raises NotImplementedError
   - `backend/app/llm/hf_adapter.py`  — fallback adapter stub
   - `backend/app/services/ingestion_orchestrator.py`  — orchestrator class with method signatures: `run_once()` and `schedule()` (no scheduling logic yet)
   - `backend/app/scheduler/__init__.py`
   - `backend/app/scheduler/jobs.py`  — APScheduler job registration stubs (no scheduling run)
   - `backend/app/email/notifier.py`  — notifier class with `compose_digest()` and `send()` stubs
   - `backend/app/cache/__init__.py`  — optional cache adapter stub
   - `backend/app/tests/test_smoke.py`  — very small test that imports `create_app()` and calls `/health` (mocked)

Detailed file structure skeleton (expanded)
```
ai-news-aggregator/
├─ README.md
├─ PLAN.md (this file)
├─ .env.example
├─ docker-compose.yml
├─ pyproject.toml
├─ main.py  # existing placeholder; will be deprecated in favor of backend/app/main.py
├─ backend/
│  ├─ pyproject.toml (optional)
│  ├─ app/
│  │  ├─ __init__.py
   │  ├─ main.py                 # FastAPI app factory (create_app)
   │  ├─ core/
   │  │  ├─ __init__.py
   │  │  ├─ config.py            # Config dataclass + env loader
   │  │  └─ logging.py           # logging setup
   │  ├─ api/
   │  │  ├─ __init__.py
   │  │  └─ routes.py            # register routers, health endpoint
   │  ├─ db/
   │  │  ├─ __init__.py
   │  │  ├─ session.py           # engine/session maker (stub)
   │  │  └─ models.py            # Base, Source, Article, Summary models (placeholders)
   │  ├─ ingest/
   │  │  ├─ __init__.py
   │  │  ├─ rss.py               # fetch_feed(), parse_entries()
   │  │  ├─ scraper.py           # fetch_html(), extract_text()
   │  │  └─ newspaper_adapter.py # wrapper stub
   │  ├─ youtube/
   │  │  ├─ __init__.py
   │  │  ├─ youtube_api.py       # signatures only
   │  │  └─ transcripts.py       # transcript extraction interface
   │  ├─ llm/
   │  │  ├─ __init__.py
   │  │  ├─ interface.py         # adapter interface (abstract)
   │  │  ├─ ollama_adapter.py    # NotImplemented stub
   │  │  └─ hf_adapter.py        # fallback stub
   │  ├─ services/
   │  │  └─ ingestion_orchestrator.py
   │  ├─ scheduler/
   │  │  ├─ __init__.py
   │  │  └─ jobs.py              # job registration stubs
   │  ├─ email/
   │  │  ├─ __init__.py
   │  │  └─ notifier.py          # compose_digest(), send()
   │  └─ tests/
   │     └─ test_smoke.py
   └─ requirements.txt (or use pyproject)
├─ frontend/
│  ├─ package.json
│  ├─ public/
│  ├─ src/
│  │  ├─ App.tsx
   │  ├─ api/
│  │  ├─ components/
   │  │  └─ ui/
│  └─ electron/
│     ├─ main.js
│     └─ preload.js
├─ scripts/
│  └─ dev.sh
└─ docker/
    ├─ backend.Dockerfile
    └─ frontend.Dockerfile
```

Notes for the skeleton
- Keep all placeholder files minimal: imports, docstrings, function/class signatures, and a brief TODO comment. No network calls, no DB writes, and no secrets in any placeholders.
- Use descriptive names for modules and functions to make later implementation straightforward.
- This skeleton is intentionally implementation-free so planning and review can occur before coding.

Next steps (proposed)
- Confirm this skeleton and any extra placeholder files you want added here.
- After confirmation, I will scaffold these placeholder files in the repository (one PR-style patch) and then mark `Scaffold backend skeleton` as completed.
