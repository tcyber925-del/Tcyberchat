# pr

Help me create and submit a pull request by following these steps in order:

1. First, show me the current status of my working directory:
   - Display any staged changes
   - Display any unstaged/uncommitted changes
   - Show the current branch name

2. Format and clean up the code:
   - Detect the project language or framework if possible, and run the appropriate formatter. For instance, if it is a Go project,  run `go fmt ./...`, and if it is a Rust project, run `cargo fmt`
   - Stage any formatting changes

3. Create a commit:
   - Generate a descriptive commit message following conventional commits format (e.g., feat:, fix:, docs:)
   - Include details about what changed and why
   - Commit all staged changes

4. Compare with base branch:
   - Determine the default branch (main or develop)
   - Generate a diff against the default branch
   - Create a structured PR description based on the diff, following the repository's PR template
   - Include:
     * Summary of changes
     * Technical implementation details
     * Testing steps
     * Related issues/tickets

5. Submit and open the PR:
   - Push changes to origin
   - Create PR using GitHub CLI (gh pr create)
   - Open the PR in browser (gh pr view --web)

Provide clear feedback after each step is completed or if any errors occur.

Stay focused on the PR creation workflow and don't execute any commands outside this scope.

Example good commit message:
"feat: implement user authentication flow
- Add JWT token generation
- Create login endpoint
- Add password hashing
- Update user model"

Example bad commit message:
"fixed stuff"
"updates"
"WIP"
