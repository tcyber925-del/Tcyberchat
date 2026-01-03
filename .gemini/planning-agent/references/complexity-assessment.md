# Complexity Assessment Guide

This reference helps AI coding agents assess task complexity and determine appropriate planning depth. Load this file when evaluating the scope of an implementation request.

## Overview

Complexity assessment determines how much planning effort is needed. Match planning depth to task complexity to avoid over-planning simple tasks or under-planning complex ones.

## Complexity Tiers

### Tier 1: Simple

**Definition**: Changes to 1-2 files, predictable outcome, well-understood scope.

**Characteristics:**
- Single file modification or one new file
- Changes are localized (no ripple effects)
- Existing patterns and tests apply directly
- No architectural decisions required
- Completion in less than one day

**Examples:**
- Rename a variable or function
- Add a single validation rule
- Fix a straightforward bug
- Update a constant value
- Add a single CSS rule

**Planning Requirements:**
- Understanding: Brief restatement of request
- Breakdown: 1-3 tasks
- Risk: Identify obvious issues only
- Verification: Basic test verification

**Estimated Effort:** 30 minutes to 2 hours

---

### Tier 2: Moderate

**Definition**: Changes to 3-10 files, multiple components affected, some coordination needed.

**Characteristics:**
- Multiple files in same module/directory
- May affect related functionality
- Some new patterns or approaches
- Requires understanding existing code structure
- Completion in 1-3 days

**Examples:**
- Add a new feature with 2-3 related functions
- Refactor a small module (5-10 functions)
- Fix a bug with changes across layers
- Add integration with one external service
- Update an API endpoint with new fields

**Planning Requirements:**
- Understanding: Full clarification of requirements
- Architecture: Option analysis for approach
- Breakdown: 5-15 tasks with dependencies
- Risk: Identify technical and scope risks
- Verification: Unit + integration tests

**Estimated Effort:** 4 hours to 3 days

---

### Tier 3: Complex

**Definition**: Changes to 10+ files, architectural considerations, significant scope.

**Characteristics:**
- Spans multiple modules or services
- Introduces new patterns or abstractions
- May require infrastructure changes
- Affects multiple features or user flows
- Completion in 1-2 weeks

**Examples:**
- New microservice or major component
- Database schema redesign
- Platform migration or upgrade
- Major refactoring across domains
- New authentication or authorization system

**Planning Requirements:**
- Understanding: Comprehensive with stakeholder alignment
- Architecture: Detailed design with trade-offs
- Breakdown: 15-50 tasks with milestones
- Risk: Full risk assessment with mitigations
- Verification: Comprehensive test strategy

**Estimated Effort:** 1-2 weeks

---

### Tier 4: Epic

**Definition**: System-wide changes, organizational impact, multiple teams involved.

**Characteristics:**
- Affects entire codebase or multiple services
- Requires architectural review and approval
- May span multiple quarters
- Involves multiple stakeholders
- Completion in 1+ months

**Examples:**
- Complete tech stack migration
- New platform or product launch
- Major security overhaul
- Architectural paradigm shift
- Multi-team coordination effort

**Planning Requirements:**
- Understanding: Documented with sign-off
- Architecture: ADRs, RFCs, review process
- Breakdown: Phased roadmap with milestones
- Risk: Full organizational risk assessment
- Verification: Staged rollout with monitoring

**Estimated Effort:** 1+ months

---

## Quick Assessment Checklist

Use this checklist to quickly determine tier:

```
Task Size
├── 1-2 files → Skip to complexity check
├── 3-10 files → Likely Moderate
├── 10+ files → Complex or Epic
└── System-wide → Epic

Complexity
├── Trivial change → Simple
├── Standard feature → Moderate
├── Challenging feature → Complex
└── Research needed → Complex+

Scope Clarity
├── Crystal clear → Consider lower tier
├── Mostly clear → Current tier
├── Some ambiguity → Consider higher tier
└── Unclear → Ask clarifying questions

Dependencies
├── No dependencies → Consider lower tier
├── Internal deps only → Current tier
├── External services → Consider higher tier
└── Multiple teams → Epic territory

Risk
├── Low risk → Consider lower tier
├── Medium risk → Current tier
├── High risk → Consider higher tier
└── Unknown risk → Assess before planning
```

## Complexity Indicators

### Indicators for Higher Tier

**Technical Complexity:**
- New technology or framework
- Performance-critical code
- Security-sensitive changes
- Distributed systems concerns
- Edge cases that are hard to test

**Scope Complexity:**
- Affects many user types
- Requires configuration/migration
- Breaking changes included
- Rollback considerations
- Compliance requirements

**Organizational Complexity:**
- Multiple stakeholders
- Cross-team dependencies
- External commitments
- Timeline pressure
- Knowledge gaps

### Indicators for Lower Tier

- Well-understood domain
- Existing patterns apply
- Small, isolated change
- Quick to verify
- Easy to rollback

## Effort Estimation

### File-Based Heuristic

| Tier | Files | Functions | Tests |
|------|-------|-----------|-------|
| Simple | 1-2 | 1-5 | 1-10 |
| Moderate | 3-10 | 5-20 | 10-50 |
| Complex | 10-50 | 20-100 | 50-200 |
| Epic | 50+ | 100+ | 200+ |

### Time-Based Guidelines

**Development Time:**
- Simple: 0.5-2 hours
- Moderate: 4-24 hours
- Complex: 40-120 hours
- Epic: 160+ hours

**Planning Time:**
- Simple: 5-10 minutes
- Moderate: 30-60 minutes
- Complex: 2-4 hours
- Epic: 1-2 days

**Review Time:**
- Simple: 10-20 minutes
- Moderate: 30-60 minutes
- Complex: 2-4 hours
- Epic: 1-2 days

## Adjusting Complexity Mid-Plan

Complexity assessment may change as you plan:

**Up-tiering Indicators:**
- Discovery of hidden dependencies
- Unplanned refactoring required
- Security concerns emerge
- Scope creep detected
- Risk assessment reveals issues

**Down-tiering Indicators:**
- Simpler than expected
- Existing code can be leveraged
- Fewer edge cases than anticipated
- Dependencies resolved easily

## Special Cases

### Quick Wins (Simpler Than Assessment)

Some tasks appear complex but are actually simple:

- **Configuration changes** that don't affect logic
- **Documentation updates** without code changes
- **Test additions** for existing code
- **Dependency updates** with compatible APIs
- **Code moves** without logic changes

### Hidden Complexity (Simpler Appears Complex)

Some simple-looking tasks have hidden complexity:

- **One-line fixes** that affect many tests
- **API additions** requiring backward compatibility
- **Refactoring names** that ripple through codebase
- **Config changes** with cascading effects
- **看似简单** (Seemingly simple) tasks in unfamiliar codebases

## Output Format

After assessment, include this in your plan:

```markdown
## Complexity Assessment

- **Tier**: [1-Simple | 2-Moderate | 3-Complex | 4-Epic]
- **Estimated Files**: [number]
- **Estimated Tasks**: [number]
- **Estimated Effort**: [time range]
- **Planning Effort**: [time range]
- **Key Complexity Factors**: [list]
- **Risk Level**: [Low | Medium | High]
```
