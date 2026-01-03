# TcyberChatbot — Local‑First AI with Web Search & MCP

A local‑first, multi‑modal chatbot API and frontend. Upload documents (PDF/TXT/images/audio), ask questions, get RAG‑enhanced answers with citations, image analysis, and audio transcription.

Now featuring **Real-time Web Search** and **Model Context Protocol (MCP)** support.

## Key Features

- **RAG (Retrieval Augmented Generation):** Chat with your documents (PDF/TXT/MD/Images/Audio).
- **Web Search:** Integrated support for **DuckDuckGo** (free) and **Tavily** (AI-optimized) to fetch real-time information.
- **MCP Support:**
  - **Client:** Connect to multiple MCP servers to extend capabilities.
  - **Server:** Expose chatbot tools (like web search) to other MCP clients.
- **Dockerized:** Production-ready multi-service setup (Frontend, Backend, Redis, Postgres, Nginx).

## Quick Links

- **Backend:** `backend/`
- **Frontend:** `frontend/`
- **Web Search Docs:** `docs/WEB_SEARCH_PHASE1_COMPLETE.md`
- **MCP Docs:** `docs/MCP.md`
- **Docker Plan:** `CONTAINERIZATION_PLAN.md`

## Docker Quick Start

The easiest way to run TcyberChatbot is using Docker Compose.

1.  **Prerequisites:** Ensure [Docker](https://www.docker.com/) and Docker Compose are installed.
2.  **Start Services:**
    ```powershell
    docker compose up --build -d
    ```
3.  **Access the App:**
    - **Web Interface:** http://localhost:8081 (served via Nginx)
    - **API Docs:** http://localhost:8000/docs (direct backend access)

**Services included:**
- **Frontend:** Next.js application
- **Backend:** FastAPI with LangChain & AI/ML
- **Redis:** Caching and session management
- **PostgreSQL:** Persistent database
- **Nginx:** Reverse proxy

## Local Development (Manual)

### Prerequisites
- Python 3.11+
- Node.js (18+ recommended)
- pnpm for frontend
- `uv` helper for Python virtualenv management (optional but recommended)

### Backend
1. Open a terminal and run:
    ```powershell
    cd backend
    uv init      # creates .venv if not present
    # Activate venv (Windows PowerShell)
    .venv\Scripts\activate
    uv pip sync requirements.txt
    # Optional: Install Tavily for AI search
    uv pip install tavily-python
    ```

2. Start the backend (development):
    ```powershell
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

3. API docs: http://localhost:8000/docs

### Frontend
1. Install dependencies and run dev server:
    ```bash
    cd frontend
    pnpm install
    pnpm run dev
    # Runs on http://localhost:3000
    ```

2. Ensure `NEXT_PUBLIC_API_URL` points to the backend (default `http://localhost:8000`).

### Hydration mismatches
- If you see React hydration mismatch warnings (attributes like `data-darkreader-inline-stroke`), disable browser extensions such as Dark Reader during development.

## Configuration

### Environment Variables
Configure these in your environment or `.env` file (see `backend/.env.example` if available).

**Web Search:**
- `WEB_SEARCH_PROVIDER`: `duckduckgo` (default) or `tavily`.
- `TAVILY_API_KEY`: Required if using Tavily.

**MCP:**
- `MCP_MULTI`: JSON configuration for connecting to multiple MCP servers.

**CORS (Backend):**
- `ALLOWED_ORIGINS`: Comma separated list (e.g., `http://localhost:3001,http://127.0.0.1:3001`).
- `ALLOW_ORIGIN_REGEX`: Regex match (e.g., `^http://localhost(:\d+)?$`).

## Repository Notes

- **API Routes:** `backend/src/api/`
- **Services:** `backend/src/services/`
- **Frontend Code:** `frontend/src/` (Next.js App Router)
- **Vector Store:** ChromaDB (local by default).
- **Restoring markdown:** A backup of original `.md` files was created at `backups/md-backup-20251218_000000/`.