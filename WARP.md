# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Local First Chatbot**: A multi-modal chatbot with local AI processing, RAG capabilities, document management, image analysis, audio transcription, and web search integration.

**Stack**:
- Backend: Python 3.11+ with FastAPI, SQLAlchemy, Alembic, ChromaDB
- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- AI/ML: LangChain, sentence-transformers, transformers, torch, Ollama (local LLM)
- Monorepo: Uses pnpm workspaces

## Common Commands

### Backend Development

All backend commands should be run from the `backend/` directory.

**Environment Setup**:
```pwsh
# Windows PowerShell (preferred on this machine)
cd backend
.venv\Scripts\activate

# Install dependencies with uv
uv pip sync requirements.txt
```

**Running the Backend**:
```pwsh
# Using uv (preferred)
uv run python main.py

# Or with uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API docs available at http://localhost:8000/docs
```

**Testing**:
```pwsh
cd backend

# Run all unit tests
uv run pytest tests/unit

# Run specific test file
uv run pytest tests/unit/test_web_search_service.py

# Run contract tests
uv run pytest tests/contract

# Run integration tests (requires backend running and seeded ChromaDB)
uv run pytest tests/integration

# Seed ChromaDB for integration tests
uv run python scripts/seed_chroma.py
```

**Database Migrations (Alembic)**:
```pwsh
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Linting & Formatting**:
```pwsh
cd backend

# Run ruff linter
ruff check .

# Auto-fix with ruff
ruff check . --fix

# Format with black
black .

# Type checking with mypy
mypy .
```

### Frontend Development

All frontend commands should be run from the `frontend/` directory.

**Setup**:
```pwsh
cd frontend
pnpm install
```

**Running the Frontend**:
```pwsh
cd frontend

# Development server with Turbopack
pnpm run dev
# Opens at http://localhost:3000

# Production build
pnpm run build
pnpm run start
```

**Testing & Linting**:
```pwsh
cd frontend

# Run tests (Jest with watch mode)
pnpm run test

# Run linter
pnpm run lint

# Format code
pnpm run format
```

### Monorepo Commands

From the root directory:

```pwsh
# Install all dependencies
pnpm install

# CI workflow runs these in GitHub Actions
# See .github/workflows/ci.yml for full CI setup
```

## Architecture & Key Concepts

### Backend Architecture

**Service Layer Pattern**: Core business logic is organized into services under `backend/src/services/`:
- `ai_service.py`: AI/LLM interaction orchestration
- `rag_service.py`: RAG (Retrieval-Augmented Generation) pipeline
- `rag_adapter.py`: Adapter layer for LangChain/embeddings/vectorstore with fallback implementations
- `chat_service.py`: Chat message handling
- `document_service.py`: Document upload, processing, and management
- `web_search_service.py`: Multi-provider web search (DuckDuckGo, Tavily)
- `multimodal_service.py`: Image analysis and audio transcription
- `memory_service.py`: Conversation memory management

**API Router Organization**: API endpoints in `backend/src/api/` follow FastAPI conventions with dedicated routers for each domain (chat, documents, search, conversations, etc.). All routers are mounted under `/api` prefix except health/root endpoints.

**Database Layer**: 
- SQLAlchemy models in `backend/src/models/`
- Alembic for migrations in `backend/alembic/`
- Default SQLite database at `./data/chatbot.db`
- ChromaDB for vector storage

**Fallback/Adapter Pattern**: The `rag_adapter.py` centralizes all LangChain/embeddings/vectorstore usage. This allows:
- Unit tests to run without heavy ML dependencies
- DEV_MOCK_AI environment variable for deterministic integration tests
- Graceful degradation if optional dependencies are missing

**Multi-Modal Processing**:
- PDF extraction: Prefers PyMuPDF (`pymupdf`) with fallback to `pypdf`
- Images: OCR and analysis capabilities
- Audio: Transcription support via Whisper

**Web Search Integration**:
- Optional web search to enhance RAG responses
- Supports DuckDuckGo (free) and Tavily (AI-optimized, requires API key)
- Configurable via `enableWebSearch` flag in chat requests
- See `docs/TAVILY_SETUP.md` and `docs/WEB_SEARCH_IMPLEMENTATION_PLAN.md`

### Frontend Architecture

**App Router (Next.js 15)**: Uses Next.js App Router with React Server Components where appropriate.

**Key Component Structure**:
- `src/app/page.tsx`: Main chat interface with drag-and-drop document upload
- `src/components/ui/`: Reusable UI components (shadcn/ui based)
- `src/components/`: Feature-specific components (Sidebar, SettingsPanel, DocumentIndicator, etc.)
- `src/lib/context/`: React Context providers (chat-context, settings-context, toast-context)

**Chat Flow**:
- Streaming responses using Vercel AI SDK and custom hooks
- Real-time message updates with SSE (Server-Sent Events)
- Citation rendering with document references
- Sidebar shows conversation history and uploaded documents

**State Management**:
- React Context for global state (chat, settings, toasts)
- Local component state with hooks
- No Redux or external state library

### Key Patterns to Follow

1. **Dependency Management**: Always use `uv` for Python backend dependencies, `pnpm` for frontend
2. **Type Safety**: Backend uses type hints everywhere; frontend uses TypeScript strict mode
3. **Testing Strategy**: 
   - Unit tests for core logic (fast, no heavy dependencies)
   - Contract tests for API endpoints
   - Integration tests for end-to-end flows (requires seeded ChromaDB and running backend)
4. **Naming Conventions**: snake_case in Python backend, camelCase in TypeScript frontend
5. **Commit Messages**: Prefix with subsystem e.g., `[backend]`, `[frontend]`, `[docs]`

## Important Gotchas

### Backend

- **ChromaDB Seeding**: Integration tests require ChromaDB to be seeded with `scripts/seed_chroma.py` before running
- **Import Paths**: Backend uses relative imports from `src/`. If running scripts directly, ensure `sys.path` includes the backend directory
- **pytest.ini**: Configured to skip `scripts/` directory during test discovery
- **Heavy Dependencies**: The adapter pattern allows tests to run without installing large ML models. Set `DEV_MOCK_AI=1` for mocked AI responses
- **Environment Variables**: 
  - `TAVILY_API_KEY`: For Tavily web search
  - `WEB_SEARCH_PROVIDER`: Set to "tavily" or "duckduckgo"
  - `RUN_INTEGRATION_TESTS`: Set to "1" to enable full integration test suite

### Frontend

- **Turbopack**: Uses Next.js Turbopack for faster builds (`--turbopack` flag)
- **Environment Variables**: Set in `.env.local`:
  - `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:3001)
  - `NEXT_PUBLIC_APP_NAME`: Application name
