# Context Gathering Guide for AI Agents

This guide outlines best practices for gathering context *before* creating an implementation plan. Accurate planning relies on a deep understanding of the existing codebase.

## Why Gather Context?

- **Avoid Assumptions**: Don't guess file paths or function names.
- **Identify Patterns**: Mimic existing coding styles and architectural patterns.
- **Find Dependencies**: Discover what else might break if you change a file.
- **Accurate Estimation**: Understand the complexity of what you're modifying.

## Workflow

### 1. Exploration (High Level)
Use `list_directory` to understand the project structure.

```python
# Check root structure
list_directory(dir_path=".")

# Check specific source folders
list_directory(dir_path="src")
list_directory(dir_path="backend")
```

**What to look for:**
- Where does the source code live? (`src`, `lib`, `app`)
- Where are tests? (`tests`, `spec`, `__tests__`)
- Where is configuration? (`config`, root files)

### 2. Search (Targeted)
Use `glob` and `search_file_content` to find relevant files.

**Finding by Name:**
```python
# Find all controller files
glob(pattern="**/*controller*")

# Find specific config file
glob(pattern="**/config.yaml")
```

**Finding by Content:**
```python
# Find usages of a function
search_file_content(pattern="processUserData", include="src/**/*.ts")

# Find where an API endpoint is defined
search_file_content(pattern="/api/v1/users")
```

### 3. Deep Dive (Reading)
Use `read_file` to examine the logic. **Do not just read the headers.**

- Read the file you intend to modify.
- Read the test file associated with it.
- Read any interface/type definitions imported.

```python
# Read multiple relevant files
read_file(file_path="src/users/userService.ts")
read_file(file_path="src/users/userService.test.ts")
```

## Context Gathering Checklist

Before writing your plan, ensure you can answer:

- [ ] **Where** will the new code live? (Exact file path)
- [ ] **What** existing code needs to change?
- [ ] **How** is similar functionality implemented elsewhere? (Reference implementation)
- [ ] **What** are the imports/dependencies required?
- [ ] **How** will I test this? (Existing test patterns)

## Common Pitfalls

1. **Hallucinating Paths**: creating `src/utils/helpers.js` when the project uses `src/shared/lib.ts`.
2. **Ignoring Types**: planning a JS change in a TS project without considering interfaces.
3. **Missed Dependencies**: forgetting that changing a database model requires a migration.
4. **Blind Refactoring**: planning to rename a function without checking all its call sites.

## Tool Usage Tips

- **`search_file_content` vs `grep`**: Always prefer `search_file_content`. It's faster and respects `.gitignore`.
- **`glob`**: Use it to verify file existence before adding it to a plan.
- **`read_file`**: If a file is huge, read relevant sections using `offset` and `limit` if needed, but usually reading the whole file is better for context if it fits.

## Example Session

**Goal**: Add a "delete user" feature.

1. `list_directory(".")` -> see `backend/` folder.
2. `glob("backend/**/*user*")` -> find `backend/models/user.py`, `backend/routes/user_routes.py`.
3. `read_file("backend/routes/user_routes.py")` -> see how routes are defined (Flask? FastAPI?).
4. `read_file("backend/models/user.py")` -> see the User class/schema.
5. `search_file_content("delete")` -> see how other delete operations are handled.
6. **Plan Creation**: Now you can write a plan referencing specific files and patterns.
