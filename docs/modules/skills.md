# Agent Skills Runtime

Agent Skills runtime — zero dependencies, stdlib only, Python 3.10+.

## Overview

A lightweight runtime for the [Agent Skills](https://agentskills.io) specification. Parse, discover, manage, and select Agent Skills programmatically. Designed for agent harness developers who need to integrate the Skills ecosystem into custom agent applications.

| File | Description | Dependencies |
|------|-------------|--------------|
| `skills.py` | Agent Skills runtime | `frontmatter` (sibling), `search` (sibling, optional) |

**Key capabilities:**

- Parse and validate `SKILL.md` files per the agentskills.io spec
- Discover skills from directory trees
- Register and manage skills in a registry
- Pre-filter skills by query relevance (pluggable selectors)
- Generate system prompt XML (catalog and activation formats)

## How to Use in Your Project

Copy the single `.py` file (and its sibling dependencies) into your project:

```bash
# Required
cp skills/skills.py your_project/
cp frontmatter/frontmatter.py your_project/
cp yaml/yaml.py your_project/

# Optional (for BM25-based selection)
cp search/sparse_search.py your_project/
```

Or install via the CLI:

```bash
zerodep add skills
```

Then import directly:

```python
from skills import Skill, SkillRegistry, load, loads, validate, to_catalog
```

## Usage Examples

### Parse a Skill

```python
from skills import load, loads

# From a directory
skill = load("path/to/my-skill")
print(skill.name)           # "my-skill"
print(skill.description)    # "What this skill does"
print(skill.instructions)   # Full markdown body

# From text
skill = loads("""---
name: pdf-processing
description: Extract text from PDF files
---
# PDF Processing

When the user asks about PDFs, use this skill.
""")
```

### Discover and Register Skills

```python
from skills import SkillRegistry

registry = SkillRegistry()

# Scan standard Agent Skills directories
registry.discover(
    "~/.agents/skills",       # User-level skills
    ".agents/skills",         # Project-level skills
)

print(f"Found {len(registry)} skills")
for skill in registry:
    print(f"  - {skill.name}: {skill.description}")
```

### Pre-Filter Skills (Save Tokens)

```python
from skills import SkillRegistry, to_catalog

registry = SkillRegistry()
registry.discover("~/.agents/skills")

# Pre-filter: 100 skills -> top 10 most relevant
matches = registry.select("convert this PDF to markdown", top_k=10)
shortlist = [m.skill for m in matches]

# Only inject filtered catalog into system prompt (saves tokens)
catalog_xml = to_catalog(shortlist)

# LLM sees the reduced catalog and decides which skill to activate
```

### Custom Selector

```python
from skills import Selector, SelectionResult, Skill

class EmbeddingSelector:
    """Custom selector using sentence embeddings."""

    def __init__(self, model_name: str):
        # Initialize your embedding model
        ...

    def select(
        self, query: str, skills: list[Skill], top_k: int
    ) -> list[SelectionResult]:
        # Your embedding-based ranking logic
        ...

# Use it
results = registry.select("query", selector=EmbeddingSelector("bge-m3"))
```

### Validate a Skill

```python
from skills import validate

problems = validate("path/to/my-skill")
if problems:
    print("Validation failed:")
    for p in problems:
        print(f"  - {p}")
else:
    print("Skill is valid!")
```

### Generate Prompts

```python
from skills import load, to_catalog, compose

skill_a = load("skills/pdf-processing")
skill_b = load("skills/code-review")

# Level 1: Catalog XML (name + description for all skills)
catalog = to_catalog([skill_a, skill_b])
# <available_skills>
# <skill><name>pdf-processing</name>...</skill>
# <skill><name>code-review</name>...</skill>
# </available_skills>

# Level 2: Activation prompt (full instructions for selected skill)
prompt = skill_a.to_prompt()
# <skill_content name="pdf-processing">
# [full markdown instructions]
# <skill_resources>
# <file>scripts/extract.py</file>
# </skill_resources>
# </skill_content>

# Compose multiple skills
combined = compose(skill_a, skill_b)
```

## Progressive Disclosure

Following the Agent Skills spec, this module supports three levels of progressive disclosure:

| Level | Content | Token Cost | Method |
|-------|---------|------------|--------|
| 1. Catalog | name + description | ~50-100/skill | `to_catalog()` |
| 2. Instructions | Full SKILL.md body | <5000/skill | `skill.to_prompt()` |
| 3. Resources | scripts/, references/ | On demand | `skill.scripts`, `skill.references` |

## Built-in Selectors

| Selector | Description | Dependencies |
|----------|-------------|--------------|
| `KeywordSelector` | Token overlap on name + description | None (stdlib only) |
| `BM25Selector` | BM25 ranking on full skill content | Sibling `search` module |

Implement the `Selector` protocol to create custom selectors (embedding-based, reranker, LLM-based, etc.).

## API Reference

See the [API Reference](../api/skills.md) for full function signatures and docstrings.

## Benchmark

No benchmark is provided for this module. As a utility module implementing the Agent Skills spec with no direct third-party counterpart for performance comparison, benchmarking is not applicable -- see [Skills Benchmark](../benchmarks/skills.md) for details.
