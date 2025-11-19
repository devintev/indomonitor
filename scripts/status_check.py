#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
# ]
# ///
"""
MySQL Server Status Checker

Connects to a MySQL server and provides detailed status information including:
- Connection status
- List of databases
- Tables in each database
- Row counts for each table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql
import yaml
from typing import Dict, List, Optional


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)


def load_database_config() -> Dict:
    """Load database configuration from config/database.yaml."""
    config_path = Path(__file__).parent.parent / 'config' / 'database.yaml'
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_connection_config(connection_name: Optional[str] = None) -> Dict[str, str]:
    """Get MySQL connection configuration for specified or default connection."""
    db_config = load_database_config()
    
    # Use provided connection name or default
    if connection_name is None:
        connection_name = db_config.get('default_connection', 'vosscloud')
    
    # Get connection settings
    connections = db_config.get('mysql_connections', {})
    if connection_name not in connections:
        print(f"Error: Connection '{connection_name}' not found in config/database.yaml")
        print(f"Available connections: {', '.join(connections.keys())}")
        sys.exit(1)
    
    conn_settings = connections[connection_name]
    env_prefix = conn_settings['env_prefix']
    
    # Build config from environment variables
    config = {
        'name': connection_name,
        'host': os.getenv(f'{env_prefix}_HOST', 'localhost'),
        'port': int(os.getenv(f'{env_prefix}_PORT', '3306')),
        'user': os.getenv(f'{env_prefix}_USER', 'root'),
        'password': os.getenv(f'{env_prefix}_PASSWORD', ''),
        'connection_timeout': conn_settings.get('connection_timeout', 5),
        'read_timeout': conn_settings.get('read_timeout', 30),
        'write_timeout': conn_settings.get('write_timeout', 30),
        'charset': conn_settings.get('charset', 'utf8mb4'),
    }
    
    return config


def test_connection(config: Dict[str, str]) -> pymysql.connections.Connection:
    """Test MySQL connection and return connection object."""
    try:
        print(f"Connecting to MySQL server at {config['host']}:{config['port']}...")
        print(f"Using connection: {config['name']}")
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            connect_timeout=config['connection_timeout'],
            read_timeout=config['read_timeout'],
            write_timeout=config['write_timeout'],
            charset=config['charset']
        )
        print("✓ Connection successful!")
        return connection
    except pymysql.Error as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


def get_databases(connection: pymysql.connections.Connection) -> List[str]:
    """Get list of all databases."""
    with connection.cursor() as cursor:
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
    return databases


def get_tables(connection: pymysql.connections.Connection, database: str) -> List[str]:
    """Get list of tables in a specific database."""
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW TABLES FROM `{database}`")
        tables = [row[0] for row in cursor.fetchall()]
    return tables


def get_table_row_count(connection: pymysql.connections.Connection, database: str, table: str) -> int:
    """Get row count for a specific table."""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table}`")
        count = cursor.fetchone()[0]
    return count


def display_server_info(connection: pymysql.connections.Connection) -> None:
    """Display MySQL server information."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"\nMySQL Version: {version}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("MySQL Server Status Check")
    print("=" * 60)

    # Load environment variables
    load_environment()

    # Parse command line arguments
    connection_name = sys.argv[1] if len(sys.argv) > 1 else None

    # Get connection configuration
    config = get_connection_config(connection_name)

    # Test connection
    connection = test_connection(config)

    try:
        # Display server info
        display_server_info(connection)

        # Get and display databases
        databases = get_databases(connection)
        print(f"\nFound {len(databases)} database(s):")

        # Filter out system databases for cleaner output (optional)
        system_dbs = {'information_schema', 'mysql', 'performance_schema', 'sys'}
        user_databases = [db for db in databases if db not in system_dbs]

        if user_databases:
            print("\nUser Databases:")
            for db in user_databases:
                print(f"\n  Database: {db}")
                print("  " + "-" * 50)

                tables = get_tables(connection, db)
                if tables:
                    print(f"  Tables: {len(tables)}")
                    for table in tables:
                        try:
                            count = get_table_row_count(connection, db, table)
                            print(f"    - {table}: {count:,} rows")
                        except pymysql.Error as e:
                            print(f"    - {table}: Error reading ({e})")
                else:
                    print("  No tables found")

        if system_dbs & set(databases):
            print("\n\nSystem Databases:")
            for db in sorted(system_dbs & set(databases)):
                tables = get_tables(connection, db)
                print(f"  - {db}: {len(tables)} tables")

        print("\n" + "=" * 60)
        print("Status check complete!")
        print("=" * 60)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
