# Database Directory

This directory contains all database-related files for the news monitoring system.

## Structure

### `schema/` (YAML Schema Definitions - Source of Truth)
**Single source of truth** for database schema definitions in YAML format.

```
schema/
├── field_sets/          # Reusable field collections
│   ├── audit.yaml       # Standard created_at/updated_at timestamps
│   ├── agent_metadata.yaml    # AI agent execution tracking
│   └── scraper_metadata.yaml  # Scraper execution lifecycle
├── tables/              # Complete table definitions
│   └── news_monitoring_tables.yaml  # All 6 core tables
└── README.md            # Schema format documentation
```

**Benefits:**
- Generate SQL, Python Pydantic models, TypeScript interfaces from one source
- Consistency across all code and documentation
- Type-safe definitions with enums and constraints
- Version control friendly

**See:** `schema/README.md` for detailed YAML format documentation

### `generated/` (Auto-Generated Code - DO NOT EDIT)
Code automatically generated from YAML schema definitions.

```
generated/
├── sql/                 # Generated SQL schema files
│   └── schema.sql       # Complete MySQL schema
├── python/models/       # Generated Pydantic models (future)
├── typescript/types/    # Generated TypeScript interfaces (future)
└── README.md            # Warning about auto-generated files
```

**⚠️ WARNING:** Files in this directory are automatically generated. DO NOT EDIT manually.

**Usage:**
```bash
# Create database and load schema
./scripts/manage_db.py --sql "CREATE DATABASE IF NOT EXISTS indomonitor"
./scripts/manage_db.py --sql "USE indomonitor; SOURCE database/generated/sql/schema.sql"

# Or using mysql client directly
mysql -h vosscloud -u indomonitor -p indomonitor < database/generated/sql/schema.sql
```

**Note:** These files are NOT committed to git (see .gitignore)

### `scripts/` (Code Generation - Future)
Scripts for generating code from YAML schemas.

```
scripts/
├── generate_sql.py         # Generate SQL schema from YAML
├── generate_python.py      # Generate Pydantic models
├── generate_typescript.py  # Generate TypeScript interfaces
└── generate_all.sh         # Run all generators
```

**Usage (when implemented):**
```bash
# Generate all code from YAML schemas
./database/scripts/generate_all.sh

# Or generate specific outputs
./database/scripts/generate_sql.py
./database/scripts/generate_python.py
```

### `migrations/`
Database migration files for incremental schema changes.

**Naming convention:** `YYYYMMDD_HHMMSS_description.sql`
- Example: `20251119_120000_add_news_sites_table.sql`

**Usage:**
```bash
# Apply migration
./scripts/manage_db.py --sql "$(cat database/migrations/20251119_120000_add_news_sites_table.sql)"
```

## Schema Design

The database schema follows the architecture defined in README.md:

### Core Tables
- `news_sites` - News website configurations
- `site_structure_reports` - Research findings for each site
- `scraper_scripts` - Version-controlled scraper code
- `agent_runs` - Agent execution history
- `scrape_runs` - Scraper execution history
- `news_scrapes` - Scraped article data

See `schemas/schema.sql` for complete definitions.
