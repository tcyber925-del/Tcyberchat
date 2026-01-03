# Planning Frameworks for AI Coding Agents

This reference documents the core planning methodologies used by the enhanced planning skill. Load this file when creating plans for implementation tasks.

## Overview

Effective planning follows a consistent 7-phase workflow adapted to task complexity. Each phase produces specific outputs that feed into subsequent phases.

## Phase 1: Understanding

**Objective**: Gain complete clarity on what is being requested.

### Inputs
- User request (raw prompt or description)
- Any provided context (files, screenshots, links)

### Outputs
- Restated problem in your own words
- List of success criteria
- Identified constraints and assumptions
- Clarifying questions (if gaps exist)

### Techniques

**Clarification Questions Template:**
```
1. What does "success" look like for this task?
2. Are there any files, functions, or code patterns I should reference?
3. What is the timeline or urgency?
4. Are there any restrictions (e.g., specific libraries, coding style)?
5. Who will review or use the output?
```

**Success Criteria Checklist:**
- [ ] Functional requirements clearly stated
- [ ] Non-functional requirements identified (performance, security, UX)
- [ ] Edge cases acknowledged
- [ ] Acceptance criteria defined (testable conditions)

## Phase 2: Analysis

**Objective**: Understand the current state and what changes are needed.

### Context Gathering
1. Explore relevant files in the codebase
2. Identify related components and dependencies
3. Map the current architecture or flow
4. Note existing patterns and conventions

### Change Impact Assessment
- Which files will be modified?
- Which files will be created?
- Which tests may break?
- Which documentation needs updates?

### Output Format: Change Impact Summary
```
Files to Modify: [list]
Files to Create: [list]
Tests Affected: [list]
Docs to Update: [list]
Breaking Changes: [none | list with migration plan]
```

## Phase 3: Architecture

**Objective**: Design the solution approach.

### Design Considerations

**Option Analysis Template:**
```
Option 1: [name]
  Pros: [list]
  Cons: [list]
  Effort: [small/medium/large]
  Risk: [low/medium/high]

Option 2: [name]
  ...

Recommended: [option] because [reasoning]
```

### Key Design Questions

**For New Features:**
- What data models are needed?
- How does this integrate with existing systems?
- What APIs or interfaces are required?
- How will this scale?

**For Bug Fixes:**
- What is the root cause?
- Is this a symptom or the actual problem?
- What tests would catch this regression?
- Is there a minimal fix or is refactoring needed?

**For Refactoring:**
- What is the motivation (performance, readability, debt)?
- What is the target architecture?
- How will changes be staged safely?
- What is the backward compatibility strategy?

## Phase 4: Breakdown

**Objective**: Decompose the work into actionable tasks.

### Task Decomposition Principles

1. **Atomic**: Each task should be completable in 2-4 hours
2. **Independent**: Tasks should not block each other unnecessarily
3. **Verifiable**: Each task has clear completion criteria
4. **Ordered**: Dependencies are explicit and logical

### Task Structure
```
- [Task ID]: Brief task description
  Files: [list of files affected]
  Depends: [task IDs this depends on]
  Verifies: [how to confirm completion]
  Effort: [1-5 scale]
```

### Effort Estimation Guidelines

| Score | Meaning | Examples |
|-------|---------|----------|
| 1 | ~30 min | Simple variable rename, one-line fix |
| 2 | ~1 hour | Small function change, single test |
| 3 | ~2-3 hours | New function, moderate refactor |
| 4 | ~4-6 hours | New module, significant feature |
| 5 | ~8+ hours | Complex feature, architectural change |

## Phase 5: Dependencies

**Objective**: Identify and document all dependencies.

### Dependency Categories

**Code Dependencies:**
- Internal: Other modules, utilities, or services in the codebase
- External: Third-party libraries, APIs, or services

**Environment Dependencies:**
- Build tools and versions
- Runtime requirements
- Database migrations
- Infrastructure changes

**Knowledge Dependencies:**
- Documentation to review
- Decisions already made (check git history, PRs)
- Subject matter experts to consult

### Dependency Graph Example
```
Task A: Create data model
  └─ Requires: Nothing

Task B: Implement API endpoints
  ├─ Depends on: Task A
  └─ External: pydantic library

Task C: Write unit tests
  ├─ Depends on: Task B
  └─ External: pytest framework

Task D: Update documentation
  ├─ Depends on: Task C
  └─ Requires: API documentation tool
```

## Phase 6: Risk Assessment

**Objective**: Identify potential problems and plan mitigations.

### Risk Categories

1. **Technical Risks**: Implementation challenges, complexity
2. **Dependency Risks**: External libraries, APIs, services
3. **Scope Risks**: Requirements creep, unclear scope
4. **Timeline Risks**: Unrealistic deadlines, blocking dependencies

### Risk Matrix
| Probability | Impact | Priority |
|-------------|--------|----------|
| High | High | Critical - address first |
| High | Low | High - plan mitigation |
| Low | High | High - have contingency |
| Low | Low | Low - document and monitor |

### Mitigation Strategies

**For Technical Risks:**
- Prototype complex parts first
- Break into smaller, provable tasks
- Research alternatives before committing

**For Dependency Risks:**
- Pin versions for reproducibility
- Have fallback options ready
- Test integration early

**For Scope Risks:**
- Define MVP vs. stretch goals
- Get early feedback on approach
- Set explicit scope boundaries

**For Timeline Risks:**
- Identify critical path
- Plan for interruptions
- Build in buffer time

## Phase 7: Verification

**Objective**: Define how to confirm the implementation is correct.

### Verification Types

**Unit Tests:**
- Test individual functions/classes
- Cover edge cases
- Aim for high coverage of changed code

**Integration Tests:**
- Test component interactions
- Test API contracts
- Verify data flow

**Manual Testing:**
- User acceptance criteria
- Exploratory testing
- Edge case verification

**Code Quality:**
- Linting passes
- Type checking passes
- No security vulnerabilities
- Documentation complete

### Verification Checklist
```
[ ] Unit tests written for new code
[ ] Existing tests pass
[ ] Integration tests verified
[ ] Manual testing completed
[ ] Code review feedback addressed
[ ] Documentation updated
[ ] Performance meets requirements
[ ] Security scan passed
```

## Planning by Complexity Tier

### Simple Tasks (1-2 files)
- Skip detailed architecture
- Focus on: Understanding + Breakdown + Verification
- Plan: 1-2 paragraphs

### Moderate Tasks (3-10 files)
- Full 7-phase planning
- Include option analysis
- Plan: 1-2 pages

### Complex Tasks (10+ files, multi-file architecture)
- Detailed architecture with diagrams
- Comprehensive risk assessment
- Staged implementation with milestones
- Plan: Multiple pages with supporting docs

### Epic Tasks (system-wide)
- Requires architectural review
- Multiple planning sessions
- Consider creating ADRs (Architecture Decision Records)
- Full project plan with phases and milestones
