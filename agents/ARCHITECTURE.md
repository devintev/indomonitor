# System Architecture

## Overview
Automated news monitoring system with autonomous Claude Code agents that scrape news websites, extract content, and store it in a database. The system is self-healing and self-maintaining through a multi-agent orchestration pattern.

## Critical Implementation Reminders
- **Python Dependency Management**: Always use `uv` (never pip or virtualenv)
- **Self-Executable Scripts**: All Python scripts in `scripts/` must start with `#!/usr/bin/env -S uv run --quiet --script` and be made executable (`chmod +x`)
- **HTTP Library Preference**: Use `httpx` (not `requests`) and `hypercorn` (not `uvicorn`) for HTTP/2 and HTTP/3 support
- **Script Organization**: Individual scraper scripts stored as strings in database, executed by manager agent
- **Configuration Management**: Database connections defined in `config/database.yaml`, credentials in `.env` using pattern `{CONNECTION_NAME}_MYSQL_{PARAMETER}`

## Frameworks and Libraries
- **Python**: 3.12+
- **Dependency Management**: uv
- **Web Scraping**: BeautifulSoup4, Scrapy, Playwright
- **HTTP Client**: httpx (HTTP/2, HTTP/3 support)
- **Server**: hypercorn (HTTP/2, HTTP/3 support)
- **Database**: MySQL (all database operations)
- **Scheduling**: APScheduler or Celery
- **Agent Platform**: Claude Code (headless mode)
- **Environment**: Docker

## Configuration Structure

### Database Connections
- **Config File**: `config/database.yaml` - Defines connection names, settings, and default connection
- **Credentials**: `.env` - Stores sensitive connection credentials
- **Pattern**: Connection named `vosscloud` uses env vars `VOSSCLOUD_MYSQL_HOST`, `VOSSCLOUD_MYSQL_PORT`, etc.
- **Default**: Set in `config/database.yaml` under `default_connection`

### Environment Variables
- Follow naming pattern: `{CONNECTION_NAME}_MYSQL_{PARAMETER}`
- Example: `VOSSCLOUD_MYSQL_HOST=vosscloud`
- See `.env.example` for complete template

## Components Structure & Data Flow

### Agent System
1. **Manager Agent**: Orchestrates all operations, ensures site coverage
2. **Research Agent**: Analyzes new sites, documents structure
3. **Script Writer Agent**: Generates and fixes Python scrapers
4. **Debug Agent**: Diagnoses scraper failures
5. **Monitor Agent**: Watches daily execution
6. **Validation Agent**: Verifies data quality

### Data Flow
1. News sites added to `news_sites` table
2. Research Agent creates `site_structure_reports`
3. Script Writer creates `scraper_scripts` (stored as text)
4. Manager executes scripts → `scrape_runs` + `news_scrapes`
5. Debug/Script Writer heal failures → new script versions

## Folder Structure
```
indomonitor/
├── agents/              # Constitutional documents
├── config/              # Configuration files (YAML)
│   ├── database.yaml    # DB connection definitions
│   └── README.md        # Config documentation
├── scripts/             # Python scraper scripts
│   ├── .venv/           # Python 3.12 virtual environment
│   ├── requirements.txt # Python dependencies
│   └── *.py             # Executable scripts
├── tmp_agent/           # Temporary agent utility scripts
├── .env                 # Sensitive credentials (not in git)
├── .env.example         # Environment template
└── README.md            # Project documentation
```

## Key Design Decisions
- **Self-executable scripts**: Using uv's inline script metadata for dependency management
- **Database-stored scrapers**: Scripts stored as strings in DB for version control and agent modification
- **Multi-connection support**: Flexible database connection management via YAML config + .env credentials
- **Agent-driven maintenance**: Autonomous error detection and script healing
- **HTTP/2-3 ready**: Modern HTTP libraries (httpx, hypercorn) for performance

## Utility Scripts

### Database Management (`scripts/manage_db.py`)
Primary tool for all MySQL database operations. Self-executable with comprehensive features:

**Capabilities:**
- **Multi-server monitoring**: Checks ALL configured servers by default
- **Database inspection**: Lists databases, tables, and row counts
- **SQL execution**: Run any SQL query on any configured server
- **Status reporting**: Shows connection status for each server (connected/not reachable)
- **Triple output formats**: Human-readable text (default), structured JSON, or structured YAML

