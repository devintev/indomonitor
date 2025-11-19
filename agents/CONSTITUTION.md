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

### Database Operations
- **ALWAYS use `scripts/manage_db.py` for MySQL database operations** – this is the primary tool for database management
- **Database inspection**: Run `./scripts/manage_db.py` to get overview of all databases and tables with row counts
- **Execute SQL queries**: Use `./scripts/manage_db.py --sql "YOUR SQL QUERY"` for any SQL operation
- **Output formats**: Choose from text (default), JSON (`--json`), or YAML (`--yaml`) output formats
- **JSON output for programmatic use**: Add `--json` flag for structured JSON responses suitable for parsing
- **YAML output for human-readable structured data**: Add `--yaml` flag for YAML formatted output
- **Specify server**: Use `--server connection_name` to target specific connection (default uses `config/database.yaml` default_connection)
- **Auto-select database**: Use `--database database_name` to auto-select a database (allows unqualified table names)
- **SQL Operator Compatibility**: Both `!=` and `<>` operators work correctly. The script automatically fixes shell escaping issues with the `!` character, so you can use either operator for "not equal" comparisons.
- **Examples**:
  - List all databases and tables: `./scripts/manage_db.py`
  - Execute query: `./scripts/manage_db.py --sql "SELECT * FROM table LIMIT 10"`
  - Get JSON response: `./scripts/manage_db.py --sql "SHOW DATABASES" --json`
  - Get YAML response: `./scripts/manage_db.py --sql "SHOW DATABASES" --yaml`
  - Use specific server: `./scripts/manage_db.py --server production --sql "SHOW TABLES"`
  - Auto-select database: `./scripts/manage_db.py --database indomonitor --sql "SHOW CREATE TABLE scraper_scripts"`
  - Combined: `./scripts/manage_db.py --server vosscloud --database indomonitor --sql "DESCRIBE users"`
  - Query with NOT EQUAL: `./scripts/manage_db.py --database indomonitor --sql "SELECT * FROM news_sites WHERE status != 'deleted'" --yaml`

### News Site Management
- **Use `scripts/indomonitor.py` for managing news sites** – CLI tool for adding and managing monitored news sites
- **Adding news sites**: Use `./scripts/indomonitor.py add site <url>` to add new sites to monitor
- **Listing news sites**: Use `./scripts/indomonitor.py list news_sites` to get all URLs (one per line)
- **Automatic features**: The tool validates URLs, checks for duplicates, extracts site names from domains, and sets initial status
- **Uses auto-increment IDs**: Follows existing schema design (INT AUTO_INCREMENT, not UUID)
- **Examples**:
  - Add a news site: `./scripts/indomonitor.py add site https://www.reuters.com`
  - List all news sites: `./scripts/indomonitor.py list news_sites`
  - Show help: `./scripts/indomonitor.py -h` or `./scripts/indomonitor.py add site -h`
  - Script will detect duplicates and report existing entries
  - Site name is automatically extracted from domain (e.g., "www.reuters.com" → "Reuters")
