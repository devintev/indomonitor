# Configuration Directory

This directory contains configuration files for the news monitoring system.

## Files

### database.yaml
Defines available database connections (MySQL and PostgreSQL).

**Key Features:**
- Multiple named MySQL connections (vosscloud, production, staging, local)
- Default connection selection
- Connection-specific settings (timeouts, charset, SSL)
- PostgreSQL configuration for news data storage

**Usage:**
- Connection names here must match the `env_prefix` in `.env` file
- Example: `vosscloud` connection uses `VOSSCLOUD_MYSQL_*` environment variables
- Default connection is used when no specific connection is requested

## Configuration Pattern

```yaml
mysql_connections:
  {connection_name}:
    env_prefix: "{CONNECTION_NAME}_MYSQL"
    # ... settings
```

Corresponding `.env`:
```bash
{CONNECTION_NAME}_MYSQL_HOST=hostname
{CONNECTION_NAME}_MYSQL_PORT=3306
{CONNECTION_NAME}_MYSQL_USER=username
{CONNECTION_NAME}_MYSQL_PASSWORD=password
```

## Adding New Connections

1. Add connection entry to `database.yaml`
2. Add corresponding credentials to `.env` (use `.env.example` as template)
3. Optionally update `default_connection` if needed
