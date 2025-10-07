# Tasks: Responsive Frontend UI

**Input**: Design documents from `/specs/002-design-and-develop/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
    → If not found: ERROR "No implementation plan found"
    → Extract: Next.js 14+, shadcn/UI, Tailwind CSS, TypeScript
2. Load optional design documents:
    → data-model.md: Extract entities → type definition tasks
    → contracts/: Each file → contract test task
    → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
    → Setup: project init, dependencies, linting
    → Tests: contract tests, integration tests
    → Core: types, API clients, components, pages
    → Integration: state management, routing
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
    → All entities have types?
    → All tests come before implementation?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/src/` for components, `frontend/tests/` for tests
- Adjust based on plan.md structure

## Phase 3.1: Setup
- [x] T001 Create frontend directory structure per implementation plan
- [x] T002 Initialize Next.js 14+ project with TypeScript and App Router
- [x] T003 Install Next.js 14+, React 18+, shadcn/UI, Tailwind CSS, Lucide React, Vercel AI SDK dependencies
- [x] T004 [P] Configure ESLint and Prettier for TypeScript strict mode
- [x] T005 [P] Initialize shadcn/UI with Tailwind CSS and configure components
- [x] T006 Configure Next.js for environment variables and API proxy

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T007 [P] Contract test for chat API in frontend/tests/contract/test_chat_api.ts
- [x] T008 [P] Contract test for upload API in frontend/tests/contract/test_upload_api.ts
- [x] T009 [P] Contract test for export-import API in frontend/tests/contract/test_export_import_api.ts
- [x] T010 [P] Integration test for sidebar toggle in frontend/tests/integration/test_sidebar_toggle.ts
- [x] T011 [P] Integration test for message sending in frontend/tests/integration/test_message_send.ts
- [x] T012 [P] Integration test for file upload in frontend/tests/integration/test_file_upload.ts
- [x] T013 [P] Integration test for settings panel in frontend/tests/integration/test_settings_panel.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T014 [P] Create ChatSession type definition in frontend/src/types/chat.ts
- [x] T015 [P] Create Message type definition in frontend/src/types/message.ts
- [x] T016 [P] Create Document type definition in frontend/src/types/document.ts
- [x] T017 [P] Create UserSettings type definition in frontend/src/types/settings.ts
- [x] T018 [P] Create chat API client in frontend/src/lib/api/chat.ts
- [x] T019 [P] Create documents API client in frontend/src/lib/api/documents.ts
- [x] T020 [P] Create data management API client in frontend/src/lib/api/data.ts
- [x] T021 [P] Create Sidebar component in frontend/src/components/sidebar.tsx
- [x] T022 [P] Create ChatHistory component in frontend/src/components/chat-history.tsx
- [x] T023 [P] Create DocumentManager component in frontend/src/components/document-manager.tsx
- [x] T024 [P] Create TopBar component in frontend/src/components/top-bar.tsx
- [x] T025 [P] Create SettingsPanel component in frontend/src/components/settings-panel.tsx
- [x] T026 [P] Create ChatBubble component in frontend/src/components/chat-bubble.tsx
- [x] T027 [P] Create Citation component in frontend/src/components/citation.tsx
- [x] T028 [P] Create MessageInput component in frontend/src/components/message-input.tsx
- [x] T029 Create main chat page in frontend/src/app/page.tsx
- [x] T030 Create layout with responsive design in frontend/src/app/layout.tsx

## Phase 3.4: Integration
- [x] T031 Implement global state management with React Context or Zustand
- [x] T032 Connect Sidebar to chat history API and state management
- [x] T033 Connect TopBar to export/import functionality
- [x] T034 Connect SettingsPanel to user settings persistence
- [x] T035 Connect ChatBubble to streaming responses and citations
- [x] T036 Connect MessageInput to file upload and message sending
- [x] T037 Implement theme switching with CSS variables
- [x] T038 Add loading states and error handling throughout UI

## Phase 3.5: Polish
- [x] T039 [P] Unit tests for Sidebar component in frontend/tests/unit/test_sidebar.tsx
- [x] T040 [P] Unit tests for MessageInput component in frontend/tests/unit/test_message_input.tsx
- [x] T041 [P] Unit tests for ChatBubble component in frontend/tests/unit/test_chat_bubble.tsx
- [x] T042 Performance optimization and code splitting for chat interface
- [x] T043 Implement accessibility features (ARIA labels, keyboard navigation)
- [x] T044 Add visual feedback for user actions (animations, loading indicators)
- [x] T045 [P] Update documentation with component usage examples
- [x] T046 Final integration testing and bug fixes

## Dependencies
- Tests (T007-T013) before implementation (T014-T038)
- Types (T014-T017) before API clients (T018-T020)
- API clients (T018-T020) before components (T021-T029)
- Components (T021-T029) before pages (T029-T030)
- Core implementation before integration (T031-T038)
- Integration before polish (T039-T046)

## Parallel Example
```
# Launch T007-T009 together:
Task: "Contract test for chat API in frontend/tests/contract/test_chat_api.ts"
Task: "Contract test for upload API in frontend/tests/contract/test_upload_api.ts"
Task: "Contract test for export-import API in frontend/tests/contract/test_export_import_api.ts"

# Launch T014-T017 together:
Task: "Create ChatSession type definition in frontend/src/types/chat.ts"
Task: "Create Message type definition in frontend/src/types/message.ts"
Task: "Create Document type definition in frontend/src/types/document.ts"
Task: "Create UserSettings type definition in frontend/src/types/settings.ts"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
    - Each contract file → contract test task [P]
    - Each endpoint → API client method

2. **From Data Model**:
    - Each entity → type definition task [P]
    - Relationships → interface extensions

3. **From User Stories**:
    - Each story → integration test [P]
    - Quickstart scenarios → end-to-end validation

4. **Ordering**:
    - Setup → Tests → Types → API Clients → Components → Pages → Integration → Polish
    - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have type definition tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task