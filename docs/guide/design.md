# Design & Architecture

This page explains the architectural thinking behind zerodep: why the repository is structured the way it is, how modules are classified by complexity, and where the project's refactoring efforts stand.

For the project's core values (zero dependencies, single-file modules, correctness-first), see [Design Philosophy](philosophy.md). For the specific cross-module implementation patterns, see [Internal Conventions](internals.md).

## Refactoring Philosophy

zerodep is not a traditional Python package. It does not ship a unified runtime, does not enforce a shared import tree, and does not aim for a single `pip install` entry point. The modules are designed to be copied into other projects and used standalone.

This means the repository does not need — and should not pursue — the kind of refactoring that typical packages undergo: extracting a shared core, building an internal utility layer, or enforcing a common base class hierarchy.

What the repository *does* need is **repo-level standardization**. The codebase is not "bad code." The real issue is that many modules solve the same problems (sibling imports, subprocess execution, color detection, cleanup) using slightly different approaches. The goal of refactoring is not to eliminate this duplication — some duplication is healthy in a single-file architecture — but to make the repeated patterns **predictable**.

!!! note "Guiding principle"
    Standardize patterns at the repository level, but never introduce a shared runtime core that modules must import.

## Core Principles

Four principles guide all refactoring and architectural decisions in zerodep.

### 1. Keep the single-file contract

No module should require importing from a shared internal package. The following are explicitly out of scope:

- Creating a `zerodep/_core` or shared utility layer
- Turning modules into thin wrappers around a common library
- Any change that prevents a copied single file from working independently

### 2. Standardize writing first, abstract later

The highest-priority work is not "eliminate repeated code" but "make repeated code follow the same conventions." Concretely:

- Same problems should use the same structure
- Same capabilities should use the same naming
- Same fallback paths should produce the same error semantics

This reduces maintenance cost without breaking the single-file design.

### 3. Large modules: internal refactoring before cross-module abstractions

For subsystem-scale modules like `httpclient`, `runner`, and `scheduler`, the most valuable refactoring is internal:

- Clearer phase boundaries
- More auditable state machines
- Obvious sync/async correspondence
- More inspectable cleanup paths

Cross-module extraction (shared helpers, common base classes) comes later, if ever.

### 4. Treat repeated patterns as repository assets

The repository explicitly maintains a set of canonical patterns — not as shared code, but as shared conventions:

- Optional sibling import
- Subprocess execution
- Terminal color detection
- Sync/async API mirroring
- Cleanup semantics (three-tier classification)
- Error type design
- Large module internal layering

These are documented in [Internal Conventions](internals.md) and serve as the reference for all contributors.

## Module Complexity Classification

Not all zerodep modules carry the same complexity or maintenance burden. The repository recognizes three tiers.

### Simple utility modules

Small, focused modules that solve one well-bounded problem. They typically have a single entry point, no internal state machine, and minimal error surface.

| Module | Description |
|--------|-------------|
| `ansi` | ANSI terminal color sequences |
| `dotenv` | `.env` file loading |
| `jsonx` | Extended JSON parsing (JSONC + JSONL/NDJSON) |
| `prompt` | Interactive CLI prompts |

### Medium functionality modules

Modules with richer feature sets, multiple entry points, or non-trivial parsing logic. They may involve internal data structures but do not manage long-lived state or concurrent execution.

| Module | Description |
|--------|-------------|
| `markdown` | Markdown-to-HTML rendering |
| `frontmatter` | YAML/TOML/JSON frontmatter extraction |
| `tabulate` | Table formatting for terminal output |
| `validate` | Data validation with type coercion |

### Subsystem modules

Modules that are effectively compressed subsystems: they manage lifecycles, handle concurrency, maintain connection pools, or coordinate multiple internal phases. These modules demand stricter internal structure and more careful review.

| Module | Description |
|--------|-------------|
| `httpclient` | HTTP client with connection pooling, streaming, sync/async |
| `runner` | Subprocess execution with streaming and timeout control |
| `scheduler` | Cron-based task scheduling with thread/async coordination |
| `cache` | Multi-backend caching with TTL and eviction |
| `vcs` | Git operations wrapper with diff integration |
| `yaml` | Full YAML parser and emitter |

This classification helps set expectations: a change to `dotenv` is reviewed differently than a change to `scheduler`.

## Refactoring Roadmap

The refactoring work is organized into three tiers, ordered by risk and impact.

### Tier 1 -- Standardization (completed)

Low-risk, high-reward normalization work. All items in this tier are complete.

| Item | Status | Commits |
|------|--------|---------|
| Pattern inventory documented | Done | `283e7dc` |
| Sibling imports unified across config, vcs, sse | Done | `a196e45` |
| Sibling modules converted to lazy loading | Done | `240d6b5`, `262674a` |
| Terminal color detection aligned across structlog, prompt | Done | `87ef4dc` |
| Cleanup semantics classified into three tiers | Done | -- |

### Tier 2 -- Core module internal refactoring (completed)

Internal structural improvements to the three largest subsystem modules. All items in this tier are complete.

| Item | Status | Commits |
|------|--------|---------|
| runner: section structure + sync/async alignment audit | Done | `0b85cf5` |
| runner: fix async partial output + process reaping gaps | Done | `98d4c8a` |
| scheduler: concurrency model documentation + error conventions | Done | `217833a` |
| scheduler: tighten lock discipline around job state transitions | Done | `116fb9e` |
| httpclient: reorganize internal sections (12-layer structure) | Done | `c8c8d61` |
| httpclient: resolve sync/async drifts + enrich error context | Done | `e9ddf8a` |

### Tier 3 -- Repository governance (completed)

Formalize contributor-facing standards and add edge-behavior test coverage. All items in this tier are complete.

| Item | Status | Commits |
|------|--------|---------|
| Module complexity tier tagged in frontmatter + CLI support | Done | `0f14b6e` |
| Edge-behavior tests: httpclient pool, streaming, timeout (12 tests) | Done | -- |
| Edge-behavior tests: runner timeout, streaming, policy (13 tests) | Done | -- |
| Edge-behavior tests: scheduler shutdown, state safety, events (10 tests) | Done | -- |
| Edge-behavior tests: config sibling import fallback (6 tests) | Done | -- |

## Further Reading

- [Internal Conventions](internals.md) -- the detailed pattern specifications that Tier 1 standardization produced
- [Design Philosophy](philosophy.md) -- the project's core values and when to use (or not use) zerodep
