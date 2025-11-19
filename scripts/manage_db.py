#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
# ]
# ///
"""
Database Management Script

A versatile MySQL database management tool for both human operators and AI agents.

Usage:
  # Check ALL configured servers (default behavior)
  ./scripts/manage_db.py
  
  # Check specific server only
  ./scripts/manage_db.py --server vosscloud
  
  # Execute SQL query on default server
  ./scripts/manage_db.py --sql "SHOW DATABASES"

  # Execute SQL query on specific server
  ./scripts/manage_db.py --server production --sql "SELECT * FROM users LIMIT 5"

  # Auto-select a database (allows unqualified table names)
  ./scripts/manage_db.py --database indomonitor --sql "SHOW CREATE TABLE scraper_scripts"
  ./scripts/manage_db.py --server vosscloud --database indomonitor --sql "DESCRIBE users"
  
  # Get output in JSON format
  ./scripts/manage_db.py --json
  ./scripts/manage_db.py --sql "SHOW DATABASES" --json

  # Get output in YAML format
  ./scripts/manage_db.py --yaml
  ./scripts/manage_db.py --sql "SHOW DATABASES" --yaml

Outputs:
  - Text format: Human-readable output (default)
  - JSON format: Structured data with status, data, and error fields
  - YAML format: Human-readable structured data (alternative to JSON)

When no --server and no --sql is specified, the script checks ALL configured servers
and reports their status, databases, tables, and row counts.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import pymysql
import yaml
from typing import Dict, List, Optional, Any, Tuple


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        return
    load_dotenv(env_path)


def load_database_config() -> Dict:
    """Load database configuration from config/database.yaml."""
    config_path = Path(__file__).parent.parent / 'config' / 'database.yaml'
    if not config_path.exists():
        error_exit(f"Configuration file not found at {config_path}", json_output=False)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_all_connection_names() -> List[str]:
    """Get list of all configured MySQL connection names."""
    db_config = load_database_config()
    connections = db_config.get('mysql_connections', {})
    return list(connections.keys())


def is_config_complete(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if all required configuration values are non-empty.
    
    Returns:
        Tuple of (is_complete, missing_vars)
    """
    required_fields = ['host', 'port', 'user', 'password']
    missing = []
    
    for field in required_fields:
        value = config.get(field)
        # Check if value is None, empty string, or 0 (but 0 port is invalid anyway)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            missing.append(field)
    
    return len(missing) == 0, missing


def get_connection_config(connection_name: str) -> Dict[str, Any]:
    """Get MySQL connection configuration for specified connection."""
    db_config = load_database_config()
    
    # Get connection settings
    connections = db_config.get('mysql_connections', {})
    if connection_name not in connections:
        available = ', '.join(connections.keys())
        error_exit(
            f"Connection '{connection_name}' not found. Available: {available}",
            json_output=False
        )
    
    conn_settings = connections[connection_name]
    env_prefix = conn_settings['env_prefix']
    
    # Build config from environment variables
    config = {
        'name': connection_name,
        'host': os.getenv(f'{env_prefix}_HOST', ''),
        'port': int(os.getenv(f'{env_prefix}_PORT', '3306')) if os.getenv(f'{env_prefix}_PORT', '').strip() else 0,
        'user': os.getenv(f'{env_prefix}_USER', ''),
        'password': os.getenv(f'{env_prefix}_PASSWORD', ''),
        'connection_timeout': conn_settings.get('connection_timeout', 5),
        'read_timeout': conn_settings.get('read_timeout', 30),
        'write_timeout': conn_settings.get('write_timeout', 30),
        'charset': conn_settings.get('charset', 'utf8mb4'),
    }
    
    return config


