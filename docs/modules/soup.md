# HTML Parser (Soup)

Zero-dependency HTML parser with BeautifulSoup-like API -- stdlib only, Python 3.10+.

> **Replaces:** `beautifulsoup4` (common subset)

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

# Pseudo-selectors
html3 = """
<ul>
  <li class="a">First</li>
  <li class="b">Second</li>
  <li class="c">Third</li>
</ul>
"""
soup3 = Soup(html3)

# :first-child / :last-child
print(soup3.select_one("li:first-child").text)  # First
print(soup3.select_one("li:last-child").text)   # Third

# :only-child
soup4 = Soup("<div><span>Alone</span></div>")
print(soup4.select_one("span:only-child").text)  # Alone

# :not(selector)
others = soup3.select("li:not(.a)")
print([li.text for li in others])  # ['Second', 'Third']
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

### Tree Mutation

```python
from soup import Soup

html = "<ul><li>A</li><li>B</li></ul>"
soup = Soup(html)
ul = soup.find("ul")

# append -- add a child at the end
new_li = soup.new_tag("li", {"class": "new"})
new_li.children.append("C")
ul.append(new_li)

# insert -- add a child at a specific position
another = soup.new_tag("li")
another.children.append("Z")
ul.insert(0, another)

# extract -- remove from parent but keep the node intact
removed = ul.children[1].extract()

# replace_with -- swap one node for another
replacement = soup.new_tag("li")
replacement.children.append("X")
ul.children[0].replace_with(replacement)

# unwrap -- remove a tag but keep its children
soup2 = Soup("<div><b>bold text</b></div>")
soup2.find("b").unwrap()
print(soup2.get_text())  # bold text
```

### HTML Serialization

```python
soup = Soup('<div class="box"><p>Hello <b>world</b></p></div>')
div = soup.find("div")
print(div.to_html())
# <div class="box"><p>Hello <b>world</b></p></div>

# str() also produces HTML
print(str(div))
# <div class="box"><p>Hello <b>world</b></p></div>
```

### Attribute Setting

```python
soup = Soup('<a href="/old">Link</a>')
a = soup.find("a")

# Set attribute
a["href"] = "/new"
a["class"] = ["nav", "active"]

# Delete attribute
del a["class"]
print(a.to_html())  # <a href="/new">Link</a>
```

### Creating New Tags

```python
soup = Soup("<div></div>")
tag = soup.new_tag("span", {"id": "greeting"})
tag.children.append("Hello!")
soup.find("div").append(tag)
print(soup.find("div").to_html())
# <div><span id="greeting">Hello!</span></div>
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
| :first-child | `li:first-child` | Match first child element |
| :last-child | `li:last-child` | Match last child element |
| :only-child | `span:only-child` | Match element that is the only child |
| :not() | `li:not(.active)` | Match elements that do NOT match the inner selector |

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
| `append(child)` | Append a child node (Tag or str). |
| `insert(index, child)` | Insert a child at the given position. |
| `extract()` | Remove from parent, return self (keeps children). |
| `replace_with(new_node)` | Replace this node with another in parent's children. |
| `unwrap()` | Remove this tag but keep its children (reparent to parent). |
| `to_html()` | Serialize this element to an HTML string. |

### `Tag` Properties

| Property | Type | Description |
|----------|------|-------------|
| `.text` | `str` | All text content (shortcut for `get_text()`). |
| `.name` | `str` | Tag name (e.g. `"div"`). |
| `.attrs` | `dict` | Attribute dictionary. `class` is stored as a list. |
| `.children` | `list` | Child nodes (`Tag` or `str`). |
| `.parent` | `Tag \| None` | Parent element. |

### `Soup` Factory Methods

| Method | Description |
|--------|-------------|
| `new_tag(name, attrs=None)` | Create a new detached Tag node. |

## Comparison with BeautifulSoup

| Feature | zerodep soup | BeautifulSoup |
|---------|-------------|---------------|
| Dependencies | None (stdlib only) | `soupsieve`, optional `lxml`/`html5lib` |
| Files | Single file | Package (multiple files) |
| Parser backends | `html.parser` only | `html.parser`, `lxml`, `html5lib` |
| find / find_all | Yes | Yes |
| CSS selectors | Tag, class, id, attr, combinators, pseudo-selectors | Full (via soupsieve) |
| Tree mutation (append/insert/extract) | Yes | Yes |
| HTML serialization (to_html) | Yes | Yes (prettify) |
| NavigableString | No (plain `str`) | Yes |
| Parse speed (small) | 149 us | 446 us (2.99x slower) |
| Parse speed (large) | 12.7 ms | 37.1 ms (2.93x slower) |

**When to use zerodep:** You need basic HTML parsing (find, select, get_text) with zero dependencies and fast performance.

**When to use BeautifulSoup:** You need the full CSS selector spec (`:nth-child()`, `:has()`, etc.), multiple parser backends, or NavigableString features.

## Benchmark

Benchmarked against `beautifulsoup4` across small, medium, and large HTML documents.

See [Soup Benchmark](../benchmarks/soup.md) for detailed results.
