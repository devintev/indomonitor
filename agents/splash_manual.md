# Splash - JavaScript Rendering Service Manual

## Overview

Splash is a lightweight JavaScript rendering service with an HTTP API. It's essentially a headless browser that can render JavaScript-heavy websites and return HTML, screenshots, or HAR data.

**Server:** http://vosscloud:32768/
**Version:** 3.5
**Documentation:** http://splash.readthedocs.org/

## Key Features

- Process multiple webpages in parallel
- Get HTML results and/or take screenshots
- Execute custom JavaScript in page context
- Write Lua browsing scripts for complex interactions
- Get detailed rendering info in HAR format
- Turn OFF images or use Adblock Plus rules for faster rendering

## HTTP API Endpoints

### 1. render.html - Get Rendered HTML

Returns the JavaScript-rendered HTML of a page.

**Shell (curl):**
```bash
# Basic usage
curl 'http://vosscloud:32768/render.html?url=http://example.com'

# With wait time (seconds to wait after page load)
curl 'http://vosscloud:32768/render.html?url=http://example.com&wait=2'

# With timeout
curl 'http://vosscloud:32768/render.html?url=http://example.com&timeout=10&wait=1'

# Without images (faster)
curl 'http://vosscloud:32768/render.html?url=http://example.com&images=0'

# With custom viewport
curl 'http://vosscloud:32768/render.html?url=http://example.com&viewport=1920x1080'
```

**Python (httpx):**
```python
import httpx

response = httpx.get(
    "http://vosscloud:32768/render.html",
    params={
        "url": "http://example.com",
        "wait": 1,
        "timeout": 10,
        "images": 1
    }
)

html = response.text
print(f"HTML length: {len(html)} characters")
```

**Parameters:**
- `url` (required): The URL to render
- `wait` (optional): Time in seconds to wait after page load (default: 0)
- `timeout` (optional): Maximum time in seconds for rendering (default: 30)
- `viewport` (optional): Viewport size as "WIDTHxHEIGHT", e.g., "1920x1080"
- `images` (optional): 1 to load images, 0 to skip (default: 1)
- `resource_timeout` (optional): Timeout for individual network requests
- `js_source` (optional): JavaScript code to execute in page context
- `headers` (optional): Custom HTTP headers (JSON object)

---

### 2. render.json - Get JSON Response with Multiple Outputs

Returns a JSON object containing HTML, PNG, HAR, and other information.

**Shell (curl):**
```bash
# Get HTML only
curl 'http://vosscloud:32768/render.json?url=http://example.com&html=1&wait=1'

# Get HTML and PNG screenshot
curl 'http://vosscloud:32768/render.json?url=http://example.com&html=1&png=1&wait=1'

# Get full information (HTML, PNG, HAR, console, history)
curl 'http://vosscloud:32768/render.json?url=http://example.com&html=1&png=1&har=1&console=1&history=1'

# Pretty print JSON
curl 'http://vosscloud:32768/render.json?url=http://example.com&html=1' | python3 -m json.tool
```

**Python (httpx):**
```python
import httpx

response = httpx.get(
    "http://vosscloud:32768/render.json",
    params={
        "url": "http://example.com",
        "html": 1,
        "png": 0,
        "wait": 1,
        "timeout": 10
    }
)

data = response.json()
print(f"URL: {data['url']}")
print(f"Title: {data['title']}")
print(f"HTML length: {len(data['html'])} characters")
```

**Parameters:**
- All parameters from `render.html` plus:
- `html` (optional): 1 to include HTML, 0 to exclude (default: 0)
- `png` (optional): 1 to include PNG screenshot (base64), 0 to exclude (default: 0)
- `jpeg` (optional): 1 to include JPEG screenshot, 0 to exclude (default: 0)
- `har` (optional): 1 to include HAR data, 0 to exclude (default: 0)
- `iframes` (optional): 1 to include iframe information, 0 to exclude (default: 0)
- `script` (optional): 1 to include JavaScript execution result, 0 to exclude (default: 0)
- `console` (optional): 1 to include console messages, 0 to exclude (default: 0)
- `history` (optional): 1 to include request/response history, 0 to exclude (default: 0)

---

### 3. render.png - Get PNG Screenshot

Returns a PNG screenshot of the rendered page.

**Shell (curl):**
```bash
# Basic screenshot
curl 'http://vosscloud:32768/render.png?url=http://example.com' > screenshot.png

# Custom size
curl 'http://vosscloud:32768/render.png?url=http://example.com&width=1920&height=1080' > screenshot.png

# Thumbnail
curl 'http://vosscloud:32768/render.png?url=http://example.com&width=320&height=240' > thumbnail.png

# Full page screenshot (requires wait > 0)
curl 'http://vosscloud:32768/render.png?url=http://example.com&render_all=1&wait=1' > fullpage.png
```

