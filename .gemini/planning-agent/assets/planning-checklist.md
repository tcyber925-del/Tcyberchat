# Planning Checklist for AI Coding Agents

Use this checklist before and during implementation to ensure nothing is missed.

## Pre-Implementation Checklist

### Understanding
- [ ] User request is clear and unambiguous
- [ ] Success criteria are defined and measurable
- [ ] Constraints and limitations are identified
- [ ] Any clarifying questions have been answered
- [ ] Stakeholder expectations are aligned

### Context Gathering
- [ ] Relevant files have been explored
- [ ] Existing patterns and conventions are identified
- [ ] Related components and dependencies are mapped
- [ ] Current architecture or flow is understood
- [ ] Similar implementations have been reviewed

### Planning
- [ ] Complexity tier has been determined
- [ ] Architecture approach is defined
- [ ] Task breakdown is complete (atomic, independent tasks)
- [ ] Dependencies are identified and documented
- [ ] Risks are assessed with mitigations planned
- [ ] Verification strategy is defined
- [ ] Plan has been validated using plan-validator.py
- [ ] User has approved the plan

### Setup
- [ ] Required tools and dependencies are available
- [ ] Development environment is configured
- [ ] Test environment is accessible
- [ ] Documentation resources are available

---

## Task Execution Checklist

### Before Starting Each Task
- [ ] Previous tasks are complete (if dependent)
- [ ] Task requirements and acceptance criteria are clear
- [ ] Related code has been reviewed
- [ ] Any needed context is fresh in memory

### During Implementation
- [ ] Code follows existing patterns and style
- [ ] Changes are focused and minimal
- [ ] Complex logic is commented
- [ ] Edge cases are considered

### After Implementation
- [ ] Code compiles/builds successfully
- [ ] Related tests pass
- [ ] Linting passes
- [ ] Type checking passes (if applicable)
- [ ] No unintended side effects

---

## Pre-Commit Checklist

- [ ] All tests pass
- [ ] Code is linted and formatted
- [ ] Type checking passes (if applicable)
- [ ] Documentation is updated
- [ ] Commit message is clear and descriptive
- [ ] No debug or temporary code included
- [ ] No secrets or credentials included
- [ ] Sensitive changes are appropriately marked

---

## Pre-Deployment Checklist

- [ ] Code review completed and approved
- [ ] All tests pass (unit, integration, e2e)
- [ ] Performance is acceptable
- [ ] Security scan passes
- [ ] Database migrations tested
- [ ] Rollback plan is documented
- [ ] Monitoring and alerts are configured
- [ ] Documentation is updated
- [ ] Stakeholders are notified

---

## Review Checklist (Reviewing Others' Work)

- [ ] Requirements are met
- [ ] Code is clean and readable
- [ ] Tests are adequate
- [ ] Error handling is appropriate
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Documentation is complete
- [ ] Follows project conventions

---

## Post-Implementation Checklist

- [ ] User confirms success criteria are met
- [ ] Documentation is complete and accurate
- [ ] Knowledge is shared if needed
- [ ] Technical debt is documented if any
- [ ] Follow-up tasks are logged if needed
- [ ] Retrospective notes captured if applicable

---

## Quick Reference: Planning by Tier

### Simple Tasks
- [ ] Quick understanding check (2 minutes)
- [ ] 1-3 tasks identified
- [ ] Basic verification defined

### Moderate Tasks
- [ ] Full understanding phase
- [ ] Option analysis complete
- [ ] 5-15 tasks with dependencies
- [ ] Risk check completed
- [ ] Testing strategy defined

### Complex Tasks
- [ ] Detailed architecture review
- [ ] Comprehensive risk assessment
- [ ] 15-50 tasks with milestones
- [ ] Staged implementation plan
- [ ] Multiple verification points

### Epic Tasks
- [ ] Architectural review and approval
- [ ] Full risk assessment with stakeholders
- [ ] Phased roadmap with milestones
- [ ] Multi-team coordination plan
- [ ] Extensive verification strategy
