# Task: Update Schema File with Explicit Foreign Key Constraint Names

**Main Tasks File**: [../TASKS.md](../TASKS.md)

---

## Metadata

- **Task ID**: P3.1
- **Priority**: 3-Planned
- **Status**: Pending
- **Labels**: database, schema, documentation, technical-debt
- **Added**: 2025-11-19
- **Last Updated**: 2025-11-19
- **Completion Date**: (not completed)

---

## Description

Update `database/generated/sql/schema.sql` to include explicit `CONSTRAINT` names for all foreign key definitions. Currently, the schema file defines foreign keys without explicit names, which would result in MySQL auto-generating names like `tablename_ibfk_N`. The actual database uses explicit, descriptive constraint names (e.g., `fk_scraper_scripts_site_id`), which is a best practice for maintainability and debugging.

---

## Current Behavior

The schema file defines foreign keys without explicit constraint names:

```sql
-- Example from current schema.sql
CREATE TABLE scraper_scripts (
    ...
    FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
);
```

**System currently:**
- ✅ Database has explicit constraint names (best practice)
- ❌ Schema file doesn't document these constraint names
- ⚠️ Running `/db-migrate` reports cosmetic discrepancies

**Actual database structure:**
```
CONSTRAINT fk_scraper_scripts_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
```

This mismatch means the schema file doesn't accurately represent what exists in production.

---

## Problem - Impact Analysis

**Severity**: LOW

**Impact Areas**:
- **Data Integrity**: No impact - foreign keys function identically
- **Financial Impact**: None
- **User Experience**: None
- **System Performance**: None
- **Security**: None
- **Scope**: Documentation and schema file accuracy only

**Business Impact**:
This is purely a documentation issue. The database is correctly structured with best-practice constraint naming, but the schema file doesn't reflect this. Fixing this ensures:
1. Schema file accurately documents production structure
2. Future schema recreations use consistent naming
3. Migration validation tools report clean compliance
4. Developers can reference correct constraint names in documentation

---

## File Locations

- **Schema Definition**: `database/generated/sql/schema.sql`
  - `scraper_scripts` table (lines ~30-45) - Add CONSTRAINT fk_scraper_scripts_site_id
  - `scrape_runs` table (lines ~50-70) - Add CONSTRAINT fk_scrape_runs_script_id and fk_scrape_runs_site_id
  - `site_structure_reports` table (lines ~75-90) - Add CONSTRAINT fk_site_structure_reports_site_id
  - `news_scrapes` table (lines ~95-115) - Add CONSTRAINT fk_news_scrapes_run_id and fk_news_scrapes_site_id
  - `agent_runs` table (lines ~120-140) - Add CONSTRAINT fk_agent_runs_site_id

- **Documentation**: `agents/ARCHITECTURE.md` or `agents/DOCUMENTATION.md`
  - Add note about foreign key constraint naming conventions

---

## Required Changes

### 1. Update scraper_scripts Table

**Location**: `database/generated/sql/schema.sql` (scraper_scripts table definition)

```sql
CREATE TABLE scraper_scripts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL,
    script_type ENUM('playwright', 'puppeteer', 'selenium', 'custom') NOT NULL,
    script_content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_tested TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_scraper_scripts_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Rationale**: Explicit naming makes debugging easier and documents intent clearly.

### 2. Update scrape_runs Table

**Location**: `database/generated/sql/schema.sql` (scrape_runs table definition)

```sql
CREATE TABLE scrape_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    script_id INT,
    site_id INT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    items_found INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_scrape_runs_script_id FOREIGN KEY (script_id) REFERENCES scraper_scripts(id) ON DELETE SET NULL,
    CONSTRAINT fk_scrape_runs_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Rationale**: Two foreign keys in this table need explicit names to distinguish them clearly.

### 3. Update site_structure_reports Table

**Location**: `database/generated/sql/schema.sql` (site_structure_reports table definition)

```sql
CREATE TABLE site_structure_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL,
    report_data JSON NOT NULL,
    structure_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_site_structure_reports_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Rationale**: Maintains naming consistency across all tables.

### 4. Update news_scrapes Table

**Location**: `database/generated/sql/schema.sql` (news_scrapes table definition)

```sql
CREATE TABLE news_scrapes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    site_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    url_hash VARCHAR(64) GENERATED ALWAYS AS (SHA2(url, 256)) STORED,
    published_date DATETIME,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_preview TEXT,
    UNIQUE KEY unique_url_hash (url_hash),
    FULLTEXT KEY idx_title_content (title, content_preview),
    CONSTRAINT fk_news_scrapes_run_id FOREIGN KEY (run_id) REFERENCES scrape_runs(id) ON DELETE CASCADE,
    CONSTRAINT fk_news_scrapes_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Rationale**: Two foreign keys require explicit naming for clarity.

### 5. Update agent_runs Table

**Location**: `database/generated/sql/schema.sql` (agent_runs table definition)

