#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
# ]
# ///
"""
Execute MariaDB 5.5 compatible schema migration.
This script adapts the generated schema for MariaDB 5.5 compatibility.
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


# MariaDB 5.5 compatible schema statements
SCHEMA_STATEMENTS = [
    # Table 1: scraper_scripts (depends on news_sites, we'll add FK later)
    """
    CREATE TABLE IF NOT EXISTS indomonitor.scraper_scripts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        site_id INT NOT NULL,
        version INT NOT NULL DEFAULT 1,
        script_code TEXT NOT NULL,
        status VARCHAR(50) COMMENT 'active, deprecated, failed',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_site_id (site_id),
        INDEX idx_status (status),
        UNIQUE KEY unique_site_version (site_id, version)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Table 2: site_structure_reports
    """
    CREATE TABLE IF NOT EXISTS indomonitor.site_structure_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        site_id INT NOT NULL,
        report_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_site_id (site_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Table 3: agent_runs
    """
    CREATE TABLE IF NOT EXISTS indomonitor.agent_runs (
        id CHAR(36) NOT NULL PRIMARY KEY,
        agent_type VARCHAR(100) NOT NULL COMMENT 'Manager, Research, ScriptWriter, Debug, Monitor, Validation',
        site_id INT,
        started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        status VARCHAR(50) NOT NULL COMMENT 'running, completed, failed',
        token_usage INT,
        report TEXT,
        INDEX idx_agent_type (agent_type),
        INDEX idx_status (status),
        INDEX idx_started_at (started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Table 4: scrape_runs
    """
    CREATE TABLE IF NOT EXISTS indomonitor.scrape_runs (
        id CHAR(36) NOT NULL PRIMARY KEY,
        site_id INT NOT NULL,
        script_id INT,
        started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        status VARCHAR(50) NOT NULL COMMENT 'running, completed, failed',
        articles_found INT NOT NULL DEFAULT 0,
        errors TEXT,
        INDEX idx_site_id (site_id),
        INDEX idx_status (status),
        INDEX idx_started_at (started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Table 5: news_scrapes
    """
    CREATE TABLE IF NOT EXISTS indomonitor.news_scrapes (
        id CHAR(36) NOT NULL PRIMARY KEY,
        run_id CHAR(36) NOT NULL,
        site_id INT NOT NULL,
        url TEXT NOT NULL,
        url_hash CHAR(64),
        title TEXT,
        content TEXT,
        published_at DATETIME,
        scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_site_id (site_id),
        INDEX idx_published_at (published_at),
        INDEX idx_scraped_at (scraped_at),
        FULLTEXT INDEX ft_title_content (title, content),
        UNIQUE KEY unique_url_hash (url_hash)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]

# Foreign key constraints to add after all tables exist
FK_STATEMENTS = [
    "ALTER TABLE indomonitor.scraper_scripts ADD CONSTRAINT fk_scraper_site FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE",
    "ALTER TABLE indomonitor.site_structure_reports ADD CONSTRAINT fk_report_site FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE",
    "ALTER TABLE indomonitor.agent_runs ADD CONSTRAINT fk_agent_site FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE SET NULL",
    "ALTER TABLE indomonitor.scrape_runs ADD CONSTRAINT fk_run_site FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE",
    "ALTER TABLE indomonitor.scrape_runs ADD CONSTRAINT fk_run_script FOREIGN KEY (script_id) REFERENCES scraper_scripts(id) ON DELETE SET NULL",
    "ALTER TABLE indomonitor.news_scrapes ADD CONSTRAINT fk_scrape_run FOREIGN KEY (run_id) REFERENCES scrape_runs(id) ON DELETE CASCADE",
    "ALTER TABLE indomonitor.news_scrapes ADD CONSTRAINT fk_scrape_site FOREIGN KEY (site_id) REFERENCES news_sites(id) ON DELETE CASCADE",
    "ALTER TABLE indomonitor.news_sites ADD CONSTRAINT fk_main_script FOREIGN KEY (main_script_id) REFERENCES scraper_scripts(id) ON DELETE SET NULL",
    "ALTER TABLE indomonitor.news_sites ADD CONSTRAINT fk_secondary_script FOREIGN KEY (secondary_script_id) REFERENCES scraper_scripts(id) ON DELETE SET NULL",
    "ALTER TABLE indomonitor.news_sites ADD CONSTRAINT fk_tertiary_script FOREIGN KEY (tertiary_script_id) REFERENCES scraper_scripts(id) ON DELETE SET NULL",
]


def execute_migration():
    """Execute the schema migration."""
    load_environment()
    config = get_connection_config()

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
            print("\n" + "="*80)
            print("Creating Tables")
            print("="*80)

            table_names = ['scraper_scripts', 'site_structure_reports', 'agent_runs',
                          'scrape_runs', 'news_scrapes']

            for i, (name, stmt) in enumerate(zip(table_names, SCHEMA_STATEMENTS), 1):
                print(f"\n[{i}/5] Creating table: {name}")
                try:
                    cursor.execute(stmt)
                    connection.commit()
                    print(f"    ✓ Success")
                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    raise

            print("\n" + "="*80)
            print("Adding Foreign Key Constraints")
            print("="*80)

            for i, stmt in enumerate(FK_STATEMENTS, 1):
                # Extract constraint name from statement
                constraint_name = stmt.split('CONSTRAINT')[1].split('FOREIGN')[0].strip()
                print(f"\n[{i}/{len(FK_STATEMENTS)}] Adding constraint: {constraint_name}")
                try:
                    cursor.execute(stmt)
                    connection.commit()
                    print(f"    ✓ Success")
                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    # Continue with other constraints even if one fails

            print("\n" + "="*80)
            print("Verifying Migration")
            print("="*80)

            cursor.execute("SHOW TABLES FROM indomonitor")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"\nTables created: {len(tables)}")
            for table in sorted(tables):
                cursor.execute(f"SELECT COUNT(*) FROM indomonitor.{table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} rows")

            print("\n" + "="*80)
            print("Migration Completed Successfully!")
            print("="*80)

    finally:
        connection.close()


if __name__ == '__main__':
    try:
        execute_migration()
    except Exception as e:
        print(f"\nMigration failed: {e}", file=sys.stderr)
        sys.exit(1)
