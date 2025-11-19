# Framework Documentation References & Development Guidelines
Each entry in the library list needs to have a Framework / Library name, a version of which this library is used, a url reference to documentation (html pages or llm.txt or llm-full.txt) and where possible the context7CompatibleLibraryID.

## Framework and Library References
- [Framework/Library Name]: Version: x.x.x, context7CompatibleLibraryID: `/websites/example_url/docu_id`, Website: https://example.com/docs, LLM.txt: https://example.com/llm.txt,
- [Library Name]: Version: x.x.x, context7CompatibleLibraryID: `/websites/example_url/docu_id`, Notes: [key usage notes]
- [Add additional frameworks and libraries as needed]

## Pitfalls and Issues to Avoid
This section is updated with warnings and lessons learned during the development process.
- Issue: [Description] | Solution: [How to avoid/fix] | Date: YYYY-MM-DD
- Issue: [Description] | Solution: [How to avoid/fix] | Date: YYYY-MM-DD
- [Add new pitfalls as discovered during development]

## Core Libraries

### Python Standard Library
- Version: 3.12+
- Website: https://docs.python.org/3.12/
- Notes: Using latest Python 3.12 features

### PyMySQL
- Version: Latest
- Website: https://pymysql.readthedocs.io/
- Usage: MySQL database connectivity (pure Python implementation)
- Notes: Used in `manage_db.py` and `status_check.py` for MySQL operations

### PyYAML
- Version: Latest
- Website: https://pyyaml.org/wiki/PyYAMLDocumentation
- Usage: Configuration file parsing (`config/database.yaml`)
- Notes: Safe loading with `yaml.safe_load()`

### python-dotenv
- Version: Latest
- Website: https://github.com/theskumar/python-dotenv
- Usage: Environment variable management from `.env` files
- Notes: Keep credentials in `.env`, never commit to git

### httpx
- Version: Latest (with HTTP/2 support)
- Website: https://www.python-httpx.org/
- context7CompatibleLibraryID: `/encode/httpx`
- Usage: HTTP client for web scraping (preferred over requests)
- Notes: Supports HTTP/2 and HTTP/3, async operations

### BeautifulSoup4
- Version: Latest
- Website: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Usage: HTML parsing and content extraction
- Notes: Primary tool for simple HTML parsing

### Scrapy
- Version: Latest
- Website: https://docs.scrapy.org/
- context7CompatibleLibraryID: `/scrapy/scrapy`
- Usage: Advanced web scraping framework
- Notes: For complex multi-page scraping workflows

### Playwright
- Version: Latest
- Website: https://playwright.dev/python/
- context7CompatibleLibraryID: `/microsoft/playwright-python`
- Usage: Browser automation for JavaScript-heavy sites
- Notes: Headless browser control, handles dynamic content

## Utility Scripts

### manage_db.py
**Purpose**: Primary database management tool for MySQL operations

**Features**:
- Multi-server health checking (checks ALL configured servers by default)
- Database and table inspection with row counts
- SQL query execution on any configured server
- Triple output formats: human-readable text (default), structured JSON, or structured YAML
- Connection status reporting (connected/not reachable/error)

**Key Functions**:
- `get_all_servers_overview()`: Check all configured servers
- `get_database_overview(connection, server_name)`: Get single server overview
- `execute_sql(connection, sql)`: Execute any SQL query
- `output_json(status, data, error)`: Structured JSON output

**Common Patterns**:
```python
# Check all servers programmatically
import subprocess
import json

result = subprocess.run(
    ['./scripts/manage_db.py', '--json'],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)

for server in data['data']['servers']:
    if server['status'] == 'connected':
        print(f"{server['server']}: {len(server['user_databases'])} databases")
    else:
        print(f"{server['server']}: {server['status']}")
```

**For AI Agents**:
- Always use `--json` flag for programmatic parsing
- Check response `status` field before accessing `data`
- Handle both `connected` and `not reachable` server states
- Use for database discovery, health checks, and SQL operations

### indomonitor.py
**Purpose**: CLI tool for managing news sites in the monitoring system

**Features**:
- Add new news sites to monitor
- List all news site URLs
- Automatic URL validation (must be http/https)
- Duplicate detection (checks existing URLs)
- Domain-based name extraction
- Auto-increment ID assignment (follows schema: INT AUTO_INCREMENT, not UUID)

**Key Functions**:
- `validate_url(url)`: Validates URL format, returns (is_valid, domain)
- `extract_site_name(url)`: Extracts human-readable name from domain
- `check_site_exists(connection, url)`: Checks for duplicate URLs
- `add_site(connection, url, name, status)`: Inserts new site into database

**Database Integration**:
- Reuses `manage_db.py` functions for database connectivity
- Inserts into `indomonitor.news_sites` table
- Sets minimal required fields: `url`, `name`, `status`, `updated_at`
- Default status: 'pending'

**Common Patterns**:
```bash
# Add a new news site
./scripts/indomonitor.py add site https://www.reuters.com

# List all news sites (outputs URLs, one per line)
./scripts/indomonitor.py list news_sites

# Check help
./scripts/indomonitor.py -h
./scripts/indomonitor.py add site -h

# Add with automatic name extraction
./scripts/indomonitor.py add site https://news.ycombinator.com
# Creates: ID=2, Name="News Ycombinator", Status="pending"
```

**Programmatic Usage**:
```python
import subprocess
import sys

# Add site programmatically
result = subprocess.run(
    ['./scripts/indomonitor.py', 'add', 'site', 'https://example.com'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(f"Success: {result.stdout}")
else:
    print(f"Error: {result.stderr}", file=sys.stderr)
```

**For AI Agents**:
- Use for adding new sites to the monitoring pipeline
- Always validate URL format before passing to script
- Script handles duplicates gracefully (reports existing entry, exits 0)
- Invalid URLs exit with code 1
- Site name extraction: "www.reuters.com" → "Reuters", "news.ycombinator.com" → "News Ycombinator"
- After adding site, status will be 'pending' until Manager Agent processes it