def get_connection(config: Dict[str, Any], raise_on_error: bool = True, database: Optional[str] = None) -> Optional[pymysql.connections.Connection]:
    """
    Create and return a MySQL connection.

    Args:
        config: Connection configuration
        raise_on_error: If False, return None on connection failure instead of raising
        database: Optional database name to auto-select upon connection

    Returns:
        Connection object or None if connection failed and raise_on_error=False
    """
    try:
        connect_args = {
            'host': config['host'],
            'port': config['port'],
            'user': config['user'],
            'password': config['password'],
            'connect_timeout': config['connection_timeout'],
            'read_timeout': config['read_timeout'],
            'write_timeout': config['write_timeout'],
            'charset': config['charset']
        }

        # Add database parameter if provided
        if database:
            connect_args['database'] = database

        connection = pymysql.connect(**connect_args)
        return connection
    except pymysql.Error as e:
        if raise_on_error:
            error_exit(f"Connection failed: {e}")
        return None


def sanitize_sql(sql: str) -> str:
    """
    Sanitize SQL query to fix common shell escaping issues.

    Specifically handles:
    - Escaped != operator (\\!= -> !=) caused by shell history expansion

    Args:
        sql: Raw SQL query string

    Returns:
        Sanitized SQL query string
    """
    # Fix escaped != operator from shell
    return sql.replace('\\!=', '!=')


def execute_sql(connection: pymysql.connections.Connection, sql: str) -> Tuple[List[Tuple], List[str]]:
    """
    Execute SQL query and return results with column names.

    Returns:
        Tuple of (rows, column_names)
    """
    # Sanitize SQL to fix shell escaping issues
    sql = sanitize_sql(sql)

    with connection.cursor() as cursor:
        cursor.execute(sql)
        
        # Get column names if available
        column_names = []
        if cursor.description:
            column_names = [desc[0] for desc in cursor.description]
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Commit for write operations
        if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
            connection.commit()
        
        return rows, column_names


def get_databases(connection: pymysql.connections.Connection) -> List[str]:
    """Get list of all databases."""
    rows, _ = execute_sql(connection, "SHOW DATABASES")
    return [row[0] for row in rows]


def get_tables(connection: pymysql.connections.Connection, database: str) -> List[str]:
    """Get list of tables in a specific database."""
    rows, _ = execute_sql(connection, f"SHOW TABLES FROM `{database}`")
    return [row[0] for row in rows]


def get_table_row_count(connection: pymysql.connections.Connection, database: str, table: str) -> int:
    """Get row count for a specific table."""
    rows, _ = execute_sql(connection, f"SELECT COUNT(*) FROM `{database}`.`{table}`")
    return rows[0][0]


def get_database_overview(connection: pymysql.connections.Connection, server_name: str) -> Dict[str, Any]:
    """
    Get overview of all databases and their tables.
    
    Returns structured data suitable for JSON or text output.
    """
    system_dbs = {'information_schema', 'mysql', 'performance_schema', 'sys'}
    
    databases = get_databases(connection)
    user_databases = [db for db in databases if db not in system_dbs]
    
    overview = {
        'server': server_name,
        'status': 'ok',
        'total_databases': len(databases),
        'user_databases': [],
        'system_databases': []
    }
    
    # Process user databases
    for db in user_databases:
        db_info = {
            'name': db,
            'tables': []
        }
        
        tables = get_tables(connection, db)
        for table in tables:
            try:
                count = get_table_row_count(connection, db, table)
                db_info['tables'].append({
                    'name': table,
                    'row_count': count
                })
            except pymysql.Error as e:
                db_info['tables'].append({
                    'name': table,
                    'row_count': None,
                    'error': str(e)
                })
        
        overview['user_databases'].append(db_info)
    
    # Process system databases (just count tables)
    for db in sorted(system_dbs & set(databases)):
        tables = get_tables(connection, db)
        overview['system_databases'].append({
            'name': db,
            'table_count': len(tables)
        })
    
    return overview


