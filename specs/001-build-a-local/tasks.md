# Tasks: Build a Local First Chatbot

**Input**: Design documents from `/specs/001-build-a-local/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Backend paths: `backend/src/models/`, `backend/src/api/`, `backend/src/services/`
- Frontend paths: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/services/`
- Tests: `backend/tests/`, `frontend/tests/`

## Phase 3.1: Setup
- [x] T001 Create web application project structure (backend/ and frontend/ directories)
- [x] T002 Initialize Python FastAPI backend project with dependencies (FastAPI, SQLAlchemy, ChromaDB, LangChain, sentence-transformers, Ollama client)
- [x] T003 Initialize React frontend project with dependencies (React, TypeScript, Tailwind CSS, shadcn/ui)
- [x] T004 [P] Configure Python linting and formatting (black, ruff)
- [x] T005 [P] Configure JavaScript/TypeScript linting and formatting (ESLint, Prettier)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T006 [P] Contract test POST /api/chat in backend/tests/contract/test_chat_post.py
- [x] T007 [P] Contract test POST /api/documents in backend/tests/contract/test_documents_upload.py
- [x] T008 [P] Contract test POST /api/documents/{id}/summarize in backend/tests/contract/test_documents_summarize.py
- [x] T009 [P] Contract test GET /api/search in backend/tests/contract/test_search_get.py
- [x] T010 [P] Contract test POST /api/export in backend/tests/contract/test_export_post.py
- [x] T011 [P] Contract test POST /api/analyze-image in backend/tests/contract/test_analyze_image.py
- [x] T012 [P] Contract test POST /api/transcribe-audio in backend/tests/contract/test_transcribe_audio.py
- [ ] T013 [P] Integration test general chat conversation in backend/tests/integration/test_general_chat.py
- [ ] T014 [P] Integration test document upload and processing in backend/tests/integration/test_document_upload.py
- [ ] T015 [P] Integration test document summarization in backend/tests/integration/test_document_summarization.py
- [ ] T016 [P] Integration test multi-document chat with citations in backend/tests/integration/test_multi_document_chat.py
- [ ] T017 [P] Integration test image analysis in backend/tests/integration/test_image_analysis.py
- [ ] T018 [P] Integration test audio transcription in backend/tests/integration/test_audio_transcription.py
- [ ] T019 [P] Integration test rich content rendering in frontend/tests/integration/test_rich_content_rendering.test.tsx
- [ ] T020 [P] Integration test chat history navigation in frontend/tests/integration/test_chat_history.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T021 [P] Message model in backend/src/models/message.py
- [x] T022 [P] Document model in backend/src/models/document.py
- [x] T023 [P] Summary model in backend/src/models/summary.py
- [x] T024 [P] MediaContent model in backend/src/models/media_content.py
- [x] T025 [P] Conversation model in backend/src/models/conversation.py
- [x] T026 [P] ChatService for conversation management in backend/src/services/chat_service.py
- [x] T027 [P] DocumentService for file processing in backend/src/services/document_service.py
- [x] T028 [P] AIService for LLM interactions in backend/src/services/ai_service.py
- [x] T029 [P] RAGService for retrieval-augmented generation in backend/src/services/rag_service.py
- [x] T030 [P] MultiModalService for image/audio processing in backend/src/services/multimodal_service.py
- [x] T031 POST /api/chat endpoint in backend/src/api/chat.py
- [x] T032 POST /api/documents endpoint in backend/src/api/documents.py
- [x] T033 POST /api/documents/{id}/summarize endpoint in backend/src/api/documents.py
- [x] T034 GET /api/search endpoint in backend/src/api/search.py
- [x] T035 POST /api/export and /api/import endpoints in backend/src/api/data_management.py
- [x] T036 POST /api/analyze-image endpoint in backend/src/api/analyze_image.py
- [x] T037 POST /api/transcribe-audio endpoint in backend/src/api/transcribe_audio.py
- [x] T038 POST /api/render-content endpoint in backend/src/api/render_content.py
- [ ] T039 ChatInterface component in frontend/src/components/ChatInterface.tsx
- [ ] T040 DocumentManager component in frontend/src/components/DocumentManager.tsx
- [ ] T041 MessageBubble component in frontend/src/components/MessageBubble.tsx
- [ ] T042 SettingsPanel component in frontend/src/components/SettingsPanel.tsx

## Phase 3.4: Integration
- [x] T043 Database initialization with SQLAlchemy models and ChromaDB setup
- [x] T044 CORS middleware configuration for frontend-backend communication
- [x] T045 Request/response logging middleware
- [x] T046 Error handling middleware with graceful degradation
- [x] T047 File upload handling with validation and storage
- [x] T048 Background task processing for document operations
- [ ] T049 Caching layer implementation (Redis-like for query results)
- [ ] T050 WebSocket support for real-time streaming responses

## Phase 3.5: Polish
- [x] T051 [P] Unit tests for service layer validation in backend/tests/unit/test_services.py
- [x] T052 [P] Unit tests for utility functions in backend/tests/unit/test_utils.py
- [ ] T053 [P] Frontend component unit tests in frontend/tests/unit/
- [ ] T054 Performance optimization and monitoring implementation
- [x] T055 [P] API documentation generation (OpenAPI/Swagger)
- [ ] T056 [P] User documentation and README updates
- [ ] T057 [P] Docker containerization for easy deployment
- [ ] T058 Final integration testing and bug fixes
- [ ] T059 Production build optimization and asset minification

## Dependencies
- Tests (T006-T020) before implementation (T021-T050)
- Models (T021-T025) before services (T026-T030)
- Services (T026-T030) before API endpoints (T031-T038)
- Backend implementation before frontend components (T039-T042)
- Core implementation (T021-T042) before integration features (T043-T050)
- Everything before polish (T051-T059)

## Parallel Example
```
# Launch contract tests together:
Task: "Contract test POST /api/chat in backend/tests/contract/test_chat_post.py"
Task: "Contract test POST /api/documents in backend/tests/contract/test_documents_upload.py"
Task: "Contract test POST /api/documents/{id}/summarize in backend/tests/contract/test_documents_summarize.py"
Task: "Contract test GET /api/search in backend/tests/contract/test_search_get.py"

# Launch model creation tasks together:
Task: "Message model in backend/src/models/message.py"
Task: "Document model in backend/src/models/document.py"
Task: "Summary model in backend/src/models/summary.py"
Task: "MediaContent model in backend/src/models/media_content.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing (TDD principle)
- Commit after each task completion
- Avoid: vague tasks, same file conflicts, missing file paths
- Backend uses Python/FastAPI, Frontend uses React/TypeScript

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks

3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task