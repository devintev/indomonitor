# System Architecture

## Overview
Automated news monitoring system with autonomous Claude Code agents that scrape news websites, extract content, and store it in a database. The system is self-healing and self-maintaining through a multi-agent orchestration pattern.

## Critical Implementation Reminders
- **Python Dependency Management**: Always use `uv` (never pip or virtualenv)
- **Self-Executable Scripts**: All Python scripts in `scripts/` must start with `#!/usr/bin/env -S uv run --quiet --script` and be made executable (`chmod +x`)
- **HTTP Library Preference**: Use `httpx` (not `requests`) and `hypercorn` (not `uvicorn`) for HTTP/2 and HTTP/3 support
- **Script Organization**: Individual scraper scripts stored as strings in database, executed by manager agent

## Frameworks and Libraries
- **Python**: 3.12+
- **Dependency Management**: uv
- **Web Scraping**: BeautifulSoup4, Scrapy, Playwright
- **HTTP Client**: httpx (HTTP/2, HTTP/3 support)
- **Server**: hypercorn (HTTP/2, HTTP/3 support)
- **Database**: PostgreSQL
- **Scheduling**: APScheduler or Celery
- **Agent Platform**: Claude Code (headless mode)
- **Environment**: Docker

## Components Structure & Data Flow
Systematic overview of relationships of the components and how data is flowing between them.

## Folder Structure and Files
file tree

## Components
### Component 1
Description and responsibilities.

### Component 2
Description and responsibilities.

## Key Design Decisions
- Decision 1: Rationale
- Decision 2: Rationale