- **File Upload**: Max file size is 100MB (configured in page.tsx)
- **Drag and Drop**: Only works with actual files, not text/links

### Testing

- **CI Workflow**: GitHub Actions CI runs frontend tests (Jest) and backend tests (unit + gated integration)
- **Integration Tests**: Only run in CI or when explicitly triggered via `workflow_dispatch` with `run_integration=1`
- **Web Search Tests**: Mock web search responses in unit tests to avoid external API calls

## Recent/Ongoing Work

**LangChain Stack Upgrade** (`upgrade/langchain-stack` branch):
- Conservative upgrade plan to modernize LangChain-related packages
- Uses `requirements.langchain-upgrade.txt` for CI testing
- See `docs/UPGRADE_LANGCHAIN_PLAN.md` for full details
- All LangChain usage centralized in `rag_adapter.py` to minimize code changes

**Web Search Feature**:
- Web search service supports DuckDuckGo and Tavily
- Optional flag `enableWebSearch` in chat API requests
- Caching and rate limiting implemented
- See `docs/WEB_SEARCH_IMPLEMENTATION_PLAN.md` and `docs/TAVILY_SETUP.md`

## Development Workflow

1. **Making Changes**:
   - Create feature branch: `feature/<short-desc>` or `fix/<short-desc>`
   - Follow existing patterns in the codebase
   - Update types (Pydantic models for backend, TypeScript interfaces for frontend)

2. **Before Committing**:
   - Run linters: `ruff check .` (backend), `pnpm run lint` (frontend)
   - Run formatters: `black .` (backend), `pnpm run format` (frontend)
   - Run relevant tests: `uv run pytest tests/unit` (backend), `pnpm run test` (frontend)
   - If API changes: update both backend Pydantic schemas and frontend TypeScript types

3. **Pull Requests**:
   - CI must pass (frontend tests, backend unit tests)
   - Integration tests run on manual trigger or for PRs
   - Commit history should be clean and descriptive

## Special Notes for Agents

- **OpenSpec Workflow**: If the request involves planning, specs, or proposals, refer to `openspec/AGENTS.md` for the project's structured change management process
- **AGENTS.md Reference**: The root `AGENTS.md` file contains comprehensive project specifications, UI layout details, and agent task guidance. Consult it for detailed feature implementation guidance
- **PDF Processing**: Use PyMuPDF (`pymupdf`) when possible for better extraction quality
- **Citation Support**: Always include citation data (snippet, page, docId, status) when implementing or modifying RAG features
- **Data Privacy**: Document operations default to local-only processing; hosted LLMs are optional and require explicit configuration
- **ACL & Security**: Document deletion should not expose removed content; cached snippets show "removed" status in historical context
