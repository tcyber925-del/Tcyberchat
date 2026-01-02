# Task Templates

This reference provides reusable templates for different types of implementation tasks. Use these templates to speed up planning and ensure consistency.

## Overview

Different task types require different planning approaches. These templates provide structured formats that can be adapted to specific needs.

---

## Feature Implementation Template

Use for: Adding new functionality to the codebase.

```markdown
## Feature: [Feature Name]

### Overview
**Goal**: [One-sentence description]
**Priority**: [P0/P1/P2/P3]
**Estimated Effort**: [time]

### Requirements
**Must Have:**
- [ ] [Requirement 1]
- [ ] [Requirement 2]

**Should Have:**
- [ ] [Requirement 3]
- [ ] [Requirement 4]

**Nice to Have:**
- [ ] [Requirement 5]
- [ ] [Requirement 6]

### Architecture
**Proposed Approach**: [Brief description]
**Alternative Considered**: [Brief description]

### Files to Create
- `path/to/new-file.js`
- `path/to/another-file.py`

### Files to Modify
- `path/to/existing-file.js`
- `path/to/another-file.py`

### Tasks
1. **Task: [Task name]**
   - Files: [list]
   - Depends: [none or task ID]
   - Effort: [1-5]
   - Verifies: [how to confirm completion]

2. **Task: [Task name]**
   - Files: [list]
   - Depends: [task ID]
   - Effort: [1-5]
   - Verifies: [how to confirm completion]

### Dependencies
- Internal: [list]
- External: [list]
- Environment: [list]

### Testing Strategy
- Unit Tests: [where and what]
- Integration Tests: [where and what]
- Manual Testing: [scenarios]

### Risks and Mitigations
- [Risk]: [Mitigation]

### Rollback Plan
[How to undo if needed]
```

---

## Bug Fix Template

Use for: Fixing defects, errors, or unexpected behavior.

```markdown
## Bug Fix: [Bug Title]

### Overview
**Problem**: [Brief description of the bug]
**Severity**: [Critical/High/Medium/Low]
**Frequency**: [Always/Sometimes/Rarely]
**Impact**: [Who/what is affected]

### Root Cause Analysis
**What happens**: [Detailed description of symptoms]
**Expected behavior**: [What should happen]
**Actual behavior**: [What actually happens]
**Root cause**: [Technical explanation of why]

### Reproduction
**Steps to reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Environment:**
- OS: [version]
- Browser: [if applicable]
- Code version: [commit/hash]

### Fix Strategy
**Approach**: [How to fix]
**Why this approach**: [Reasoning]
**Alternative**: [Other approaches considered]

### Files to Modify
- `path/to/file.js` - [what changes]
- `path/to/file.py` - [what changes]

### Tasks
1. **Task: Add failing test**
   - Files: `path/to/test.js`
   - Depends: none
   - Effort: 2
   - Verifies: Test fails with current code

2. **Task: Implement fix**
   - Files: [list]
   - Depends: 1
   - Effort: [1-5]
   - Verifies: Test passes

3. **Task: Verify fix**
   - Files: [list of test files]
   - Depends: 2
   - Effort: 2
   - Verifies: All related tests pass

### Regression Prevention
- Tests to add: [list]
- Areas to verify: [list]
- Manual testing scenarios: [list]

### Documentation
- [ ] Update relevant docs
- [ ] Add comment explaining fix
- [ ] Update changelog
```

---

## Refactoring Template

Use for: Improving code structure without changing behavior.

```markdown
## Refactor: [Component/Module Name]

### Overview
**Motivation**: [Why refactor]
- [Reason 1]
- [Reason 2]

**Scope**: [What is included]
**Scope Boundaries**: [What is NOT included]

### Current State
**Problems identified:**
- [Problem 1]
- [Problem 2]

**Complexity**: [Simple/Moderate/Complex]
**Technical debt level**: [Low/Medium/High]

### Target State
**Architecture**: [Brief description]
**Key improvements:**
- [Improvement 1]
- [Improvement 2]

### Constraints
- Must maintain API compatibility
- No behavioral changes
- Performance must not degrade
- Backward compatibility: [required/not required]

### Files Affected
**Will modify:**
- `path/to/file1.js`
- `path/to/file2.py`

**Will create:**
- `path/to/new-file.js`

**Will delete:**
- `path/to/old-file.js`

### Tasks
1. **Task: Create new structure**
   - Files: [new files]
   - Depends: none
   - Effort: [1-5]
   - Verifies: New files exist and compile

2. **Task: Copy logic to new structure**
   - Files: [new + existing]
   - Depends: 1
   - Effort: [1-5]
   - Verifies: Logic compiles, no functionality

3. **Task: Update references**
   - Files: [files calling old code]
   - Depends: 2
   - Effort: [1-5]
   - Verifies: No import/reference errors

4. **Task: Run full test suite**
   - Files: [test files]
   - Depends: 3
   - Effort: 2
   - Verifies: All tests pass

5. **Task: Remove old code**
   - Files: [old files]
   - Depends: 4
   - Effort: 1
   - Verifies: Old files deleted, tests still pass

### Testing Strategy
- [ ] Verify existing tests still pass
- [ ] Add tests for new structure
- [ ] Performance comparison
- [ ] Manual verification if needed

### Migration Plan
For dependent code:
1. [Step 1]
2. [Step 2]

### Rollback Plan
[How to restore if issues arise]
```

---

## Infrastructure Change Template

Use for: Changes to build, deployment, configuration, or environment.

