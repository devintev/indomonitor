# Indomonitor Operator Script

The `operator` script is a headless Claude Code automation tool for database monitoring and status checks.

## Quick Start

```bash
# Run standard operator workflow
./operator

# Run with a custom task
./operator "Check for empty tables"

# Use a different model
./operator --model sonnet-4-5

# Get JSON output for programmatic processing
./operator --format json

# Run without logging
./operator --no-log
```

## Features

- **Automated database monitoring** - Checks database connectivity and status
- **News sites verification** - Queries and reports on configured news sites
- **Flexible model selection** - Choose between haiku-4-5 (fast), sonnet-4-5 (balanced), or opus-4-1 (powerful)
- **Multiple output formats** - text, json, or markdown
- **Automatic logging** - Saves execution logs with timestamps
- **Custom tasks** - Add additional tasks to the workflow

## Command-Line Options

```
Usage: ./operator [OPTIONS] [CUSTOM_TASK]

Options:
  -h, --help          Show help message
  -m, --model MODEL   Specify Claude model (default: haiku-4-5)
                      Options: haiku-4-5, sonnet-4-5, opus-4-1
  -f, --format FORMAT Output format (default: text)
                      Options: text, json, markdown
  -t, --task TASK     Add a custom task to the operator workflow
  --no-log            Disable logging to file
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY='your-api-key-here'

# Optional configuration
export CLAUDE_OPERATOR_MODEL='haiku-4-5'     # Default model
export CLAUDE_OPERATOR_FORMAT='text'         # Default output format
export CLAUDE_OPERATOR_LOG='true'            # Enable/disable logging
```

## Examples

### Basic Usage

```bash
# Standard check with default settings (haiku-4-5 model, text output, logging enabled)
./operator
```

### Custom Tasks

```bash
# Check for specific issues
./operator "Find all tables with more than 10,000 rows"

# Using -t flag for clarity
./operator -t "Check last update time for all news sites"
```

### Different Models

```bash
# Fast and cost-effective (recommended for routine checks)
./operator --model haiku-4-5

# Balanced performance (for more complex analysis)
./operator --model sonnet-4-5

# Most capable (for difficult troubleshooting)
./operator --model opus-4-1
```

### Output Formats

```bash
# Human-readable text (default)
./operator --format text

# JSON for programmatic processing
./operator --format json > status.json

# Markdown for documentation
./operator --format markdown > STATUS_REPORT.md
```

### Automation & Scheduling

```bash
# Run hourly via cron (add to crontab with: crontab -e)
0 * * * * cd /Users/voss/code/indomonitor && ./operator --no-log >> /var/log/indomonitor.log 2>&1

# Run on demand with custom checks
./operator "Verify all news sites are active and report any with status != 'active'"
```

## What It Does

The operator script executes a workflow defined in `agents/commands/operator.md`:

1. **Database Overview** - Runs `./scripts/manage_db.py` to check connectivity and list all databases/tables
2. **Schema Validation** - Uses the `db-migration-validator` subagent to verify schema compliance
3. **News Sites Check** - Queries the `news_sites` table to verify configured news sources (if table exists)
4. **Summary Report** - Provides concise summary with database status, schema status, news sites count, and recommended actions

The operator uses subagents (via the Task tool) for schema validation and can invoke the `db-migration-executor` if needed.

## Logs

Logs are saved to `logs/operator_YYYYMMDD_HHMMSS.log` with timestamps.

```bash
# View recent logs
ls -lt logs/ | head -10

# View latest log
cat logs/operator_*.log | tail -1

# Disable logging for a run
./operator --no-log
```

## Customization

To modify the operator workflow, edit `agents/commands/operator.md`. The script automatically reads this file and uses it as the prompt.

## Troubleshooting

### API Key Not Set
```
Error: ANTHROPIC_API_KEY environment variable is not set
```
**Solution:** Set your API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Prompt File Not Found
```
Error: Prompt file not found at agents/commands/operator.md
```
**Solution:** Ensure you're running the script from the project root directory.

### Database Connection Issues
Check the database configuration in `config/database.yaml` and verify MySQL is running.

## Integration with Other Tools

### Use with watch for continuous monitoring
```bash
# Check every 5 minutes
watch -n 300 './operator --no-log'
```

### Combine with jq for JSON processing
```bash
# Extract specific data from JSON output
./operator --format json | jq '.databases[] | select(.table_count > 0)'
```

### Alert on issues
```bash
#!/bin/bash
OUTPUT=$(./operator --format text)
if echo "$OUTPUT" | grep -i "error\|warning\|failed"; then
    echo "$OUTPUT" | mail -s "Indomonitor Alert" admin@example.com
fi
```

## Related Documentation

- `agents/commands/operator.md` - Operator workflow definition
- `scripts/manage_db.py` - Database management script
- `config/database.yaml` - Database connection configuration
- `CLAUDE.md` - Project-wide Claude Code instructions
