---
name: planning-agent
description: Creates comprehensive implementation plans for coding tasks before writing any code. Use when users request features, bug fixes, refactoring, or any development work. This skill ensures every coding task starts with a clear, structured plan covering requirements analysis, technical approach, task breakdown, dependencies, risk assessment, and verification strategy.
---

# Planning Agent

Before implementing any coding task, create a structured plan using the framework below.

## When to Trigger

Always trigger this skill when:
- User asks to "create", "build", "implement", "add", "make"
- User asks to "fix", "debug", "resolve", "repair"
- User asks to "refactor", "rewrite", "restructure"
- User asks to "update", "modify", "change"
- User asks "how to" for implementation tasks
- Any request that requires writing code

## Quick Start

For simple tasks (1-2 files):
1. Run `python scripts/complexity-scorer.py "task description" --path .` to confirm tier
2. Create brief plan with Understanding, Breakdown, Verification sections
3. Skip detailed architecture

For moderate+ tasks:
1. Run complexity scorer to confirm tier: `python scripts/complexity-scorer.py "task" --path .`
2. Load `references/context-gathering.md` and gather codebase context
3. Load `references/planning-frameworks.md` for detailed methodology
4. Load `references/task-templates.md` for task structure templates
5. Create comprehensive plan with all 7 phases
6. Validate with `python scripts/plan-validator.py plan.md`
7. Present plan to user for approval

## 7-Phase Planning Workflow

### Phase 1: Understanding
- Restate the problem in your own words
- Identify success criteria
- List constraints and assumptions
- Ask clarifying questions if gaps exist

### Phase 2: Analysis (Context Gathering)
- **Consult `references/context-gathering.md`**
- Explore relevant files in the codebase using `list_directory` and `glob`
- Identify related components and dependencies
- Map current architecture or flow
- Note existing patterns and conventions

### Phase 3: Architecture
- Propose solution approach
- Document key design decisions
- Consider alternatives and trade-offs
- Select best option with reasoning

### Phase 4: Breakdown
- Decompose into atomic, verifiable tasks
- Estimate effort for each task (1-5 scale)
- Define clear completion criteria
- Order tasks logically

### Phase 5: Dependencies
- Identify code dependencies (internal and external)
- List environment prerequisites
- Map task dependencies
- Highlight critical path

### Phase 6: Risk Assessment
- Identify technical risks
- Assess dependency risks
- Consider scope and timeline risks
- Plan mitigations and contingencies

### Phase 7: Verification
- Define testing strategy (Unit, Integration, E2E)
- Identify success criteria
- Plan manual verification steps with specific commands
- Set quality gates

## Complexity Assessment

Use the 4-tier system to match planning depth to task scope:

| Tier | Files | Effort | Planning Time |
|------|-------|--------|---------------|
| Simple | 1-2 | 30min-2hr | 5-10 min |
| Moderate | 3-10 | 4hr-3 days | 30-60 min |
| Complex | 10-50 | 1-2 weeks | 2-4 hours |
| Epic | 50+ | 1+ month | 1-2 days |

Run `python scripts/complexity-scorer.py "task description" --path .` for quick assessment.

## Reference Files

Load these resources as needed:

- **context-gathering.md**: Guide for effective codebase exploration
- **planning-frameworks.md**: Detailed 7-phase methodology with techniques
- **complexity-assessment.md**: Tier definitions and assessment checklist
- **risk-analysis.md**: Risk categories and mitigation strategies
- **task-templates.md**: Reusable templates for features, bugs, refactors, tests, migrations

## Tools

### Complexity Scorer
```bash
python scripts/complexity-scorer.py "task description" --path .
python scripts/complexity-scorer.py "task" --path . --json
python scripts/complexity-scorer.py --interactive
```

### Plan Validator
```bash
python scripts/plan-validator.py plan.md
python scripts/plan-validator.py plan.md --json
python scripts/plan-validator.py --interactive
```

## Planning Checklist

Use `assets/planning-checklist.md` as a reference:
- Pre-implementation checklist
- Task execution checklist
- Pre-commit checklist
- Pre-deployment checklist
- Post-implementation checklist

## Standard Plan Format

```markdown
# Implementation Plan: [Task Name]

## 1. Understanding
- What is being asked?
- Success criteria:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]

## 2. Analysis
- Files to modify: [list]
- Files to create: [list]
- Related components: [list]

## 3. Architecture
- Proposed approach: [description]
- Alternatives considered: [list]
- Key design decisions: [list]

## 4. Task Breakdown
- [Task ID]: [Brief description]
  - Files: [list]
  - Depends: [none or task ID]
  - Effort: [1-5]
  - Verifies: [completion criteria]

## 5. Dependencies
- Internal: [list]
- External: [list]
- Environment: [list]

## 6. Risk Assessment
| Risk | Category | Impact | Mitigation |
|------|----------|--------|------------|
| [Risk] | [Category] | [H/M/L] | [Strategy] |

## 7. Verification
- Unit tests: [where and what]
- Integration tests: [where and what]
- Manual testing: [scenarios]
- Quality gates: [list]

## Complexity Assessment
- **Tier**: [Simple/Moderate/Complex/Epic]
- **Estimated Effort**: [time]
- **Risk Level**: [Low/Medium/High]
```

## Planning Principles

1. **Context First**: Never plan without exploring the codebase first.
2. **Never skip planning**: Even small tasks benefit from a brief plan.
3. **Match depth to complexity**: Simple tasks need light planning.
4. **Be specific**: Reference actual files, functions, and code patterns.
5. **Break it down**: Decompose into atomic, verifiable steps.
6. **Identify risks**: Call out potential problems early.
7. **Validate plans**: Use plan-validator.py before presenting.

## Output

After creating the plan:
1. Validate with `python scripts/plan-validator.py`
2. Present to user with: "Does this plan align with your expectations?"
3. Only proceed after user confirmation
4. Use planning-checklist.md throughout implementation