**Usage Examples:**
```bash
# Check all configured servers (default)
./scripts/manage_db.py

# Check specific server only
./scripts/manage_db.py --server production

# Execute SQL query on default server
./scripts/manage_db.py --sql "SHOW DATABASES"

# Execute SQL on specific server
./scripts/manage_db.py --server vosscloud --sql "SELECT * FROM users"

# Get JSON output for programmatic parsing
./scripts/manage_db.py --json
./scripts/manage_db.py --sql "SHOW TABLES" --json

# Get YAML output for human-readable structured data
./scripts/manage_db.py --yaml
./scripts/manage_db.py --sql "SHOW TABLES" --yaml
```

**Output Format:**
- Text: `server: {name}, db: {database}\n  {table}: {count}`
- Unreachable: `server: {name}, db: -, result: not reachable`
- JSON: Structured with `status`, `data`, `error` fields (machine-optimized)
- YAML: Structured with `status`, `data`, `error` fields (human-readable)

**AI Agent Usage:**
This script is designed for both human operators and AI agents. Agents should:
1. Use `--json` flag for programmatic parsing
2. Check all servers with no parameters to get infrastructure overview
3. Execute queries with `--sql` parameter for specific operations
4. Parse JSON response fields: `status`, `data.servers`, `data.rows`

### Status Check (`scripts/status_check.py`)
Legacy script for detailed MySQL server inspection. Provides verbose output about server version, databases, and tables. Consider using `manage_db.py` for most operations.

## Database Schema Management

### YAML-Based Schema Definition
The database schema is defined in **YAML files** as a single source of truth, located in `database/schema/`.

**Directory Structure:**
```
database/schema/
├── field_sets/          # Reusable field collections
│   ├── audit.yaml       # Standard created_at/updated_at timestamps
│   ├── agent_metadata.yaml    # AI agent execution tracking
│   └── scraper_metadata.yaml  # Scraper execution lifecycle
└── tables/              # Complete table definitions
    └── news_monitoring_tables.yaml  # All 6 core tables
```

**Benefits:**
- Single source of truth for SQL, Python Pydantic models, TypeScript interfaces
- Consistency across all generated code
- Type-safe definitions with enums and constraints
- Automatic naming convention translation (snake_case ↔ camelCase)
- Version control friendly (text-based)
- Generated code excluded from git (see `database/generated/`)

### Schema Files

**Field Sets (`database/schema/field_sets/`):**
- `audit.yaml` - Standard created_at/updated_at fields (used in all tables)
- `scraper_metadata.yaml` - Common scraper execution fields (started_at, completed_at, status)
- `agent_metadata.yaml` - AI agent execution metrics (token_usage, report, etc.)

**Database Schemas (`database/schema/tables/news_monitoring_tables.yaml`):**
1. `news_sites` - News website configurations
2. `site_structure_reports` - Research findings
3. `scraper_scripts` - Version-controlled Python code (stored as text)
4. `agent_runs` - Claude Code agent execution history
5. `scrape_runs` - Scraper execution results
6. `news_scrapes` - Scraped articles with content

### Schema Structure Example

```yaml
database_schemas:
  table_name:
    title: "Human Readable Name"
    python_class_name: "ClassName"
    typescript_class_name: "ClassName"
    db_table_name: "table_name"
    primary_key: "id"
    
    # Include reusable fields
    include_field_sets: ["audit_timestamps"]
    
    # Define table-specific fields
    fields:
      - name: "field_name"
        type: "string|integer|text|timestamp|json|uuid"
        sql_type: "VARCHAR(255)|INT|TEXT|TIMESTAMP|JSON|CHAR(36)"
        description: "Field purpose"
        required: true|false
        python_property_name: "field_name"    # snake_case
        typescript_property_name: "fieldName" # camelCase
```

### Modifying Schemas

1. **Edit YAML files** in `database/schema/` (either field sets or tables)
2. **Run generators** (when available) to create:
   - SQL schema → `database/generated/sql/schema.sql`
   - Python Pydantic models → `database/generated/python/models/`
   - TypeScript interfaces → `database/generated/typescript/types/`
   - API documentation
3. **Apply changes** to database using migration tools

**⚠️ Important:** Never edit files in `database/generated/` - they are auto-generated and excluded from git.

### Code Generation (Future)

```bash
# Generate all code from YAML schemas
./database/scripts/generate_all.sh

# Or generate specific outputs
./database/scripts/generate_sql.py       # → database/generated/sql/
./database/scripts/generate_python.py    # → database/generated/python/models/
./database/scripts/generate_typescript.py # → database/generated/typescript/types/
```

### Current SQL Schema
- **Authoritative source**: YAML files in `database/schema/`
- **Generated SQL**: `database/generated/sql/schema.sql` (auto-generated, not in git)
- **Future**: Code generators will auto-generate all code from YAML

See `database/schema/README.md` for complete documentation on YAML schema format and usage.
