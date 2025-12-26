# TcyberChatbot — Local‑First Chatbot

A local‑first, multi‑modal chatbot API and frontend. Upload documents (PDF/TXT/images/audio), ask questions, get RAG‑enhanced answers with citations, image analysis, and audio transcription.

Quick links
- Backend: `backend/`
- Frontend: `frontend/`
- Backups of cleared markdown: `backups/md-backup-20251218_000000/`
- Spec & agent guidance: `AGENTS.md`

Requirements
- Python 3.11+
- Node.js (18+ recommended)
- pnpm for frontend
- `uv` helper for Python virtualenv management (optional but recommended)

Backend — local development
1. Open a terminal and run:

```powershell
cd backend
uv init      # creates .venv if not present
# Activate venv (Windows PowerShell)
.venv\Scripts\activate
uv pip sync requirements.txt
```

2. Start the backend (development):

```powershell
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. API docs: http://localhost:8000/docs

CORS configuration
- Development defaults allow `http://localhost:3000` and `http://localhost:3001`.
- To change allowed origins, set one of the following environment variables before starting the backend:
  - `ALLOWED_ORIGINS` — comma separated list, e.g. `http://localhost:3001,http://127.0.0.1:3001`
  - `ALLOW_ORIGIN_REGEX` — a regex (useful to match any localhost port), e.g. `^http://localhost(:\\d+)?$`

Important: Do not use `allow_origins=["*"]` in production when `allow_credentials=True`.

Frontend — local development
1. Install dependencies and run dev server:

```bash
cd frontend
pnpm install
pnpm run dev
# By default frontend runs on http://localhost:3000 or http://localhost:3001 (depending on your setup)
```

2. Ensure `NEXT_PUBLIC_API_URL` points to the backend (default `http://localhost:8000`).

Hydration mismatches and browser extensions
- If you see React hydration mismatch warnings (attributes like `data-darkreader-inline-stroke`), disable browser extensions such as Dark Reader during development — these inject attributes that cause false hydration warnings.
- Keep non-deterministic rendering (e.g., `Date.now()`, `Math.random()`, locale formatting) inside client components or guard them with `useEffect`/`suppressHydrationWarning`.

Repository notes
- API routes live under `backend/src/api/`.
- Backend service implementations are in `backend/src/services/`.
- Frontend React code under `frontend/src/` (Next.js App Router).
- Vector store: ChromaDB (local by default).

Restoring markdown files
- A backup of original `.md` files was created at `backups/md-backup-20251218_000000/` before any clearing operations.

If you want me to: truncate selected `.md` files (root-level notes) now, or preserve/restore specific files, tell me which files to act on.
