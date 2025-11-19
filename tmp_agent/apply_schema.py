#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
# ]
# ///
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql
import yaml

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'database.yaml'
with open(config_path, 'r') as f:
    db_config = yaml.safe_load(f)

# Get connection config
conn_settings = db_config['mysql_connections']['vosscloud']
env_prefix = conn_settings['env_prefix']

config = {
    'host': os.getenv(f'{env_prefix}_HOST'),
    'port': int(os.getenv(f'{env_prefix}_PORT', '3306')),
    'user': os.getenv(f'{env_prefix}_USER'),
    'password': os.getenv(f'{env_prefix}_PASSWORD'),
    'database': 'indomonitor',
    'charset': 'utf8mb4'
}

# Read schema file
schema_path = Path(__file__).parent.parent / 'database' / 'generated' / 'sql' / 'schema.sql'
with open(schema_path, 'r') as f:
    schema_sql = f.read()

# Connect and execute
try:
    connection = pymysql.connect(**config)
    with connection.cursor() as cursor:
        # Split and execute statements
        statements = []
        current = []
        for line in schema_sql.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            current.append(line)
            if line.endswith(';'):
                statements.append(' '.join(current))
                current = []
        
        for i, stmt in enumerate(statements, 1):
            print(f"Executing statement {i}/{len(statements)}...", file=sys.stderr)
            try:
                cursor.execute(stmt)
                connection.commit()
            except pymysql.Error as e:
                print(f"Error in statement {i}: {e}", file=sys.stderr)
                print(f"Statement: {stmt[:100]}...", file=sys.stderr)
                raise
    
    connection.close()
    print(f"Successfully executed {len(statements)} SQL statements")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
