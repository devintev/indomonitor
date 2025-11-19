# News Monitoring Application

## Overview

Automated system that monitors news websites, extracts content, and stores it in a database. Python scripts orchestrated by Claude Code agents (headless) for autonomous operation and self-maintenance.

## Architecture

### 1. Data Collection

- Python scrapers for news websites
- Configurable monitoring schedules
- Content extraction (articles, metadata, timestamps)
- Deduplication logic

### 2. Agent System (Claude Code Headless)

- **Manager Agent (Main)**: Orchestrates all agents, ensures every news site has a functioning scrape workflow
- **Research Agent**: Investigates new sites (news listing structure, HTML extraction patterns)
- **Script Writer Agent**: Builds, tests, and fixes Python scraper scripts
- **Debug Agent**: Identifies problems when scripts fail (page structure changes, alternating DOM)
- **Monitor Agent**: Watches daily routine execution
- **Validation Agent**: Verifies data quality

### 3. Database

- **news_sites**: URL, name, config, status
- **site_structure_reports**: Research findings for each site
- **scraper_scripts**: All script versions stored as strings
- **scrape_runs**: Execution history (started, completed, status, articles_found, errors)
- **news_scrapes**: Scraped articles (URL, title, content, timestamps)

### 4. Monitoring

- Health checks and error detection
- Self-healing via Claude Code agents
- Alerts for critical failures

## Tech Stack

- Python 3.11+
- Scraping: BeautifulSoup4, Scrapy, or Playwright
- Database: MySQL
- Agent Platform: Claude Code (headless)
- Scheduling: APScheduler/Celery
- Environment: Docker

## Management Tools

### indomonitor.py
Command-line interface for managing the news monitoring system.

**Add News Sites:**
```bash
# Add a new site to monitor
./scripts/indomonitor.py add site https://example.com

# The script will:
# - Validate the URL format
# - Check for duplicates
# - Extract site name from domain
# - Insert into database with 'pending' status
```

**Features:**
- Automatic duplicate detection
- URL validation (must be http/https)
- Domain-based name extraction
- Uses auto-increment IDs (follows schema)

**Usage:**
```bash
# Show help
./scripts/indomonitor.py -h
./scripts/indomonitor.py add site -h

# Add a news site
./scripts/indomonitor.py add site https://www.reuters.com
# Output: Successfully added new site (ID: 1, Name: Reuters)

# Try to add duplicate
./scripts/indomonitor.py add site https://www.reuters.com
# Output: Site already exists (ID: 1)

# List all news sites (outputs URLs, one per line)
./scripts/indomonitor.py list news_sites
# Output:
# https://www.reuters.com
# https://news.ycombinator.com
```

### manage_db.py
Primary database management tool for MySQL operations.

**Database Inspection:**
```bash
# Check all configured servers
./scripts/manage_db.py

# Check specific server
./scripts/manage_db.py --server vosscloud

# Execute SQL query
./scripts/manage_db.py --sql "SELECT * FROM indomonitor.news_sites"

# JSON output for programmatic use
./scripts/manage_db.py --json
./scripts/manage_db.py --sql "SHOW DATABASES" --json
```

**Features:**
- Multi-server health checking
- Database and table inspection with row counts
- SQL query execution
- Multiple output formats (text, JSON, YAML)

## Workflow

### New Site Onboarding

1. Add new site using CLI tool:
   ```bash
   ./scripts/indomonitor.py add site https://example.com/news
   ```
2. Manager calls Research Agent to investigate site
3. Research Agent creates site structure report → stored in DB
4. Manager calls Script Writer Agent
5. Script Writer builds/tests/fixes Python scraper → script stored as string in DB
6. Once working, Manager enqueues script to daily routine

### Daily Operations

1. Manager runs daily routine for all active sites
2. Execute scrapers → store results in scrape_runs + news_scrapes
3. Manager checks for errors in scrape_runs
4. If errors detected:
   - Manager calls Debug Agent to identify problem
   - Debug Agent creates assessment report
   - Manager sends assessment + instructions to Script Writer Agent
   - Script Writer updates script → new version stored in DB
5. Validation Agent verifies data quality

## Configuration Example

```python
{
  "source_id": "news_site_1",
  "url": "https://example.com/news",
  "schedule": "*/15 * * * *",
  "selectors": {
    "article_links": "div.article-list a",
    "title": "h1.article-title",
    "content": "div.article-body"
  }
}
```

## Data Schema

```sql
CREATE TABLE news_sites (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    name VARCHAR(255),
    config JSONB,
    status VARCHAR(50),
    script_health_status VARCHAR(50), -- missing, failed, healed, success
    main_script_id INTEGER REFERENCES scraper_scripts(id),
    secondary_script_id INTEGER REFERENCES scraper_scripts(id),
    tertiary_script_id INTEGER REFERENCES scraper_scripts(id),
    script_notes TEXT,
    created_at TIMESTAMP
);

CREATE TABLE site_structure_reports (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES news_sites(id),
    report_text TEXT,
    created_at TIMESTAMP
);

CREATE TABLE scraper_scripts (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES news_sites(id),
    version INTEGER,
    script_code TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(100),
    site_id INTEGER REFERENCES news_sites(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    token_usage INTEGER,
    report TEXT,
    status VARCHAR(50)
);

CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY,
    site_id INTEGER REFERENCES news_sites(id),
    script_id INTEGER REFERENCES scraper_scripts(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50),
    articles_found INTEGER,
    errors TEXT
);

CREATE TABLE news_scrapes (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES scrape_runs(id),
    site_id INTEGER REFERENCES news_sites(id),
    url TEXT UNIQUE,
    title TEXT,
    content TEXT,
    published_at TIMESTAMP,
    scraped_at TIMESTAMP
);
```

## Key Metrics

- Scraping success rate
- Articles processed/hour
- Agent intervention frequency
- Error rates