**Python (httpx):**
```python
import httpx

response = httpx.get(
    "http://vosscloud:32768/render.png",
    params={
        "url": "http://example.com",
        "width": 1920,
        "height": 1080,
        "wait": 1
    }
)

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(response.content)
```

**Parameters:**
- All parameters from `render.html` plus:
- `width` (optional): Width in pixels
- `height` (optional): Height in pixels
- `render_all` (optional): 1 to capture full page, 0 for viewport only (default: 0)

---

### 4. render.har - Get HAR Data

Returns HTTP Archive (HAR) format data with all network requests/responses.

**Shell (curl):**
```bash
# Basic HAR
curl 'http://vosscloud:32768/render.har?url=http://example.com&wait=1'

# HAR with request/response bodies
curl 'http://vosscloud:32768/render.har?url=http://example.com&wait=1&request_body=1&response_body=1'
```

**Python (httpx):**
```python
import httpx

response = httpx.get(
    "http://vosscloud:32768/render.har",
    params={
        "url": "http://example.com",
        "wait": 1,
        "request_body": 1,
        "response_body": 1
    }
)

har_data = response.json()
print(f"Requests: {len(har_data['log']['entries'])}")
```

**Parameters:**
- All parameters from `render.html` plus:
- `request_body` (optional): 1 to include request bodies, 0 to exclude (default: 0)
- `response_body` (optional): 1 to include response bodies, 0 to exclude (default: 0)

---

### 5. execute - Run Lua Scripts

Execute custom Lua scripts for complex browser automation.

**Shell (curl):**
```bash
# Simple Lua script
curl -X POST http://vosscloud:32768/execute \
  -H "Content-Type: application/json" \
  -d '{
    "lua_source": "function main(splash, args) assert(splash:go(args.url)) assert(splash:wait(1.0)) return {html = splash:html(), title = splash:evaljs(\"document.title\"), url = splash:url()} end",
    "url": "http://example.com",
    "timeout": 10
  }'

# From file
curl -X POST http://vosscloud:32768/execute \
  -H "Content-Type: application/json" \
  -d @script.json
```

**Python (httpx):**
```python
import httpx

lua_script = """
function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:wait(1.0))

    local title = splash:evaljs("document.title")
    local body = splash:select("body")

    return {
        html = splash:html(),
        title = title,
        url = splash:url()
    }
end
"""

response = httpx.post(
    "http://vosscloud:32768/execute",
    json={
        "lua_source": lua_script,
        "url": "http://example.com",
        "timeout": 10
    }
)

data = response.json()
print(f"Title: {data['title']}")
print(f"URL: {data['url']}")
```

**Common Lua Script Patterns:**

**Navigate and wait:**
```lua
function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:wait(2.0))
    return splash:html()
end
```

**Execute JavaScript:**
```lua
function main(splash, args)
    assert(splash:go(args.url))
    local result = splash:evaljs("document.querySelector('h1').textContent")
    return result
end
```

**Click elements:**
```lua
function main(splash, args)
    assert(splash:go(args.url))
    local button = splash:select("button#submit")
    button:click()
    assert(splash:wait(1.0))
    return splash:html()
end
```

**Scroll page:**
```lua
function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:runjs("window.scrollTo(0, document.body.scrollHeight)"))
    assert(splash:wait(1.0))
    return splash:html()
end
```

---

## Common Use Cases

### 1. Get Rendered HTML for Scraping

**Shell:**
```bash
curl 'http://vosscloud:32768/render.html?url=http://example.com&wait=2' > page.html
```

**Python:**
```python
import httpx
from bs4 import BeautifulSoup

response = httpx.get(
    "http://vosscloud:32768/render.html",
    params={"url": "http://example.com", "wait": 2}
)

soup = BeautifulSoup(response.text, "html.parser")
# Now scrape the rendered HTML
```

### 2. Take Screenshots of Multiple Pages

**Python:**
```python
import httpx

urls = [
    "http://example.com",
    "http://example.org",
    "http://example.net"
]

for i, url in enumerate(urls):
    response = httpx.get(
        "http://vosscloud:32768/render.png",
        params={"url": url, "wait": 1, "width": 1920, "height": 1080}
    )
    with open(f"screenshot_{i}.png", "wb") as f:
        f.write(response.content)
```

### 3. Wait for Dynamic Content