```markdown
## Infrastructure Change: [Change Description]

### Overview
**Goal**: [What this change accomplishes]
**Type**: [Build/Deploy/Config/Environment/Other]
**Affected Environments**: [Dev/Staging/Prod]

### Change Description
**Current state**: [Brief description]
**Proposed state**: [Brief description]
**Reason for change**: [Why this is needed]

### Technical Details
**Components affected:**
- [Component 1]
- [Component 2]

**Configuration changes:**
```yaml
# Example config change
setting: new-value  # was: old-value
```

### Pre-requisites
- [Prerequisite 1]
- [Prerequisite 2]

### Files to Modify
- `path/to/config/file.yaml`
- `path/to/Dockerfile`
- etc.

### Files to Create
- `path/to/new/config.yaml`

### Tasks
1. **Task: [Task name]**
   - Files: [list]
   - Depends: none
   - Effort: [1-5]
   - Verifies: [completion criteria]

### Validation Strategy
- [ ] Config syntax validation
- [ ] Integration testing
- [ ] Staging deployment
- [ ] Smoke tests after deploy

### Rollback Plan
[Detailed rollback steps]

### Monitoring
**Metrics to watch:**
- [Metric 1]
- [Metric 2]

**Alerts to configure:**
- [Alert 1]
- [Alert 2]
```

---

## Database Migration Plan

Use for: Changes to database schema, data backfills, or data migrations.

```markdown
## Migration: [Migration Name]

### Overview
**Goal**: [Brief description]
**Database**: [Postgres/MySQL/MongoDB/etc]
**Type**: [Schema Change/Data Backfill/Data Cleanup]
**Risk Level**: [High/Medium/Low]

### Schema Changes
**Table/Collection**: [Name]
- [ ] Add column/field: `[name]` ([type])
- [ ] Remove column/field: `[name]`
- [ ] Change type: `[name]` from [old] to [new]
- [ ] Add index: [name] on [fields]

### Data Migration Strategy
**Approach**: [Online/Offline/Lazy Migration]
**Volume**: [Estimated row/document count]
**Estimated Time**: [Duration]

### Tasks
1. **Task: Create migration script**
   - Files: `migrations/V1__desc.sql`
   - Depends: none
   - Effort: [1-5]
   - Verifies: Script passes linting

2. **Task: Test migration (Down/Up)**
   - Files: [test files]
   - Depends: 1
   - Effort: [1-5]
   - Verifies: Can migrate up and down without data loss

3. **Task: Execute in Staging**
   - Files: none
   - Depends: 2
   - Effort: [1-5]
   - Verifies: Staging DB matches expected state

### Rollback Plan
**Revert Script**: `migrations/V1__undo_desc.sql`
**Data Restore**: [Strategy for restoring data if corrupted]

### Verification Queries
```sql
SELECT count(*) FROM table WHERE new_column IS NOT NULL;
```
```

---

## Test Strategy Plan

Use for: Planning comprehensive testing for a feature or system.

```markdown
## Test Strategy: [Feature/System Name]

### Overview
**Scope**: [What is being tested]
**Out of Scope**: [What is NOT being tested]
**Tools**: [Jest/Pytest/Cypress/etc]

### Test Levels

#### Unit Tests
**Focus**: Individual functions and components
**Coverage Goal**: [XX]%
**Key Scenarios**:
- [ ] [Scenario 1]
- [ ] [Scenario 2: Edge case]
- [ ] [Scenario 3: Error handling]

#### Integration Tests
**Focus**: API endpoints and database interactions
**Key Scenarios**:
- [ ] [Flow 1: Happy path]
- [ ] [Flow 2: Invalid input]
- [ ] [Flow 3: Database error]

#### E2E Tests
**Focus**: Full user journeys
**Key Scenarios**:
- [ ] [User Journey 1]
- [ ] [User Journey 2]

### Test Data
- [ ] Fixtures needed
- [ ] Mock data requirements
- [ ] Seed scripts

### Automation
**CI/CD Integration**:
- [ ] Run on PR
- [ ] Run nightly
- [ ] Run on deploy

### Manual Testing
**Exploratory Sessions**:
- [ ] Session 1: Usability
- [ ] Session 2: Security boundaries
```

---

## Documentation Update Template

Use for: Updating or creating documentation.

```markdown
## Documentation: [Document Name]

### Overview
**Type**: [API/User Guide/Internal/Readme/Other]
**Location**: `path/to/docs/file.md`
**Purpose**: [What this documents]

### Current State
**Issues identified:**
- [Issue 1]
- [Issue 2]
- [Issue 3]

### Changes Required
**Sections to add:**
- [Section 1]

**Sections to update:**
- [Section 2]

**Sections to remove:**
- [Section 3]

### Tasks
1. **Task: [Task name]**
   - Files: [list]
   - Depends: none
   - Effort: [1-5]
   - Verifies: [completion criteria]

### Review Process
- [ ] Technical accuracy review
- [ ] Editorial review
- [ ] Stakeholder sign-off

### Related
- PR/Issue: [link]
- Related documentation: [list]
```

---

## Quick Reference: Task Template Selection

| Task Type | Template to Use |
|-----------|-----------------|
| Add new feature | Feature Implementation |
| Fix a bug | Bug Fix |
| Improve code structure | Refactoring |
| Update build/deploy config | Infrastructure Change |
| Create/update docs | Documentation Update |
| Database migration | Database Migration Plan |
| Test planning | Test Strategy Plan |
| API change | Feature Implementation |
| Performance optimization | Refactoring + Infrastructure |
| Security hardening | Infrastructure Change + Feature |

---

## Task Template Best Practices

1. **Always include verification criteria** - How will you know the task is done?

2. **Keep tasks atomic** - If a task takes more than 4 hours, break it down.

3. **Document dependencies** - What must be completed first?

4. **Include rollback plan** - For non-trivial changes, how do you undo?

5. **Define done clearly** - What conditions must be met to consider complete?

6. **Be specific about files** - Don't say "update config", say "update config/database.yml"