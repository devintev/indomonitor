#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pymysql",
#   "python-dotenv",
#   "pyyaml",
#   "httpx",
#   "html2text",
# ]
# ///
"""
IndoMonitor CLI Tool

A command-line interface for managing the IndoMonitor news monitoring system.

Usage:
  # Add a new news site to monitor
  ./scripts/indomonitor.py add site https://example.com

  # List all news sites
  ./scripts/indomonitor.py list news_sites

  # Get rendered HTML from a URL via Splash
  ./scripts/indomonitor.py get https://example.com

  # Get rendered HTML converted to Markdown
  ./scripts/indomonitor.py get md https://example.com

  # Show help
  ./scripts/indomonitor.py -h
  ./scripts/indomonitor.py add site -h

Commands:
  add site <url>     Add a new news site to the monitoring system
  list news_sites    List all news site URLs
  get <url>          Fetch and render a URL via Splash, return HTML
  get md <url>       Fetch and render a URL via Splash, return Markdown

Examples:
  ./scripts/indomonitor.py add site https://news.example.com
  ./scripts/indomonitor.py add site "https://blog.example.com/news"
  ./scripts/indomonitor.py list news_sites
  ./scripts/indomonitor.py get https://news.example.com
  ./scripts/indomonitor.py get md https://news.example.com
"""

import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, Tuple
import httpx
import html2text

# Add scripts directory to path to import manage_db
sys.path.insert(0, str(Path(__file__).parent))

# Import from manage_db.py
from manage_db import (
    load_environment,
    load_database_config,
    get_connection_config,
    get_connection,
    execute_sql,
    is_config_complete
)

# Splash server configuration
SPLASH_URL = "http://vosscloud:32768"


def fetch_html_via_splash(url: str, wait: float = 2.0, timeout: int = 30) -> str:
    """
    Fetch and render a URL via Splash, returning the rendered HTML.

    Args:
        url: The URL to fetch
        wait: Time in seconds to wait after page load (default: 2.0)
        timeout: Maximum time in seconds for rendering (default: 30)

    Returns:
        Rendered HTML as string

    Raises:
        httpx.HTTPError: If the request fails
    """
    response = httpx.get(
        f"{SPLASH_URL}/render.html",
        params={
            "url": url,
            "wait": wait,
            "timeout": timeout,
            "images": 0  # Disable images for faster rendering
        },
        timeout=timeout + 10  # Client timeout slightly longer than server timeout
    )
    response.raise_for_status()
    return response.text


def html_to_markdown(html: str) -> str:
    """
    Convert HTML to Markdown format.

    Args:
        html: HTML string to convert

    Returns:
        Markdown formatted string
    """
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    return h.handle(html)


def validate_url(url: str) -> Tuple[bool, Optional[str], str]:
    """
    Validate URL format and extract domain name.
    Automatically prepends https:// if scheme is missing.

    Returns:
        Tuple of (is_valid, domain_name, normalized_url)
    """
    try:
        # First, try parsing as-is
        parsed = urlparse(url)

        # If no scheme, prepend https://
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)

        # Check if netloc is present after normalization
        if not parsed.netloc:
            return False, None, url

        # Check if scheme is http or https
        if parsed.scheme not in ['http', 'https']:
            return False, None, url

        # Extract domain (remove www. prefix if present)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]

        return True, domain, url

    except Exception:
        return False, None, url


def extract_site_name(url: str) -> str:
    """
    Extract a human-readable site name from URL.

    Returns site name derived from domain.
    """
    is_valid, domain, _ = validate_url(url)

    if not is_valid or not domain:
        return "Unknown Site"

    # Remove TLD and capitalize
    # e.g., "news.example.com" -> "News Example"
    parts = domain.split('.')
    if len(parts) > 1:
        # Remove TLD (.com, .org, etc.)
        name_parts = parts[:-1]
    else:
        name_parts = parts

    # Capitalize and join
    name = ' '.join(part.capitalize() for part in name_parts)

    return name


def check_site_exists(connection, url: str) -> Optional[dict]:
    """
    Check if a site with the given URL already exists.

    Returns:
        Dict with site info if exists, None otherwise
    """
    sql = "SELECT id, url, name, status FROM indomonitor.news_sites WHERE url = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, (url,))
        result = cursor.fetchone()

        if result:
            return {
                'id': result[0],
                'url': result[1],
                'name': result[2],
                'status': result[3]
            }

        return None


