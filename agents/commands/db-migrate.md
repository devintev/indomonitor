---
description: Validate database schema and auto-execute migrations if needed
allowed-tools: Task, Read, Bash(./scripts/manage_db.py:*)
argument-hint: [server-name] [database-name]
---

# Database Schema Validation and Migration

You are executing an **automated database migration workflow**. Follow this process precisely:

## Parameters

- **Server**: $1 (defaults to `vosscloud` if not provided)
- **Database**: $2 (defaults to `indomonitor` if not provided)

## Workflow

### Step 1: Validate Schema Compliance

Use the `db-migration-validator` subagent to check if the database schema matches the schema definitions in `database/generated/sql/schema.sql`.

**Task for validator:**
- Target server: $1 (or vosscloud if not specified)
- Target database: $2 (or indomonitor if not specified)
- Check all tables, columns, indexes, constraints, and foreign keys
- Report any discrepancies found

### Step 2: Analyze Validation Results

**If schema is compliant:**
- Report: "✓ Database schema is up to date. No migration needed."
- STOP HERE - do not proceed to Step 3

**If schema has discrepancies:**
- Extract the migration SQL statements from the validator's report
- Proceed to Step 3

### Step 3: Execute Migration (Only if Step 2 found discrepancies)

Use the `db-migration-executor` subagent to apply the migration changes.

**Task for executor:**
- Execute the migration SQL statements identified by the validator
- Target the same server and database from Step 1
- Verify each change after execution
- Report completion status

### Step 4: Final Report

Provide a brief summary:

```
=== DATABASE MIGRATION REPORT ===

Server: [server-name]
Database: [database-name]

Validation: [✓ Compliant | ⚠ Discrepancies Found]
Migration: [Not needed | ✓ Completed | ❌ Failed]

[Any relevant details or errors]
```

## Important Notes

- **Be concise** - This is an automated workflow, not an exploratory task
- **Execute automatically** - Don't ask for user permission between steps
- **Sequential execution** - Complete Step 1 before Step 2, Step 2 before Step 3
- **Error handling** - If validation or migration fails, report the error and stop
- **No assumptions** - Use the exact server/database names provided (or defaults)

## Usage Examples

```
/db-migrate                      # Uses defaults: vosscloud, indomonitor
/db-migrate production           # Uses: production server, indomonitor database
/db-migrate vosscloud testdb     # Uses: vosscloud server, testdb database
```
