#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "httpx",
# ]
# ///
"""Test Splash HTTP API using httpx"""

import httpx
import json

# Splash server URL
SPLASH_URL = "http://vosscloud:32768"

def test_render_html():
    """Test render.html endpoint"""
    print("Testing render.html endpoint...")
    response = httpx.get(
        f"{SPLASH_URL}/render.html",
        params={
            "url": "http://example.com",
            "wait": 1,
            "timeout": 10
        }
    )
    print(f"Status: {response.status_code}")
    print(f"HTML length: {len(response.text)} characters")
    print(f"First 200 chars: {response.text[:200]}")
    print()

def test_render_json():
    """Test render.json endpoint"""
    print("Testing render.json endpoint...")
    response = httpx.get(
        f"{SPLASH_URL}/render.json",
        params={
            "url": "http://example.com",
            "html": 1,
            "png": 0,
            "wait": 1,
            "timeout": 10
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"URL: {data['url']}")
    print(f"Title: {data['title']}")
    print(f"HTML length: {len(data['html'])} characters")
    print()

def test_execute_lua():
    """Test execute endpoint with Lua script"""
    print("Testing execute endpoint with Lua script...")
    lua_script = """function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:wait(1.0))
    local title = splash:evaljs("document.title")
    return {
        html = splash:html(),
        title = title,
        url = splash:url()
    }
end"""

    response = httpx.post(
        f"{SPLASH_URL}/execute",
        json={
            "lua_source": lua_script,
            "url": "http://example.com",
            "timeout": 10
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"URL: {data['url']}")
    print(f"Title: {data['title']}")
    print(f"HTML length: {len(data['html'])} characters")
    print()

if __name__ == "__main__":
    test_render_html()
    test_render_json()
    test_execute_lua()