def add_site(connection, url: str, name: Optional[str] = None, status: str = 'pending') -> int:
    """
    Add a new news site to the database.

    Returns:
        The ID of the newly inserted site
    """
    # Use provided name or extract from URL
    if not name:
        name = extract_site_name(url)

    # Get current timestamp for updated_at
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sql = """
        INSERT INTO indomonitor.news_sites
        (url, name, status, updated_at)
        VALUES (%s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, (url, name, status, now))
        connection.commit()

        # Get the inserted ID
        site_id = cursor.lastrowid

        return site_id


def cmd_add_site(args):
    """Handle 'add site' command."""
    url = args.url

    # Validate URL format and get normalized URL
    is_valid, domain, normalized_url = validate_url(url)
    if not is_valid:
        print(f"Error: Invalid URL format: {url}", file=sys.stderr)
        print("URL must be a valid http:// or https:// URL", file=sys.stderr)
        sys.exit(1)

    # Use the normalized URL
    url = normalized_url

    # Load environment and config
    load_environment()
    db_config = load_database_config()
    server_name = db_config.get('default_connection', 'vosscloud')

    # Get connection config
    try:
        config = get_connection_config(server_name)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if config is complete
    is_complete, missing_vars = is_config_complete(config)
    if not is_complete:
        print(f"Error: Configuration incomplete for {server_name}", file=sys.stderr)
        print(f"Missing: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    try:
        connection = get_connection(config)
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Check if site already exists
        existing_site = check_site_exists(connection, url)

        if existing_site:
            print(f"Site already exists:")
            print(f"  ID:     {existing_site['id']}")
            print(f"  URL:    {existing_site['url']}")
            print(f"  Name:   {existing_site['name']}")
            print(f"  Status: {existing_site['status']}")
            sys.exit(0)

        # Add new site
        site_id = add_site(connection, url)
        site_name = extract_site_name(url)

        print(f"Successfully added new site:")
        print(f"  ID:     {site_id}")
        print(f"  URL:    {url}")
        print(f"  Name:   {site_name}")
        print(f"  Status: pending")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        connection.close()


def cmd_list_news_sites(args):
    """Handle 'list news_sites' command."""
    # Load environment and config
    load_environment()
    db_config = load_database_config()
    server_name = db_config.get('default_connection', 'vosscloud')

    # Get connection config
    try:
        config = get_connection_config(server_name)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if config is complete
    is_complete, missing_vars = is_config_complete(config)
    if not is_complete:
        print(f"Error: Configuration incomplete for {server_name}", file=sys.stderr)
        print(f"Missing: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    try:
        connection = get_connection(config)
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Query news sites
        sql = "SELECT url FROM indomonitor.news_sites WHERE status != 'deleted' ORDER BY id"

        with connection.cursor() as cursor:
            cursor.execute(sql)
            results = cursor.fetchall()

            # Print URLs, one per line
            for row in results:
                print(row[0])

            # If no results, exit silently (no output)
            if not results:
                sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        connection.close()


def cmd_get(args):
    """Handle 'get' command and 'get md' subcommand."""
    # Parse the arguments manually to handle both 'get <url>' and 'get md <url>'
    arguments = args.args

    if len(arguments) < 1:
        print("Error: URL required", file=sys.stderr)
        print("Usage: ./scripts/indomonitor.py get <url>", file=sys.stderr)
        print("       ./scripts/indomonitor.py get md <url>", file=sys.stderr)
        sys.exit(1)

    # Check if first argument is 'md' (subcommand)
    if arguments[0] == 'md':
        # This is 'get md <url>'
        if len(arguments) < 2:
            print("Error: URL required for 'get md' command", file=sys.stderr)
            print("Usage: ./scripts/indomonitor.py get md <url>", file=sys.stderr)
            sys.exit(1)

        url = arguments[1]
        output_format = 'markdown'
    else:
        # This is 'get <url>'
        url = arguments[0]
        output_format = 'html'

    # Validate URL format and get normalized URL
    is_valid, domain, normalized_url = validate_url(url)
    if not is_valid:
        print(f"Error: Invalid URL format: {url}", file=sys.stderr)
        print("URL must be a valid domain or http:// / https:// URL", file=sys.stderr)
        sys.exit(1)

    # Use the normalized URL
    url = normalized_url

    # Fetch HTML via Splash
    try:
        html = fetch_html_via_splash(url)
    except httpx.HTTPError as e:
        print(f"Error fetching URL via Splash: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output based on format
    if output_format == 'markdown':
        try:
            markdown = html_to_markdown(html)
            print(markdown)
        except Exception as e:
            print(f"Error converting HTML to Markdown: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(html)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='IndoMonitor CLI - News monitoring system management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title='commands',
        description='Available commands',
        dest='command',
        required=True
    )

    # 'add' command parser
    add_parser = subparsers.add_parser(
        'add',
        help='Add resources to the monitoring system'
    )

    # 'add' subcommands
    add_subparsers = add_parser.add_subparsers(
        title='add commands',
        description='Resources to add',
        dest='add_command',
        required=True
    )

    # 'add site' subcommand
    add_site_parser = add_subparsers.add_parser(
        'site',
        help='Add a new news site to monitor',
        description='Add a new news site to the monitoring system'
    )

    add_site_parser.add_argument(
        'url',
        type=str,
        help='URL of the news site to monitor (e.g., https://news.example.com)'
    )

    add_site_parser.set_defaults(func=cmd_add_site)

    # 'list' command parser
    list_parser = subparsers.add_parser(
        'list',
        help='List resources from the monitoring system'
    )

    # 'list' subcommands
    list_subparsers = list_parser.add_subparsers(
        title='list commands',
        description='Resources to list',
        dest='list_command',
        required=True
    )

    # 'list news_sites' subcommand
    list_news_sites_parser = list_subparsers.add_parser(
        'news_sites',
        help='List all news site URLs',
        description='List all news site URLs from the database (one per line)'
    )

    list_news_sites_parser.set_defaults(func=cmd_list_news_sites)

    # 'get' command parser
    get_parser = subparsers.add_parser(
        'get',
        help='Fetch and render a URL via Splash',
        description='Fetch a URL via Splash and return HTML or Markdown'
    )

    get_parser.add_argument(
        'args',
        nargs='+',
        help='URL to fetch, or "md <url>" for Markdown output'
    )

    get_parser.set_defaults(func=cmd_get)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