**Python:**
```python
import httpx

# Wait for AJAX content to load
response = httpx.get(
    "http://vosscloud:32768/render.html",
    params={
        "url": "http://example.com",
        "wait": 3,  # Wait 3 seconds for dynamic content
        "timeout": 30
    }
)
```

### 4. Disable Images for Faster Rendering

**Python:**
```python
import httpx

response = httpx.get(
    "http://vosscloud:32768/render.html",
    params={
        "url": "http://example.com",
        "images": 0,  # Don't load images
        "wait": 1
    }
)
```

### 5. Execute Custom JavaScript

**Python:**
```python
import httpx

js_code = """
document.querySelectorAll('.ad').forEach(el => el.remove());
return document.documentElement.outerHTML;
"""

response = httpx.get(
    "http://vosscloud:32768/render.html",
    params={
        "url": "http://example.com",
        "js_source": js_code,
        "wait": 1
    }
)
```

---

## Best Practices

1. **Always set a timeout**: Prevent hanging requests
   ```python
   params={"url": url, "timeout": 30}
   ```

2. **Use wait parameter for dynamic content**: Give JavaScript time to execute
   ```python
   params={"url": url, "wait": 2}
   ```

3. **Disable images when not needed**: Faster rendering
   ```python
   params={"url": url, "images": 0}
   ```

4. **Use appropriate viewport**: Match your target device
   ```python
   params={"url": url, "viewport": "1920x1080"}
   ```

5. **Handle errors gracefully**:
   ```python
   try:
       response = httpx.get(splash_url, params=params, timeout=60)
       response.raise_for_status()
   except httpx.HTTPError as e:
       print(f"Error: {e}")
   ```

6. **For complex interactions, use Lua scripts**: More control than simple parameters

---

## Integration with IndoMonitor

For news scraping in the IndoMonitor project, use Splash to:

1. **Render JavaScript-heavy news sites**:
   ```python
   import httpx

   def get_rendered_html(url: str, wait: float = 2.0) -> str:
       response = httpx.get(
           "http://vosscloud:32768/render.html",
           params={
               "url": url,
               "wait": wait,
               "timeout": 30,
               "images": 0  # Don't need images for text scraping
           }
       )
       return response.text
   ```

2. **Handle AJAX-loaded article lists**:
   ```python
   def get_article_list(url: str) -> str:
       lua_script = """
       function main(splash, args)
           assert(splash:go(args.url))
           assert(splash:wait(3.0))

           -- Scroll to load more articles
           assert(splash:runjs("window.scrollTo(0, document.body.scrollHeight)"))
           assert(splash:wait(2.0))

           return splash:html()
       end
       """

       response = httpx.post(
           "http://vosscloud:32768/execute",
           json={"lua_source": lua_script, "url": url, "timeout": 30}
       )
       return response.json()["html"]
   ```

3. **Wait for specific elements**:
   ```python
   lua_script = """
   function main(splash, args)
       assert(splash:go(args.url))

       -- Wait for article list to appear
       while not splash:select('.article-list') do
           splash:wait(0.5)
       end

       return splash:html()
   end
   """
   ```

---

## Error Handling

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (check parameters)
- `504`: Timeout (increase timeout parameter)
- `415`: Unsupported Media Type (check Content-Type header for POST requests)
- `502`: Bad gateway (Splash may be overloaded or down)

**Python Error Handling Example:**
```python
import httpx

def safe_render(url: str) -> str:
    try:
        response = httpx.get(
            "http://vosscloud:32768/render.html",
            params={"url": url, "wait": 2, "timeout": 30},
            timeout=60  # Client-side timeout
        )
        response.raise_for_status()
        return response.text
    except httpx.TimeoutException:
        print(f"Timeout rendering {url}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error {e.response.status_code} rendering {url}")
        return None
    except Exception as e:
        print(f"Error rendering {url}: {e}")
        return None
```

---

## Additional Resources

- **Official Documentation**: http://splash.readthedocs.org/
- **HTTP API Reference**: http://splash.readthedocs.org/en/stable/api.html
- **Lua Scripting Tutorial**: http://splash.readthedocs.org/en/stable/scripting-tutorial.html
- **Lua API Reference**: http://splash.readthedocs.org/en/stable/scripting-ref.html
- **GitHub Repository**: https://github.com/scrapinghub/splash

---

## Server Information

- **Host**: vosscloud
- **Port**: 32768
- **Base URL**: http://vosscloud:32768/
- **Version**: 3.5
- **Status Check**: http://vosscloud:32768/ (returns web interface)
