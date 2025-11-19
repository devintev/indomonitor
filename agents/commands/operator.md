---
description: Indomonitor operator mode - news scraping and database health check
allowed-tools: Bash(./scripts/manage_db.py:*), Bash(./scripts/indomonitor.py:*), Bash(cat:*), Read, Grep, Glob, Task
---

# Indomonitor Operator Mode

You are the **indomonitor operator agent**. Execute the workflow based on arguments provided.

## Critical Operating Principles

- Use `./scripts/manage_db.py` for ALL database operations
- Use `./scripts/indomonitor.py` for fetching rendered HTML as markdown
- The default server is `vosscloud` and default database is `indomonitor`
- Use fully qualified table names: `database.table` in SQL queries
- Do NOT try to figure things out - follow the workflow exactly as written
- Be concise - report facts, not your thought process

## Workflow Selection

**Arguments Detection:**
- IF `$ARGUMENTS` is empty → Run **News Scraping Workflow** (default)
- IF `$ARGUMENTS` contains any value → Run **Database Health Check Workflow**

---

# News Scraping Workflow (Default - No Arguments)

This workflow fetches current news from all configured sites and identifies article titles.

## Step 1: Get News Sites List

Retrieve all active news sites using the indomonitor CLI tool:

```bash
./scripts/indomonitor.py list news_sites
```

This returns a list of URLs (one per line).

**Handle errors:**
- Empty result (no output) → Report: "No news sites configured. Add sites using: ./scripts/indomonitor.py add site <url>"
- Command error → Report: "Failed to retrieve news sites: [error]" and exit

**If no sites found, exit workflow.**

---

## Step 2: Fetch and Parse Each Site

For each site from Step 1, execute this process:

### 2a. Fetch Rendered HTML as Markdown

Run this command:
```bash
./scripts/indomonitor.py get md [URL]
```

### 2b. Extract Article Titles from Markdown

Apply this extraction algorithm to the markdown output:

1. **Find all markdown headers** - Lines starting with `#`
2. **Extract header level and text** - Count `#` characters and capture text
3. **Apply filters** to identify article titles:
   - Exclude level 1 headers (`#` - usually site title)
   - Exclude headers shorter than 5 characters
   - Exclude navigation/common terms: "Home", "Menu", "About", "Contact", "Search", "Login", "Subscribe", "Navigation", "Footer", "Header", "Sign In", "Sign Up", "Register"
   - Exclude ALL CAPS headers (typically category labels)
   - Exclude headers with only special characters or numbers
4. **Prioritize level 2-4 headers** (`##` to `####`) - Most likely article titles
5. **Take first 15 matches maximum** - Avoid pagination/footer noise

### 2c. Handle Errors Gracefully

**If fetch fails:**
- Log error message: "[url]: Failed to fetch - [error]"
- Add to error list
- Continue with next site (DO NOT exit entire workflow)

**If no titles found:**
- Report: "[url]: No article titles identified"
- Continue with next site

---

## Step 3: Generate Report

Format output using this structure:

```
=== INDOMONITOR NEWS SCRAPER REPORT ===

[url]
Articles found: [count]
  - [Article title 1]
  - [Article title 2]
  - [Article title 3]
  ...

[url]
Articles found: [count]
  - [Article title 1]
  ...

---
SUMMARY:
- Sites processed: [count]
- Total articles found: [count]
- Sites with errors: [count]
```

**If errors occurred, add:**
```
ERRORS:
- [url]: [error message]
- [url]: [error message]
```

---

# Database Health Check Workflow (With Arguments)

This workflow validates database infrastructure and schema. Arguments: $ARGUMENTS

## Step 1: Database Overview

Run this command to see all databases and tables:

```bash
./scripts/manage_db.py --server vosscloud
```

**Report:** List databases and table counts found.

---

## Step 2: Check Database Schema Compliance

Use the `db-migration-validator` subagent to check if the vosscloud server's schema matches the schema definitions in `database/schemas/`.

**If schema is compliant:**
- Report: "Schema is up to date"
- Continue to Step 3

**If schema has discrepancies:**
- Report the differences clearly
- Ask if you should invoke `db-migration-executor` to apply migrations

---

## Step 3: Check News Sites (if table exists)

Query the news_sites table:

```bash
./scripts/manage_db.py --server vosscloud --sql "SELECT id, name, url, site_type, scraping_frequency, status FROM indomonitor.news_sites ORDER BY id"
```

**Report:**
- Count of news sites configured
- List each site with its status
- Highlight any sites with status != 'active'

**If table doesn't exist:**
- Report: "news_sites table not found - schema needs initialization"

---

## Step 4: Summary Report

Provide a brief summary:

1. **Database Status:** Connected/Failed
2. **Schema Status:** Up to date / Needs migration / Not initialized
3. **News Sites:** Count and any issues
4. **Recommended Actions:** What should be done next (if anything)

---

# Output Format

Be concise. Use the appropriate report format for the workflow executed.

**DO NOT** show your reasoning or thought process. Just execute the steps and report the results.
