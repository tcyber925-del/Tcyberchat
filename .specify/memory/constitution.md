<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0
- List of modified principles: N/A
- Added sections: N/A
- Removed sections: N/A
- Templates requiring updates: None
- Follow-up TODOs: N/A
-->

# TcyberChatbot Constitution

## Core Principles

### Component-First
Every feature starts as a reusable component; Components must be self-contained, independently testable, documented; Clear purpose required - no organizational-only components.

### Web Interface
Every component exposes functionality via web UI; User interactions via forms/buttons, responses via UI updates, errors via user notifications; Support accessible and responsive formats.

### Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced.

### Integration Testing
Focus areas requiring integration tests: New component contract tests, Contract changes, Inter-component communication, Shared state management.

### Observability, Versioning & Simplicity
User interactions logged for debuggability; Structured logging required; Semantic versioning (MAJOR.MINOR.PATCH) format; Start simple, YAGNI principles.

## Additional Constraints

Technology stack requirements: React/TypeScript/Vite for frontend, Python/FastAPI for backend, LangChain/ChromaDB for RAG, Ollama for local AI; Compliance with web accessibility standards; Responsive design for all devices.

## Development Workflow

Code review requirements: All changes reviewed by at least one other developer; Testing gates: Must pass all automated tests; Deployment approval process: Automated CI/CD with manual approval for production.

## Governance

Constitution supersedes all other practices; Amendments require documentation, approval, migration plan. All PRs/reviews must verify compliance; Complexity must be justified; Use guidance files for runtime development guidance.

**Version**: 1.1.0 | **Ratified**: 2025-09-22 | **Last Amended**: 2025-09-22