```sql
CREATE TABLE agent_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT,
    agent_type VARCHAR(50) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    result_data JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_runs_site_id FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Rationale**: Completes the pattern across all tables with foreign keys.

### 6. Add Documentation Comment

**Location**: `database/generated/sql/schema.sql` (top of file or before first table)

```sql
-- Foreign Key Naming Convention:
-- All foreign key constraints use explicit names following the pattern:
-- fk_{table_name}_{column_name}
-- This improves debugging, makes error messages clearer, and documents intent.
-- Example: fk_scraper_scripts_site_id
```

**Rationale**: Documents the naming convention for future schema modifications.

---

## Design Decisions

### Decision 1: Use Explicit Constraint Names Matching Production Database
- **What was decided**: Add explicit `CONSTRAINT constraint_name` clauses matching the exact names in production
- **Rationale**: Production database already uses well-named constraints; schema file should document this
- **Alternatives Considered**:
  - Removing explicit names from database (rejected - worse practice)
  - Using different naming convention (rejected - would require database migration)
- **Trade-offs**: Slightly more verbose schema file, but significantly better maintainability
- **References**: MySQL best practices, db-migration-validator report

### Decision 2: Document Naming Convention in Schema File
- **What was decided**: Add comment block explaining the naming pattern
- **Rationale**: Future developers should understand why explicit naming is used
- **Alternatives Considered**: Document only in ARCHITECTURE.md (rejected - should be in schema file itself)
- **Trade-offs**: None - only benefits
- **References**: Standard practice for schema documentation

---

## Edge Cases to Handle

- **Empty database recreation** - Expected behavior: ALLOW
  - Example: Running schema.sql on fresh database
  - Handling: Should create identical structure to production

- **Constraint name conflicts** - Expected behavior: ERROR
  - Example: Trying to create duplicate constraint name
  - Handling: MySQL will reject; schema file must have unique names

- **Migration validation** - Expected behavior: ALLOW
  - Example: Running `/db-migrate` after changes
  - Handling: Should report "✓ Database schema is up to date"

**Boundary Conditions**:
- Schema file must be valid SQL that executes without errors
- All constraint names must be unique within each table

**Error Conditions**:
- None expected - this is a documentation update only

**Concurrent Access**:
- Not applicable - schema file is static

---

## Testing Requirements

### Unit Tests
Not applicable - this is a schema documentation update, not code.

### Integration Tests
Not applicable - no application code changes.

### Manual Testing Checklist
- [ ] Read updated schema file to verify valid SQL syntax
- [ ] Run `/db-migrate` to verify schema compliance
- [ ] Verify report shows "✓ Database schema is up to date. No migration needed."
- [ ] Confirm all 6 constraint names are documented

### Regression Tests
- [ ] Verify existing database remains unchanged
- [ ] Confirm no unintended migrations triggered

---

## Success Criteria

All criteria must be met before marking task as complete:

- [ ] Schema file includes explicit CONSTRAINT clauses for all 6 foreign keys
- [ ] Constraint names exactly match production database
- [ ] All foreign key behaviors (ON DELETE CASCADE/SET NULL) maintained
- [ ] Documentation comment added explaining naming convention
- [ ] Schema file syntax is valid (can be executed without errors)
- [ ] Running `/db-migrate` reports "✓ Database schema is up to date. No migration needed."
- [ ] ARCHITECTURE.md or DOCUMENTATION.md updated with constraint naming standards
- [ ] User verification completed successfully

---

## Sub-tasks

Track implementation progress with detailed markdown checkboxes. Mark complete IMMEDIATELY after finishing each step.

**Planning Phase:**
- [ ] Read `agents/DOCUMENTATION.md` for MySQL foreign key documentation references
- [ ] Review current `database/generated/sql/schema.sql` structure
- [ ] Verify exact constraint names from db-migration-validator report

**Implementation Phase:**
- [ ] Update scraper_scripts table with CONSTRAINT fk_scraper_scripts_site_id
- [ ] Update scrape_runs table with CONSTRAINT fk_scrape_runs_script_id
- [ ] Update scrape_runs table with CONSTRAINT fk_scrape_runs_site_id
- [ ] Update site_structure_reports table with CONSTRAINT fk_site_structure_reports_site_id
- [ ] Update news_scrapes table with CONSTRAINT fk_news_scrapes_run_id
- [ ] Update news_scrapes table with CONSTRAINT fk_news_scrapes_site_id
- [ ] Update agent_runs table with CONSTRAINT fk_agent_runs_site_id
- [ ] Add documentation comment explaining naming convention

**Testing Phase:**
- [ ] Verify SQL syntax is valid (visual inspection)
- [ ] Run `/db-migrate` to validate schema compliance
- [ ] Verify clean validation report (no discrepancies)
- [ ] Confirm all constraint names match production

**Documentation & Completion:**
- [ ] Update ARCHITECTURE.md or DOCUMENTATION.md with constraint naming standards
- [ ] User verification - confirm schema file accurately documents database
- [ ] Update HISTORY.md when task completed (via TASKS.md completion process)

---

## Dependencies

### Blocking Dependencies
None - this task can be started immediately.

### Blocked Tasks
None - no other tasks waiting on this.

### External Dependencies
None - only requires text editor to modify schema file.

### Related Tasks
- Database migration validation system (already complete)
- Schema file maintenance practices (ongoing)

---

## Notes

**Historical Context**:
- Database was created with explicit foreign key constraint names (best practice)
- Schema file was written without documenting these names
- Migration validation tool detected this discrepancy during `/db-migrate` run on 2025-11-19

**Implementation Considerations**:
- This is purely a documentation update - no database changes needed
- All 6 constraint names already confirmed by db-migration-validator
- Schema file must remain executable SQL (syntax validation critical)

**Future Enhancements**:
- Consider adding schema generation script that enforces naming conventions
- Automate schema file updates from database structure

**Open Questions**:
None - all constraint names confirmed by validation report.

---

## References

### Related Documentation
- Schema File: `database/generated/sql/schema.sql`
- Database Tool: `scripts/manage_db.py`
- Migration Command: `/db-migrate` in `.claude/commands/db-migrate.md`

### Related Tasks
- `/db-migrate` command implementation (completed)
- db-migration-validator agent (completed)

### External Resources
- MySQL CONSTRAINT documentation: https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html
- MySQL naming best practices

### Code References
- Current schema file structure: `database/generated/sql/schema.sql`
- Database validation: db-migration-validator report from 2025-11-19

---

## Update Log

- **2025-11-19**: Claude - Task created based on `/db-migrate` validation findings
