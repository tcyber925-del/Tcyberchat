pecs/004-polish-the-ui/plan.md</path>
<content lines="1-212">
  1 | # Implementation Plan: UI Polish and Feature Enhancements
  2 |
  3 | **Branch**: `004-polish-the-ui` | **Date**: 2025-09-29 | **Spec**: specs/004-polish-the-ui/spec.md
  4 | **Input**: Feature specification from `specs/004-polish-the-ui/spec.md`
  5 |
  6 | ## Execution Flow (/plan command scope)
  7 | ```
  8 | 1. Load feature spec from Input path
  9 |    → If not found: ERROR "No feature spec at {path}"
  10 | 2. Fill Technical Context (scan for NEEDS CLARIFICATION)
  11 |    → Detect Project Type from context (web=frontend+backend, mobile=app+api)
  12 |    → Set Structure Decision based on project type
  13 | 3. Fill the Constitution Check section based on the content of the constitution document.
  14 | 4. Evaluate Constitution Check section below
  15 |    → If violations exist: Document in Complexity Tracking
  16 |    → If no justification possible: ERROR "Simplify approach first"
  17 |    → Update Progress Tracking: Initial Constitution Check
  18 | 5. Execute Phase 0 → research.md
  19 |    → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
  20 | 6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
  21 | 7. Re-evaluate Constitution Check section
  22 |    → If new violations: Refactor design, return to Phase 1
  23 |    → Update Progress Tracking: Post-Design Constitution Check
  24 | 8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
  25 | 9. STOP - Ready for /tasks command
  26 | ```
  27 |
  28 | **IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
  29 | - Phase 2: /tasks command creates tasks.md
  30 | - Phase 3-4: Implementation execution (manual or via tools)
  31 |
  32 | ## Summary
  33 | UI enhancement feature to polish the chatbot interface with bug fixes, settings improvements, and new multimodal features. Includes sidebar toggle fix, settings panel accessibility, export/import restoration, branding elements, and input enhancements for audio/web search.
  34 |
  35 | ## Technical Context
  36 | **Language/Version**: Backend: Python 3.11, Frontend: TypeScript/React 18 + Next.js 14
  37 | **Primary Dependencies**: Backend: FastAPI, SQLAlchemy, ChromaDB; Frontend: React 18, Next.js, Tailwind CSS, Radix UI
  38 | **Storage**: SQLite (SQLAlchemy ORM) + ChromaDB (vector storage)
  39 | **Testing**: Backend: pytest + pytest-asyncio; Frontend: Jest
  40 | **Target Platform**: Web application (desktop + mobile responsive)
  41 | **Project Type**: Web application (frontend + backend)
  42 | **Performance Goals**: Chat responses < 2 seconds, UI interactions < 100ms
  43 | **Constraints**: Local-first design, offline-capable, responsive design (WCAG 2.1 accessible)
  44 | **Scale/Scope**: Single-page React app with FastAPI backend, 10-15 UI components to enhance
  45 |
  46 | ## Constitution Check
  47 | *GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
  48 |
  49 | ### I. Code Quality ✅
  50 | - Backend follows Python type hints, PEP 8 standards with ruff/black/mypy
  51 | - Frontend uses TypeScript strict mode, ESLint, Prettier
  52 | - Modular code organization with clear separation of concerns
  53 | - All changes will require code review
  54 |
  55 | ### II. Testing Standards ✅
  56 | - Unit tests for UI components (Jest)
  57 | - Integration tests for settings/export functionality
  58 | - Contract tests for API endpoints if new ones added
  59 | - Minimum 80% code coverage maintained
  60 |
  61 | ### III. User Experience Consistency ✅
  62 | - Uses existing Tailwind CSS + Radix UI design system
  63 | - Responsive design maintained
  64 | - Accessibility standards (WCAG 2.1) followed
  65 | - Consistent interaction patterns
  66 |
  67 | ### IV. Performance Requirements ✅
  68 | - UI interactions under 100ms target
  69 | - No impact on existing chat response performance (< 2 seconds)
  70 | - Efficient state management for settings
  71 |
  68 | ### Implementation Standards ✅
  69 | - Uses existing tech stack: FastAPI backend, React/Next.js frontend
  70 | - Follows local-first design with Ollama AI
  71 | - Maintains multi-modal support capabilities
  72 |
  73 | ### Development Process ✅
  74 | - Branch naming: feature/ui-polish-enhancements
  75 | - Commit messages prefixed [frontend], [ui], etc.
  76 | - Regular linting and testing gates
  77 | - Documentation updates with changes
  78 |
  79 | **Overall Assessment**: ✅ PASS - No constitution violations detected
  80 |
  81 | ## Project Structure
  82 |
  83 | ### Documentation (this feature)
  84 | ```
  85 | specs/004-polish-the-ui/
  86 | ├── plan.md              # This file (/plan command output)
  87 | ├── research.md          # Phase 0 output (/plan command)
  88 | ├── data-model.md        # Phase 1 output (/plan command)
  89 | ├── quickstart.md        # Phase 1 output (/plan command)
  90 | ├── contracts/           # Phase 1 output (/plan command)
  91 | └── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
  92 | ```
  93 |
  94 | ### Source Code (repository root)
  95 | ```
  96 | # Web application structure (frontend + backend detected)
  97 | backend/
  98 | ├── src/
  99 | │   ├── models/
  100 | │   ├── services/
  101 | │   └── api/
  102 | └── tests/
  103 |
  104 | frontend/
  105 | ├── src/
  106 | │   ├── components/
  107 | │   │   ├── settings/     # NEW: Settings components
  108 | │   │   ├── sidebar.tsx   # MODIFY: Fix toggle
  109 | │   │   ├── top-bar.tsx   # MODIFY: Add logo/name
  110 | │   │   └── message-input.tsx # MODIFY: Add multimodal buttons
  111 | │   ├── pages/
  112 | │   └── services/
  113 | └── tests/
  114 | ```
  115 |
  116 | **Structure Decision**: Web application (frontend + backend) - follows existing project structure
  117 |
  118 | ## Phase 0: Outline & Research
  119 | 1. **Extract unknowns from Technical Context** above:
  120 |    - Audio recording API compatibility research
  121 |    - Web search API integration patterns
  122 |    - Theme switching implementation best practices
  123 |    - Export/import data format standards
  124 |
  125 | 2. **Generate and dispatch research agents**:
  126 |    ```
  127 |    For each UI enhancement:
  128 |      Task: "Research best practices for {feature} in React/Next.js applications"
  129 |    For each integration:
  130 |      Task: "Find patterns for {integration} in web applications"
  131 |    ```
  132 |
  133 | 3. **Consolidate findings** in `research.md` using format:
  134 |    - Decision: [what was chosen]
  135 |    - Rationale: [why chosen]
  136 |    - Alternatives considered: [what else evaluated]
  137 |
  138 | **Output**: research.md with all implementation approaches documented
  139 |
  140 | ## Phase 1: Design & Contracts
  141 | *Prerequisites: research.md complete*
  142 |
  143 | 1. **Extract entities from feature spec** → `data-model.md`:
  144 |    - User Preferences: theme, selected models, UI preferences
  145 |    - Model Configuration: local Ollama models, cloud fallback settings
  146 |    - Export/Import Data: conversation history, settings backup
  147 |    - Audio Settings: recording preferences, transcription options
  148 |
  149 | 2. **Generate API contracts** from functional requirements:
  150 |    - Settings endpoints: GET/PUT user preferences
  151 |    - Export endpoint: POST /export with format options
  152 |    - Import endpoint: POST /import with data validation
  153 |    - Model management: GET available models, PUT model preferences
  154 |
  155 | 3. **Generate contract tests** from contracts:
  156 |    - Settings API contract tests
  157 |    - Export/import functionality tests
  158 |    - Model configuration tests
  159 |
  160 | 4. **Extract test scenarios** from user stories:
  161 |    - Settings panel accessibility scenario
  162 |    - Export/import workflow
  163 |    - Multimodal input interactions
  164 |
  165 | 5. **Update agent file incrementally** (O(1) operation):
  166 |    - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType roo`
  167 |      **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
  168 |    - If exists: Add only NEW tech from current plan
  169 |    - Preserve manual additions between markers
  170 |    - Update recent changes (keep last 3)
  171 |    - Keep under 150 lines for token efficiency
  172 |    - Output to repository root
  173 |
  174 | **Output**: data-model.md, /contracts/*, failing tests, quickstart.md, AGENTS.md updated
  175 |
  176 | ## Phase 2: Task Planning Approach
  177 | *This section describes what the /tasks command will do - DO NOT execute during /plan*
  178 |
  179 | **Task Generation Strategy**:
  180 | - Load `.specify/templates/tasks-template.md` as base
  181 | - Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
  182 | - Each contract → contract test task [P]
  183 | - Each entity → model creation task [P]
  184 | - Each user story → integration test task
  185 | - Implementation tasks to make tests pass
  186 |
  187 | **Ordering Strategy**:
  188 | - TDD order: Tests before implementation
  189 | - UI order: Settings infrastructure before sidebar fixes
  190 | - Dependency order: Data models before API before UI
  191 | - Mark [P] for parallel execution (independent components)
  192 |
  193 | **Estimated Output**: 20-25 numbered, ordered tasks in tasks.md
  194 |
  195 | **IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan
  196 |
  197 | ## Phase 3+: Future Implementation
  198 | *These phases are beyond the scope of the /plan command*
  199 |
  200 | **Phase 3**: Task execution (/tasks command creates tasks.md)
  201 | **Phase 4**: Implementation (execute tasks.md following constitutional principles)
  202 | **Phase 5**: Validation (run tests, execute quickstart.md, performance validation)
  203 |
  204 | ## Complexity Tracking
  205 | *Fill ONLY if Constitution Check has violations that must be justified*
  206 |
  207 | No constitution violations detected - clean implementation within existing architectural boundaries.
  208 |
  209 | ## Progress Tracking
  210 | *This checklist is updated during execution flow*
  211 |
  212 | **Phase Status**:
  213 | - [x] Phase 0: Research complete (/plan command)
  214 | - [x] Phase 1: Design complete (/plan command)
  215 | - [x] Phase 2: Task planning complete (/plan command - describe approach only)
  216 | - [ ] Phase 3: Tasks generated (/tasks command)
  217 | - [ ] Phase 4: Implementation complete
  218 | - [ ] Phase 5: Validation passed
  219 |
  220 | **Gate Status**:
  221 | - [x] Initial Constitution Check: PASS
  222 | - [x] Post-Design Constitution Check: PASS
  223 | - [x] All NEEDS CLARIFICATION resolved
  224 | - [x] Complexity deviations documented
  225 |
  226 | ---
  227 | *Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*