def get_all_servers_overview() -> List[Dict[str, Any]]:
    """
    Get overview of ALL configured servers.
    
    Returns list of server overviews, including unreachable servers and those with missing config.
    """
    connection_names = get_all_connection_names()
    all_overviews = []
    
    for conn_name in connection_names:
        try:
            config = get_connection_config(conn_name)
            
            # Check if config is complete
            is_complete, missing_vars = is_config_complete(config)
            
            if not is_complete:
                # Config is missing required values
                all_overviews.append({
                    'server': conn_name,
                    'status': 'config missing',
                    'missing_vars': missing_vars
                })
                continue
            
            # Try to connect
            connection = get_connection(config, raise_on_error=False)
            
            if connection is None:
                # Server not reachable
                all_overviews.append({
                    'server': conn_name,
                    'status': 'not reachable',
                    'host': config['host'],
                    'port': config['port']
                })
            else:
                # Server reachable - get full overview
                try:
                    overview = get_database_overview(connection, conn_name)
                    all_overviews.append(overview)
                finally:
                    connection.close()
        
        except Exception as e:
            all_overviews.append({
                'server': conn_name,
                'status': 'error',
                'error': str(e)
            })
    
    return all_overviews


def format_overview_text(overview: Dict[str, Any]) -> str:
    """Format database overview as human-readable text."""
    lines = []
    
    # Handle config missing
    if overview.get('status') == 'config missing':
        missing_str = ', '.join(overview.get('missing_vars', []))
        lines.append(f"server: {overview['server']}, db: -, status: config incomplete ({missing_str} missing)")
        lines.append("")  # Empty line
        return "\n".join(lines)
    
    # Handle not reachable
    if overview.get('status') == 'not reachable':
        lines.append(f"server: {overview['server']}, db: -, status: not reachable")
        if 'host' in overview and 'port' in overview:
            lines.append(f"  target: {overview['host']}:{overview['port']}")
        return "\n".join(lines)
    
    # Handle error
    if overview.get('status') == 'error':
        lines.append(f"server: {overview['server']}, db: -, status: error")
        if 'error' in overview:
            lines.append(f"  error: {overview['error']}")
        return "\n".join(lines)
    
    # Handle connected servers (status: ok)
    for db_info in overview.get('user_databases', []):
        lines.append(f"server: {overview['server']}, db: {db_info['name']}, status: ok")
        
        if not db_info['tables']:
            lines.append("  (no tables)")
        else:
            for table in db_info['tables']:
                if table.get('error'):
                    lines.append(f"  {table['name']}: ERROR - {table['error']}")
                else:
                    lines.append(f"  {table['name']}: {table['row_count']}")
        lines.append("")  # Empty line between databases
    
    # If no user databases, show minimal info
    if not overview.get('user_databases'):
        lines.append(f"server: {overview['server']}, db: -, status: ok")
        lines.append("  (no user databases)")
        lines.append("")
    
    return "\n".join(lines)


def format_all_servers_text(all_overviews: List[Dict[str, Any]]) -> str:
    """Format all server overviews as human-readable text."""
    lines = []
    
    for overview in all_overviews:
        lines.append(format_overview_text(overview))
    
    return "\n".join(lines).rstrip()


def format_sql_results_text(rows: List[Tuple], column_names: List[str]) -> str:
    """Format SQL query results as human-readable text."""
    if not rows:
        return "(no results)"
    
    lines = []
    
    # Add column headers if available
    if column_names:
        lines.append(" | ".join(column_names))
        lines.append("-" * 80)
    
    # Add rows
    for row in rows:
        lines.append(" | ".join(str(val) for val in row))
    
    return "\n".join(lines)


def output_json(status: str, data: Any = None, error: str = None) -> None:
    """Output JSON response."""
    response = {
        'status': status,
        'data': data,
        'error': error
    }
    print(json.dumps(response, indent=2, default=str))


def output_yaml(status: str, data: Any = None, error: str = None) -> None:
    """Output YAML response."""
    response = {
        'status': status,
        'data': data,
        'error': error
    }
    print(yaml.dump(response, default_flow_style=False, sort_keys=False, allow_unicode=True))


