# Risk Analysis Guide

This reference provides a systematic approach to identifying, assessing, and mitigating risks in implementation plans. Load this file when conducting risk assessment for any planning task.

## Overview

Risk analysis is essential for creating robust implementation plans. The goal is not to avoid risk but to identify it early, assess its impact, and plan mitigations or contingencies.

## Risk Categories

### 1. Technical Risks

**Definition**: Risks arising from technical challenges, complexity, or unknowns.

**Common Technical Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| Performance issues | Code doesn't meet latency/throughput requirements | Medium | High |
| Scalability limits | Solution doesn't scale with growth | Low | High |
| Concurrency bugs | Race conditions, deadlocks, etc. | Medium | High |
| Memory issues | Leaks, excessive consumption | Low | Medium |
| Integration failures | External system integration breaks | Medium | High |
| Legacy code issues | Unexpected behavior in old code | Medium | Medium |
| Dependency conflicts | Library/API incompatibilities | Low | Medium |
| Security vulnerabilities | Introduces security weaknesses | Low | High |

**Mitigation Strategies:**
- Prototype performance-critical code early
- Add monitoring and alerting
- Implement circuit breakers for external calls
- Write integration tests before full implementation
- Conduct code reviews for security-sensitive areas

---

### 2. Dependency Risks

**Definition**: Risks from external dependencies, third-party services, or inter-team dependencies.

**Common Dependency Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| API changes | External API breaks compatibility | Medium | High |
| Service outages | External service unavailable | Medium | High |
| Library abandonment | Dependency no longer maintained | Low | Medium |
| Version conflicts | Dependencies conflict with each other | Medium | Medium |
| Rate limits | Hit API rate limits in production | Medium | Medium |
| Deprecation warnings | Tools/libraries being deprecated | Low | Medium |
| License issues | Dependency licensing conflicts | Low | Medium |

**Mitigation Strategies:**
- Pin dependency versions
- Use abstraction layers for external services
- Monitor dependency health and announcements
- Have fallback options ready
- Keep dependencies updated

---

### 3. Scope Risks

**Definition**: Risks from unclear, changing, or expanding requirements.

**Common Scope Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| Scope creep | Requirements expand during implementation | High | Medium |
| Unclear requirements | Requirements are ambiguous or missing | High | High |
| Hidden requirements | Requirements not initially stated | Medium | High |
| Stakeholder conflicts | Different stakeholders want different things | Medium | Medium |
| Compliance changes | New regulatory requirements emerge | Low | High |
| Technical debt | Quick fixes accumulate | Medium | Medium |

**Mitigation Strategies:**
- Get written requirements and confirmation
- Define MVP vs. stretch goals explicitly
- Implement iterative delivery with feedback
- Set change request process
- Document assumptions and constraints

---

### 4. Timeline Risks

**Definition**: Risks from time pressure, resource constraints, or scheduling issues.

**Common Timeline Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| Unrealistic deadline | Timeline is too aggressive | Medium | High |
| Resource constraints | Team capacity insufficient | Medium | High |
| Interruptions | Unexpected issues consume time | High | Medium |
| Blocking dependencies | Waiting on others | Medium | High |
| Review delays | Code review takes too long | Medium | Medium |
| Environment issues | Dev/staging environment problems | Medium | Medium |

**Mitigation Strategies:**
- Build in buffer time
- Identify critical path
- Break work into parallelizable chunks
- Escalate blockers early
- Automate where possible

---

### 5. Quality Risks

**Definition**: Risks to code quality, test coverage, or maintainability.

**Common Quality Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| Test gaps | Insufficient test coverage | Medium | Medium |
| Tech debt accumulation | Quality shortcuts taken | Medium | Medium |
| Documentation gaps | Code poorly documented | Medium | Low |
| Code complexity | Overly complex implementation | Medium | Medium |
| Inconsistent patterns | Doesn't follow codebase conventions | Low | Medium |
| Bug leakage | Bugs shipped to production | Medium | High |

**Mitigation Strategies:**
- Define quality gates upfront
- Require tests for new code
- Use linters and formatters
- Conduct peer reviews
- Plan for documentation

---

### 6. Operational Risks

**Definition**: Risks to deployment, monitoring, and ongoing operations.

**Common Operational Risks:**

| Risk | Description | Likelihood | Impact |
|------|-------------|------------|--------|
| Deployment failures | Deploy doesn't succeed | Medium | High |
| Rollback difficulties | Can't easily rollback | Low | High |
| Monitoring gaps | Issues not visible in production | Medium | Medium |
| Data issues | Data corruption or loss | Low | High |
| Migration problems | Migration fails or corrupts data | Low | High |
| Access issues | Permission/credential problems | Medium | Medium |

**Mitigation Strategies:**
- Plan deployment and rollback procedures
- Add monitoring and alerts before deploy
- Test migrations in staging
- Use feature flags for gradual rollout
- Document runbooks

---

## Risk Assessment Matrix

Use this matrix to prioritize risks:

| Impact → | Low | Medium | High |
|----------|-----|--------|------|
| **Likelihood ↓** | | | |
| High | Medium | High | Critical |
| Medium | Low | Medium | High |
| Low | Low | Low | Medium |

### Priority Definitions

**Critical**: Must address before proceeding. Create detailed mitigation plan.

**High**: Should address in plan. Have mitigation strategy ready.

**Medium**: Monitor and have contingency plan.

**Low**: Document and track, but don't block on it.

---

## Risk Documentation Format

Include this in your plan:

```markdown
## Risk Assessment

### Identified Risks

| Risk | Category | Likelihood | Impact | Priority |
|------|----------|------------|--------|----------|
| [Risk name] | [Category] | [H/M/L] | [H/M/L] | [Critical/High/Medium/Low] |

### Mitigation Plans

**Critical Risks:**
1. [Risk]: [Mitigation approach]

**High Risks:**
2. [Risk]: [Mitigation approach]

### Contingency Plans

**Critical Risks:**
- [Risk]: [Contingency if mitigation fails]
```

---

## Risk Identification Techniques

### 1. Codebase Analysis

- Search for similar implementations
- Check for patterns that caused issues
- Review recent bug fixes for context
- Identify code with known debt

### 2. Dependency Analysis

- Audit required dependencies
- Check version compatibility
- Review dependency health (maintenance, issues)
- Check for known vulnerabilities

### 3. Requirements Analysis

- Identify ambiguous requirements
- Look for missing scenarios
- Consider edge cases
- Identify conflicting requirements

### 4. Historical Analysis

- Check git history for similar changes
- Review PRs with similar scope
- Check issue tracker for related bugs
- Consult team memory for past issues

---

## Common Risk Patterns by Task Type

### New Feature Development
- Scope creep
- Integration complexity
- Performance requirements
- User acceptance

### Bug Fixes
- Root cause identification
- Regression risk
- Test coverage gaps
- Edge cases

### Refactoring
- Breaking changes
- Testing requirements
- Performance impact
- Feature flag needs

### Infrastructure Changes
- Deployment risk
- Rollback complexity
- Data migration
- Service disruption

### Security Changes
- Implementation correctness
- Audit requirements
- Performance impact
- Compatibility

---

## Risk Response Strategies

### Avoid
Eliminate the risk by changing the approach or scope.

### Mitigate
Reduce likelihood or impact through planning and controls.

### Transfer
Shift risk to another party (insurance, outsourcing, etc.).

### Accept
Acknowledge the risk and plan for recovery if it occurs.

### Contingency
Have a backup plan ready if the risk materializes.
