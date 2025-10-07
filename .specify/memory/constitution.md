<!-- Version change: N/A → 1.0.0
List of modified principles: N/A (new constitution)
Added sections: I. Code Quality, II. Testing Standards, III. User Experience Consistency, IV. Performance Requirements, Implementation Standards, Development Process
Removed sections: N/A
Templates requiring updates: None - templates are generic and align with new principles
Follow-up TODOs: Set RATIFICATION_DATE upon agreement -->

# Local First Chatbot Constitution

## Core Principles

### I. Code Quality
All code must adhere to high standards of readability, maintainability, and efficiency. Backend uses Python type hints everywhere, follows PEP 8, linted with ruff, formatted with black, type checked with mypy. Frontend uses TypeScript strict mode, ESLint, Prettier. Modular code organization, clear separation of concerns. Every change requires code review.

### II. Testing Standards
Comprehensive testing is mandatory for all features. Unit tests for core logic with pytest (backend) and Jest (frontend), integration tests for API endpoints, contract tests for interfaces. Minimum 80% code coverage. TDD approach encouraged: write failing tests first, then implement. Contract tests ensure API stability.

### III. User Experience Consistency
UI must provide consistent, intuitive experience across all interactions. Follow design system with Tailwind CSS and Radix UI components. Responsive design for mobile and desktop. Ensure accessibility standards (WCAG 2.1). User feedback loops for usability testing. Streamlined navigation and clear error messages.

### IV. Performance Requirements
System must maintain high performance standards. Chat responses under 2 seconds, efficient RAG pipeline with optimized vector searches. Monitor latency, memory usage, and resource consumption. Asynchronous processing for heavy operations. Scalable architecture for growing document collections.

## Implementation Standards

Use specified tech stack: FastAPI for backend API, React 18 + TypeScript for frontend, SQLAlchemy for ORM, ChromaDB for vector storage, LangChain for AI orchestration. Local-first design with Ollama for LLM, optional hosted fallbacks. Multi-modal support: OCR for images, transcription for audio.

## Development Process

Follow AGENTS.md guidelines: branch naming feature/<desc>, commit messages prefixed [backend], [frontend], etc. Regular linting and testing gates. Pair programming for complex features. Documentation updates with code changes.

## Governance

Constitution takes precedence over all other practices. Amendments require documentation, approval, and migration plan. Version follows semver. Compliance verified in PR reviews. Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Original adoption date to be determined | **Last Amended**: 2025-09-24