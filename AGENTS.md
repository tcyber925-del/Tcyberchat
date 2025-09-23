# AGENTS.md

A specification file to guide coding agents (or AI assistants) working on the Local RAG Chatbot project.

---

## Project Overview

- **Name**: Local First Chatbot
- **Purpose**: A comprehensive multi-modal chatbot API with local AI processing. Users upload documents (PDF, TXT, images, audio), ask questions via conversational AI, get RAG-enhanced answers with citations; supports image analysis, audio transcription, vector search, and data portability.
- **Stack**:
  - Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Radix UI
  - Backend: Python 3.11 + FastAPI + SQLAlchemy + ChromaDB
  - AI/ML: LangChain + sentence-transformers + transformers + torch + OpenAI Whisper
  - Multi-modal Processing: Image analysis (OCR), audio transcription
  - Vector Store: ChromaDB (for local development)
  - LLM: Ollama (local) by default; optional hosted LLMs as needed

---

## Setup Commands

`uv` is used for creating and managing Python virtual environments, dependency installation, version locking, and running Python commands.

### Install `uv`

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternatively via pipx or pip
pip install uv
```

### Backend Setup

```bash
cd backend

# Initialize uv project (creates pyproject.toml and .venv if not exists)
uv init

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies from requirements.txt
uv pip sync requirements.txt
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm run dev
```

### Running the Backend

```bash
cd backend

# Use uv run to ensure .venv is used
uv run python main.py
# Or using uvicorn directly:
uv run uvicorn main:app --reload --host 0.0.0.0 --port 3001
```

### Running Tests

```bash
cd backend
uv run pytest
```

---

## API & Data Contracts

(As before; interfaces and endpoints remain same; agents should follow contract specs in the PRD.)

### Endpoints

| Method | Path                         | Description                                  |
|--------|-----------------------------|----------------------------------------------|
| POST   | `/chat/`                    | Send user query → AI response with citations |
| GET    | `/chat/conversations`       | List all conversations                       |
| GET    | `/chat/conversations/:id`   | Get messages in a conversation               |
| DELETE | `/chat/conversations/:id`   | Delete a conversation                        |
| POST   | `/documents/upload`         | Upload document                              |
| GET    | `/documents/`               | List documents                               |
| DELETE | `/documents/:id`            | Delete document                              |
| GET    | `/documents/:id/summary`    | Get document summary                         |
| POST   | `/search/`                  | Vector search across documents               |
| POST   | `/data-management/export`   | Export data                                  |
| POST   | `/data-management/import`   | Import data                                  |
| POST   | `/analyze-image/`           | Analyze image with OCR                       |
| POST   | `/transcribe-audio/`        | Transcribe audio file                        |
| GET    | `/render-content/:id`       | Render content in various formats            |

### Data Models

```ts
interface Conversation {
  id: string;
  title: string;
  startedAt: string;
  lastActivity: string;
  documentId?: string;
  messageCount: number;
}

interface Document {
  id: string;
  filename: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
  status: 'uploading' | 'processing' | 'analyzing' | 'transcribing' | 'embedding' | 'ready' | 'error';
  hasContent: boolean;
  hasTranscription: boolean;
  hasImageAnalysis: boolean;
  previewImage?: string;
}

