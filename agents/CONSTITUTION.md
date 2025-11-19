### Project Awareness & Context
- **Always read `agents/ARCHITECTURE.md`** at the start of a new conversation to understand the project's complete architecture, development patterns, and critical implementation guidelines.
- **Always read `agents/REPO.md`** before any github relevant actions. The file will inform you whether and what role a github repo plays in this project. Follow possible instructions directly - if applicable
- **Always check `agents/TASKS.md`** when starting a new conversation and before starting a new task. If the task isn't listed, add it with a brief description and today's date first before proceeding to implement it. Always keep this file updated by marking completed tasks as completed immediately.
- **Reference `agents/DOCUMENTATION.md`** or individual sections in it to make sure that the proper library and framework documentation is considered before starting any task. Add any lessons-learned or pitfalls-to-avoid into that section whenever they come up.

### Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.

### Task Completion
- **ALWAYS mark completed tasks (or sub tasks) in `agents/TASKS.md`** IMMEDIATELY after finishing them. Don't mark user-verification-tasks as completed unless the user has clearly confirmed to do so.
- **Follow the format provided in `agents/TASKS.md`** when creating new tasks (with  `- [ ] subtask name`, documentation check first, user verification, etc)

### Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline comment** explaining the why, not just the what.

### AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified packages in their correct version and get their documentation via tools (mdfetch or context7) or any other way mentioned in `agents/DOCUMENTATION.md`.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `agents/TASKS.md`.
- **Never change code unless explicitly instructed** Never assume a question as an instruction to act but only as an instruction to respond and explain. Only start changing files when user gave permission. Follow the practice of 1. Investigate, 2. Reflect, 3. Explain and Suggest to user 4. Wait for user instructions response of permission.
- **Use folder `tmp_agent/` for any shell scripts or other scripts that you might use to streamline repeated commands or tests or to run tests on components.

### Python Tooling & Dependency Management
- **Always use `uv` for dependency management and running Python code** – never use pip or virtualenv directly.
- **All Python scripts in `scripts/` should be self-executable** with the shebang line: `#!/usr/bin/env -S uv run --quiet --script`
- **Make scripts executable**: `chmod +x script_name.py` after creating them.
- **Installing dependencies**: Use `uv add package_name` in the project root.
- **Running scripts**: Execute directly with `./script_name.py` or via `uv run script_name.py`.
- **Prefer modern HTTP libraries**: Use `httpx` over `requests` (HTTP/2 and HTTP/3 support) and `hypercorn` over `uvicorn` (HTTP/2 and HTTP/3 support).
