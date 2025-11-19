#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
# ]
# ///
"""
Execute database schema migration for indomonitor database.
This script reads the generated schema SQL and executes it on the vosscloud server.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql
import yaml


def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)


def get_connection_config():
    """Get vosscloud connection configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'database.yaml'

    with open(config_path, 'r') as f:
        db_config = yaml.safe_load(f)

    conn_settings = db_config['mysql_connections']['vosscloud']
    env_prefix = conn_settings['env_prefix']

    return {
        'host': os.getenv(f'{env_prefix}_HOST'),
        'port': int(os.getenv(f'{env_prefix}_PORT', '3306')),
        'user': os.getenv(f'{env_prefix}_USER'),
        'password': os.getenv(f'{env_prefix}_PASSWORD'),
        'database': 'indomonitor',
        'charset': 'utf8mb4',
    }


def execute_schema():
    """Execute the schema migration."""
    # Load environment
    load_environment()

    # Get connection config
    config = get_connection_config()

    # Read schema file
    schema_path = Path(__file__).parent.parent / 'database' / 'generated' / 'sql' / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Connect to MySQL
    print(f"Connecting to {config['host']}:{config['port']} as {config['user']}...")
    connection = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset=config['charset'],
    )

    try:
        with connection.cursor() as cursor:
            # Split the SQL into individual statements
            # Remove comments and empty lines
            statements = []
            current_statement = []

            for line in schema_sql.split('\n'):
                # Skip comment lines
                if line.strip().startswith('--') or not line.strip():
                    continue

                current_statement.append(line)

                # Check if this line ends a statement (has semicolon)
                if line.strip().endswith(';'):
                    stmt = '\n'.join(current_statement)
                    if stmt.strip():
                        statements.append(stmt)
                    current_statement = []

            print(f"\nExecuting {len(statements)} SQL statements...\n")

            # Execute each statement
            for i, statement in enumerate(statements, 1):
                try:
                    # Extract table name for reporting
                    if 'CREATE TABLE' in statement:
                        table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().replace('IF NOT EXISTS', '').strip()
                        print(f"[{i}/{len(statements)}] Creating table: {table_name}")
                    elif 'ALTER TABLE' in statement:
                        table_name = statement.split('ALTER TABLE')[1].split('\n')[0].strip()
                        print(f"[{i}/{len(statements)}] Adding constraints to: {table_name}")
                    else:
                        print(f"[{i}/{len(statements)}] Executing statement...")

                    cursor.execute(statement)
                    connection.commit()
                    print(f"    ✓ Success")

                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    print(f"    Statement: {statement[:100]}...")
                    raise

            print("\n" + "="*80)
            print("Schema migration completed successfully!")
            print("="*80)

    finally:
        connection.close()


if __name__ == '__main__':
    try:
        execute_schema()
    except Exception as e:
        print(f"\nMigration failed: {e}", file=sys.stderr)
        sys.exit(1)