interface Message {
  id: string;
  content: string;
  timestamp: string;
  type: 'user' | 'bot';
  conversationId?: string;
  citations?: Array<{
    docId: string;
    page?: number;
    snippet: string;
  }>;
  metadata?: object;
}
```

---

## Code Style & Conventions

- **Backend** (Python):
  - Use uv for all dependency management; `uv pip sync` etc.
  - Utilize Pydantic models for request/response schemas.
  - Organize code modularly: ingestion, retrieval, API, orchestration (LangChain).
  - Type hints everywhere; linting with `ruff`, formatting with `black`, type checking with `mypy`.
- **Frontend**:
  - TypeScript strict mode.
  - React functional components & hooks.
  - Tailwind CSS with utility classes, consistent spacing & theming.
  - Use Radix UI component primitives for Buttons, Dialogs, Tabs, etc.
  - Linting with ESLint, formatting with Prettier.
  - Avoid large bundle dependencies; lazy‑load DocumentViewer / PDF rendering.

- **General**:
  - Use consistent naming (snake_case on backend, camelCase in frontend).
  - Commit messages prefixed with subsystem e.g. `[frontend]`, `[backend]`, `[ingest]`, `[UI]`.

---

## UI Layout & Behavior (Sidebar Version)

Agents should know how the UI is structured so changes align.

- Left Sidebar: contains a list of sessions (chat history) and documents. Sessions at top; documents below. Sidebar visible on desktop, collapsible / slide‑over on mobile.
- Center area: main chat interface: message list + input bar fixed bottom.
- Right Drawer: DocumentViewer opens upon clicking a citation or sidebar document.
- UI supports upload, streaming, delete with undo, snippet caching, citation chips.

---

## Testing & QA

- Unit tests for core components & backend routines.
- Contract tests for API endpoints.
- Integration tests for flows: upload → index → chat → citation → viewer.
- Tests for offline mode and sync behavior.
- Nightly evaluative tests: Recall@k, citation accuracy, hallucination flags using gold Q/A set.

---

## Observability & Telemetry

- Optional: Use LangChain + LangSmith for tracing (not currently implemented)
  - retrieval candidates, reranker scores
  - prompt used
  - LLM latency and token counts
  - errors & fallback paths

- Backend logging:
  - ingestion pipeline status
  - API call timings, failures
  - usage of special tools (DuckDB, KG)

- Frontend metrics:
  - latency from user “send” to first token
  - time to index docs
  - error rates in upload/document viewing

---

## Agents Task Guidance

When asked to build/modify features, follow these guidelines:

- **Feature requests** should be implemented end‑to‑end: UI + API + backend + indexing logic + tests.
- For UI behavior, mirror the design in the layout spec: sidebar sessions & documents, DocumentViewer, streaming responses.
- When adding new endpoints or data models, update frontend and backend contracts, and include Pydantic/Typescript types.
- Always include citations support: snippet + page + docId + status (removed or available).
- For components affected by deletions (docs or sessions), include undo logic and UI feedback.

---

## Build & Deployment

- Dev: run frontend and backend locally; vector store local or hosted dev instance.
- For production or hosted LLMs: configure environment variables for LLM endpoint, API keys.
- If using Milvus or Weaviate, include start‑up scripts or Docker Compose definitions.
- Persist storage directories, vector DB data, metadata DB; version control frontend; backup raw documents.

---

## Security & Privacy Notes

- Docs and user data are sensitive: operations must default local; no external data leaks.
- If hosted LLMs are enabled, ensure data policies are clear, optional.
- ACL metadata must be enforced in retrieval (backend).
- Document deletion must not expose removed content; cached snippet only visible in historical context with “removed” status.

---

## Contribution & PR Guidelines

- Branch naming: `feature/<short‑desc>` or `fix/<short‑desc>`
- Before merging:
  1. Run lint / formatting checks (prettier / eslint / black / ruff / mypy)
  2. Run tests (unit & contract)
  3. Verify UI behavior matches design spec (screenshots or storybook if available)
  4. If new API changes: update API docs (OpenAPI / Swagger) + update frontend types
  5. Ensure commit history is clean

---

## Where to Find More Context

- README.md for high-level usage and setup  
- UI design tokens and Figma file for look & feel  
- Backend architecture docs for ingestion / indexing / query pipelines  
- Evaluation plan & gold Q/A set in `qa/` folder  

---

## Why AGENTS.md Exists

This file is the single source of truth for coding agents (AI or human) to understand the project’s architecture, coding conventions, UI layout, and integration points. It complements README and detailed design docs by gathering instructions in one structured place.

---