def error_exit(message: str, json_output: bool = False, yaml_output: bool = False) -> None:
    """Exit with error message."""
    if json_output:
        output_json('error', error=message)
    elif yaml_output:
        output_yaml('error', error=message)
    else:
        print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='MySQL Database Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--server',
        type=str,
        help='Database server connection name (if not specified with --sql, checks ALL servers)'
    )

    parser.add_argument(
        '--database',
        type=str,
        help='Database name to auto-select (allows unqualified table names in queries)'
    )

    parser.add_argument(
        '--sql',
        type=str,
        help='SQL query to execute'
    )
    
    # Create mutually exclusive group for output formats
    output_group = parser.add_mutually_exclusive_group()

    output_group.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )

    output_group.add_argument(
        '--yaml',
        action='store_true',
        help='Output results in YAML format'
    )

    args = parser.parse_args()
    
    # Load environment
    load_environment()
    
    # Determine operation mode
    if args.sql:
        # SQL query mode - use specific server or default
        db_config = load_database_config()
        server_name = args.server or db_config.get('default_connection', 'vosscloud')
        
        try:
            config = get_connection_config(server_name)
        except Exception as e:
            error_exit(str(e), args.json, args.yaml)

        # Check if config is complete
        is_complete, missing_vars = is_config_complete(config)
        if not is_complete:
            error_exit(
                f"Configuration incomplete for {server_name}. Missing: {', '.join(missing_vars)}",
                args.json,
                args.yaml
            )
        
        # Connect to database (with optional database auto-selection)
        try:
            connection = get_connection(config, database=args.database)
        except Exception as e:
            error_exit(str(e), args.json, args.yaml)

        try:
            # Execute provided SQL query
            rows, column_names = execute_sql(connection, args.sql)

            if args.json:
                # Convert rows to list of dicts if column names available
                if column_names:
                    data = [dict(zip(column_names, row)) for row in rows]
                else:
                    data = [list(row) for row in rows]

                output_json(
                    'success',
                    data={
                        'server': config['name'],
                        'rows': data,
                        'row_count': len(rows)
                    }
                )
            elif args.yaml:
                # Convert rows to list of dicts if column names available
                if column_names:
                    data = [dict(zip(column_names, row)) for row in rows]
                else:
                    data = [list(row) for row in rows]

                output_yaml(
                    'success',
                    data={
                        'server': config['name'],
                        'rows': data,
                        'row_count': len(rows)
                    }
                )
            else:
                print(f"Server: {config['name']}")
                print(f"Query: {args.sql}")
                print("-" * 80)
                print(format_sql_results_text(rows, column_names))
                print(f"\n({len(rows)} row(s) returned)")

        except pymysql.Error as e:
            error_exit(f"SQL error: {e}", args.json, args.yaml)
        except Exception as e:
            error_exit(f"Unexpected error: {e}", args.json, args.yaml)
        finally:
            connection.close()
    
    elif args.server:
        # Single server overview mode
        try:
            config = get_connection_config(args.server)
        except Exception as e:
            error_exit(str(e), args.json, args.yaml)

        try:
            # Check if config is complete
            is_complete, missing_vars = is_config_complete(config)

            if not is_complete:
                overview = {
                    'server': args.server,
                    'status': 'config missing',
                    'missing_vars': missing_vars
                }
            else:
                connection = get_connection(config, raise_on_error=False)

                if connection is None:
                    overview = {
                        'server': args.server,
                        'status': 'not reachable',
                        'host': config['host'],
                        'port': config['port']
                    }
                else:
                    try:
                        overview = get_database_overview(connection, config['name'])
                    finally:
                        connection.close()

            if args.json:
                output_json('success', data=overview)
            elif args.yaml:
                output_yaml('success', data=overview)
            else:
                print(format_overview_text(overview))

        except Exception as e:
            error_exit(f"Unexpected error: {e}", args.json, args.yaml)
    
    else:
        # Multi-server overview mode (default - check ALL servers)
        try:
            all_overviews = get_all_servers_overview()

            if args.json:
                output_json('success', data={'servers': all_overviews})
            elif args.yaml:
                output_yaml('success', data={'servers': all_overviews})
            else:
                print(format_all_servers_text(all_overviews))

        except Exception as e:
            error_exit(f"Unexpected error: {e}", args.json, args.yaml)


if __name__ == "__main__":
    main()
