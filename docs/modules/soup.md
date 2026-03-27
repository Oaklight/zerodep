# HTML Parser (Soup)

Zero-dependency HTML parser with BeautifulSoup-like API -- stdlib only, Python 3.10+.

## Overview

The Soup module provides a lightweight DOM tree built on top of `html.parser.HTMLParser`. It supports `find`, `find_all`, `select`, `select_one`, `get_text`, `decompose`, and `find_parent` -- the subset of BeautifulSoup used by the vast majority of real-world scraping scripts.

| File | Description | Dependencies |
|------|-------------|--------------|
| `soup.py` | Pure Python implementation | None (stdlib only: `re`, `html.parser`) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp soup/soup.py your_project/
```

Then import directly:

```python
from soup import Soup
```

## Usage Examples

### Basic Parsing

```python
from soup import Soup

html = "<html><body><p class='msg'>Hello <b>world</b></p></body></html>"
soup = Soup(html)
print(soup.find("p", class_="msg").text)
# Hello world
```

### find and find_all

```python
html = """
<ul>
  <li class="item">Apple</li>
  <li class="item">Banana</li>
  <li class="item special">Cherry</li>
</ul>
"""
soup = Soup(html)

# Find first match
first = soup.find("li")
print(first.text)  # Apple

# Find all matches
items = soup.find_all("li", class_="item")
print([i.text for i in items])  # ['Apple', 'Banana', 'Cherry']
```

### CSS Selectors

```python
html = """
<div id="main">
  <p class="intro">Welcome</p>
  <p class="body">Content</p>
</div>
"""
soup = Soup(html)

# Select by ID
main = soup.select_one("#main")

# Select by class
intro = soup.select_one(".intro")
print(intro.text)  # Welcome

# Select by tag
paragraphs = soup.select("p")
print(len(paragraphs))  # 2

# Descendant selector
body_p = soup.select_one("div p.body")
print(body_p.text)  # Content

# Child selector
children = soup.select("div > p")
print(len(children))  # 2

# Attribute selector
soup2 = Soup('<a href="/home">Home</a><a href="/about">About</a>')
links = soup2.select("a[href]")
print(len(links))  # 2
```

### get_text

```python
soup = Soup("<p>Hello <b>world</b></p>")
print(soup.get_text())          # Hello world
print(soup.get_text(separator=" | "))  # Hello  | world
print(soup.get_text(strip=True))  # Helloworld
```

### Attributes

```python
soup = Soup('<a href="/page" class="nav active" id="link1">Click</a>')
a = soup.find("a")

# Access attributes
print(a["href"])         # /page
print(a["id"])           # link1
print(a.get("class"))    # ['nav', 'active']
print(a.get("missing", "default"))  # default
```

### decompose (Remove Elements)

```python
html = "<div><p>Keep</p><script>remove me</script></div>"
soup = Soup(html)
for script in soup.find_all("script"):
    script.decompose()
print(soup.get_text())  # Keep
```

### find_parent

```python
soup = Soup("<div><ul><li>Item</li></ul></div>")
li = soup.find("li")
print(li.find_parent("div").name)  # div
print(li.find_parent().name)       # ul
```

## Supported CSS Selectors

| Selector | Example | Description |
|----------|---------|-------------|
| Tag | `p` | Match by tag name |
| Class | `.intro` | Match by class name |
| ID | `#main` | Match by ID |
| Attribute | `[href]` | Match elements with attribute |
| Attribute value | `[href="/home"]` | Match attribute value |
| Descendant | `div p` | Match `p` inside `div` |
| Child | `div > p` | Match direct children |
| Compound | `p.intro` | Match `p` with class `intro` |

## API Reference

### `Soup(markup, parser="html.parser")`

Parse an HTML document and provide a BeautifulSoup-like API.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `markup` | `str` | -- | The HTML string to parse. |
| `parser` | `str` | `"html.parser"` | Ignored (present only for API compatibility with BS4). |

### `Tag` Methods

| Method | Description |
|--------|-------------|
| `find(name, class_, **attrs)` | Find first matching child element. |
| `find_all(name, class_, **attrs)` | Find all matching child elements. |
| `select(selector)` | Find all elements matching a CSS selector. |
| `select_one(selector)` | Find first element matching a CSS selector. |
| `get_text(separator="", strip=False)` | Get all text content. |
| `decompose()` | Remove this element from its parent. |
| `find_parent(name=None)` | Find the nearest parent, optionally by tag name. |
| `get(attr, default=None)` | Get attribute value. |

### `Tag` Properties

| Property | Type | Description |
|----------|------|-------------|
| `.text` | `str` | All text content (shortcut for `get_text()`). |
| `.name` | `str` | Tag name (e.g. `"div"`). |
| `.attrs` | `dict` | Attribute dictionary. `class` is stored as a list. |
| `.children` | `list` | Child nodes (`Tag` or `str`). |
| `.parent` | `Tag \| None` | Parent element. |

## Comparison with BeautifulSoup

| Feature | zerodep soup | BeautifulSoup |
|---------|-------------|---------------|
| Dependencies | None (stdlib only) | `soupsieve`, optional `lxml`/`html5lib` |
| Files | Single file | Package (multiple files) |
| Parser backends | `html.parser` only | `html.parser`, `lxml`, `html5lib` |
| find / find_all | Yes | Yes |
| CSS selectors | Basic (tag, class, id, attr, descendant, child) | Full (via soupsieve) |
| prettify | No | Yes |
| NavigableString | No (plain `str`) | Yes |
| Parse speed (small) | 149 us | 446 us (2.99x slower) |
| Parse speed (large) | 12.7 ms | 37.1 ms (2.93x slower) |

**When to use zerodep:** You need basic HTML parsing (find, select, get_text) with zero dependencies and fast performance.

**When to use BeautifulSoup:** You need advanced CSS pseudo-selectors, multiple parser backends, or NavigableString features.

## Benchmark

Benchmarked against `beautifulsoup4` across small, medium, and large HTML documents.

See [Soup Benchmark](../benchmarks/soup.md) for detailed results.
