"""Correctness tests: zerodep skills."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from skills import (
    BM25Selector,
    KeywordSelector,
    ParseError,
    SelectionResult,
    Selector,
    SkillProperties,
    SkillRegistry,
    compose,
    discover,
    load,
    loads,
    to_catalog,
    validate,
)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

SIMPLE_SKILL_MD = """\
---
name: pdf-processing
description: Extract text and metadata from PDF files
---
# PDF Processing

When the user asks about PDF files, use this skill.

1. Read the PDF using the appropriate tool.
2. Extract text content.
3. Return formatted results.
"""

FULL_SKILL_MD = """\
---
name: code-review
description: Review code for bugs, style issues, and security vulnerabilities
license: MIT
compatibility: Requires Bash and Read tools
allowed-tools: Bash(git:*) Read
metadata:
  author: test-org
  version: "1.0"
---
# Code Review Skill

Carefully review the code changes.
"""

NO_FRONTMATTER = """\
# Just Markdown

No frontmatter here.
"""

MISSING_NAME = """\
---
description: A skill without a name
---
Instructions here.
"""

MISSING_DESCRIPTION = """\
---
name: missing-desc
---
Instructions here.
"""


# ---------------------------------------------------------------------------
# SkillProperties
# ---------------------------------------------------------------------------


class TestSkillProperties:
    def test_to_dict_minimal(self):
        props = SkillProperties(name="test-skill", description="A test skill")
        d = props.to_dict()
        assert d == {"name": "test-skill", "description": "A test skill"}
        assert "license" not in d
        assert "metadata" not in d

    def test_to_dict_full(self):
        props = SkillProperties(
            name="test-skill",
            description="A test skill",
            license="MIT",
            compatibility="Python 3.10+",
            allowed_tools="Bash Read",
            metadata={"author": "me"},
        )
        d = props.to_dict()
        assert d["name"] == "test-skill"
        assert d["license"] == "MIT"
        assert d["compatibility"] == "Python 3.10+"
        assert d["allowed-tools"] == "Bash Read"
        assert d["metadata"] == {"author": "me"}

    def test_to_dict_empty_metadata_excluded(self):
        props = SkillProperties(name="x", description="y", metadata={})
        d = props.to_dict()
        assert "metadata" not in d


# ---------------------------------------------------------------------------
# Skill parsing
# ---------------------------------------------------------------------------


class TestSkillParsing:
    def test_loads_simple(self):
        skill = loads(SIMPLE_SKILL_MD)
        assert skill.name == "pdf-processing"
        assert skill.description == "Extract text and metadata from PDF files"
        assert "PDF Processing" in skill.instructions
        assert skill.path is None

    def test_loads_full(self):
        skill = loads(FULL_SKILL_MD)
        assert skill.name == "code-review"
        assert skill.properties.license == "MIT"
        assert skill.properties.compatibility == "Requires Bash and Read tools"
        assert skill.properties.allowed_tools == "Bash(git:*) Read"
        assert skill.properties.metadata == {"author": "test-org", "version": "1.0"}

    def test_loads_no_frontmatter_raises(self):
        with pytest.raises(ParseError):
            loads(NO_FRONTMATTER)

    def test_loads_missing_name_raises(self):
        with pytest.raises(ParseError, match="name"):
            loads(MISSING_NAME)

    def test_loads_missing_description_raises(self):
        with pytest.raises(ParseError, match="description"):
            loads(MISSING_DESCRIPTION)

    def test_load_from_directory(self, tmp_path):
        skill_dir = tmp_path / "pdf-processing"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "extract.py").write_text("# script", encoding="utf-8")

        skill = load(skill_dir)
        assert skill.name == "pdf-processing"
        assert skill.path == skill_dir
        assert len(skill.scripts) == 1
        assert skill.scripts[0].name == "extract.py"
        assert skill.references == []
        assert skill.assets == []

    def test_load_from_file(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        skill = load(skill_md)
        assert skill.name == "pdf-processing"
        assert skill.path == skill_dir

    def test_load_case_insensitive(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "skill.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        skill = load(skill_dir)
        assert skill.name == "pdf-processing"


# ---------------------------------------------------------------------------
# Skill output
# ---------------------------------------------------------------------------


class TestSkillOutput:
    def test_describe(self):
        skill = loads(SIMPLE_SKILL_MD)
        desc = skill.describe()
        assert "pdf-processing" in desc
        assert "Extract text" in desc

    def test_to_dict(self):
        skill = loads(SIMPLE_SKILL_MD)
        d = skill.to_dict()
        assert d["name"] == "pdf-processing"
        assert "instructions" in d
        assert "path" not in d  # no path when parsed from text

    def test_to_prompt(self):
        skill = loads(SIMPLE_SKILL_MD)
        prompt = skill.to_prompt()
        assert '<skill_content name="pdf-processing">' in prompt
        assert "PDF Processing" in prompt
        assert "</skill_content>" in prompt

    def test_to_prompt_with_resources(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "run.sh").write_text("#!/bin/bash", encoding="utf-8")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "guide.md").write_text("# Guide", encoding="utf-8")

        skill = load(skill_dir)
        prompt = skill.to_prompt()
        assert "<skill_resources>" in prompt
        assert "<file>scripts/run.sh</file>" in prompt
        assert "<file>references/guide.md</file>" in prompt

    def test_repr(self):
        skill = loads(SIMPLE_SKILL_MD)
        r = repr(skill)
        assert "pdf-processing" in r


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_skill(self, tmp_path):
        skill_dir = tmp_path / "pdf-processing"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        problems = validate(skill_dir)
        assert problems == []

    def test_missing_skill_md(self, tmp_path):
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()

        problems = validate(skill_dir)
        assert any("SKILL.md" in p for p in problems)

    def test_name_too_long(self, tmp_path):
        long_name = "a" * 65
        skill_dir = tmp_path / long_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {long_name}\ndescription: test\n---\n", encoding="utf-8"
        )

        problems = validate(skill_dir)
        assert any("64" in p for p in problems)

    def test_name_not_kebab_case(self, tmp_path):
        skill_dir = tmp_path / "BadName"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: BadName\ndescription: test\n---\n", encoding="utf-8"
        )

        problems = validate(skill_dir)
        assert any("kebab-case" in p for p in problems)

    def test_name_mismatch(self, tmp_path):
        skill_dir = tmp_path / "wrong-dir"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        problems = validate(skill_dir)
        assert any("does not match" in p for p in problems)

    def test_unknown_field(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: test\ncustom-field: value\n---\n",
            encoding="utf-8",
        )

        problems = validate(skill_dir)
        assert any("Unknown" in p for p in problems)

    def test_description_too_long(self, tmp_path):
        long_desc = "x" * 1025
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: test-skill\ndescription: {long_desc}\n---\n",
            encoding="utf-8",
        )

        problems = validate(skill_dir)
        assert any("1024" in p for p in problems)

    def test_not_a_directory(self, tmp_path):
        problems = validate(tmp_path / "nonexistent")
        assert any("Not a directory" in p for p in problems)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestSkillRegistry:
    def test_register_and_get(self):
        registry = SkillRegistry()
        skill = loads(SIMPLE_SKILL_MD)
        registry.register(skill)

        assert len(registry) == 1
        assert "pdf-processing" in registry
        assert registry.get("pdf-processing") is skill

    def test_register_duplicate_raises(self):
        registry = SkillRegistry()
        skill = loads(SIMPLE_SKILL_MD)
        registry.register(skill)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(skill)

    def test_unregister(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        registry.unregister("pdf-processing")
        assert len(registry) == 0

    def test_unregister_not_found(self):
        registry = SkillRegistry()
        with pytest.raises(KeyError):
            registry.unregister("nonexistent")

    def test_get_not_found(self):
        registry = SkillRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        registry.register(loads(FULL_SKILL_MD))
        assert len(registry.list()) == 2

    def test_iter(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        skills = list(registry)
        assert len(skills) == 1

    def test_discover(self, tmp_path):
        # Create two skill directories
        skill_data = [
            ("pdf-processing", SIMPLE_SKILL_MD),
            ("code-review", FULL_SKILL_MD),
        ]
        for sname, md in skill_data:
            d = tmp_path / sname
            d.mkdir()
            (d / "SKILL.md").write_text(md, encoding="utf-8")

        # Also create a non-skill directory
        (tmp_path / "not-a-skill").mkdir()

        registry = SkillRegistry()
        found = registry.discover(tmp_path)
        assert len(found) == 2
        assert len(registry) == 2
        names = {s.name for s in found}
        assert "pdf-processing" in names
        assert "code-review" in names

    def test_discover_skips_already_registered(self, tmp_path):
        d = tmp_path / "pdf-processing"
        d.mkdir()
        (d / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        registry = SkillRegistry()
        registry.discover(tmp_path)
        found2 = registry.discover(tmp_path)
        assert len(found2) == 0
        assert len(registry) == 1

    def test_discover_nonexistent_path(self):
        registry = SkillRegistry()
        found = registry.discover("/nonexistent/path")
        assert found == []

    def test_repr(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        r = repr(registry)
        assert "pdf-processing" in r


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


class TestKeywordSelector:
    def _make_skills(self):
        skills = [
            loads(SIMPLE_SKILL_MD),
            loads(FULL_SKILL_MD),
        ]
        return skills

    def test_basic_selection(self):
        skills = self._make_skills()
        selector = KeywordSelector()
        results = selector.select("PDF extract text", skills, top_k=5)
        assert len(results) > 0
        assert results[0].skill.name == "pdf-processing"

    def test_code_review_match(self):
        skills = self._make_skills()
        selector = KeywordSelector()
        results = selector.select("review code bugs security", skills, top_k=5)
        assert len(results) > 0
        assert results[0].skill.name == "code-review"

    def test_no_match(self):
        skills = self._make_skills()
        selector = KeywordSelector()
        results = selector.select("zzzzz qqqqq", skills, top_k=5)
        assert results == []

    def test_empty_query(self):
        skills = self._make_skills()
        selector = KeywordSelector()
        results = selector.select("", skills, top_k=5)
        assert results == []

    def test_top_k_limit(self):
        skills = self._make_skills()
        selector = KeywordSelector()
        results = selector.select("the", skills, top_k=1)
        assert len(results) <= 1


class TestBM25Selector:
    def test_basic_selection(self):
        try:
            selector = BM25Selector()
        except ImportError:
            pytest.skip("search module not available")

        skills = [loads(SIMPLE_SKILL_MD), loads(FULL_SKILL_MD)]
        results = selector.select("PDF extract text", skills, top_k=5)
        assert len(results) > 0
        assert results[0].skill.name == "pdf-processing"

    def test_code_review_match(self):
        try:
            selector = BM25Selector()
        except ImportError:
            pytest.skip("search module not available")

        skills = [loads(SIMPLE_SKILL_MD), loads(FULL_SKILL_MD)]
        results = selector.select("review code bugs", skills, top_k=5)
        assert len(results) > 0
        assert results[0].skill.name == "code-review"


class TestRegistrySelect:
    def test_select_default_selector(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        registry.register(loads(FULL_SKILL_MD))

        results = registry.select("PDF files")
        assert len(results) > 0
        assert isinstance(results[0], SelectionResult)

    def test_select_with_custom_selector(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))

        class AlwaysMatch:
            def select(self, query, skills, top_k):
                return [SelectionResult(skill=s, score=1.0) for s in skills[:top_k]]

        results = registry.select("anything", selector=AlwaysMatch())
        assert len(results) == 1
        assert results[0].score == 1.0

    def test_select_empty_registry(self):
        registry = SkillRegistry()
        results = registry.select("query")
        assert results == []

    def test_selector_protocol(self):
        assert isinstance(KeywordSelector(), Selector)


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------


class TestPromptGeneration:
    def test_to_catalog(self):
        skills = [loads(SIMPLE_SKILL_MD), loads(FULL_SKILL_MD)]
        xml = to_catalog(skills)
        assert "<available_skills>" in xml
        assert "</available_skills>" in xml
        assert "<name>pdf-processing</name>" in xml
        assert "<name>code-review</name>" in xml
        assert "<description>" in xml

    def test_to_catalog_empty(self):
        xml = to_catalog([])
        assert "<available_skills>" in xml
        assert "</available_skills>" in xml

    def test_to_catalog_with_path(self, tmp_path):
        skill_dir = tmp_path / "pdf-processing"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")
        skill = load(skill_dir)
        xml = to_catalog([skill])
        assert "<location>" in xml

    def test_compose(self):
        skills = [loads(SIMPLE_SKILL_MD), loads(FULL_SKILL_MD)]
        result = compose(*skills)
        assert '<skill_content name="pdf-processing">' in result
        assert '<skill_content name="code-review">' in result
        assert "</skill_content>" in result

    def test_registry_to_catalog(self):
        registry = SkillRegistry()
        registry.register(loads(SIMPLE_SKILL_MD))
        xml = registry.to_catalog()
        assert "<name>pdf-processing</name>" in xml

    def test_registry_to_catalog_subset(self):
        registry = SkillRegistry()
        s1 = loads(SIMPLE_SKILL_MD)
        s2 = loads(FULL_SKILL_MD)
        registry.register(s1)
        registry.register(s2)
        xml = registry.to_catalog(skills=[s1])
        assert "<name>pdf-processing</name>" in xml
        assert "code-review" not in xml


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


class TestConvenience:
    def test_discover_function(self, tmp_path):
        d = tmp_path / "pdf-processing"
        d.mkdir()
        (d / "SKILL.md").write_text(SIMPLE_SKILL_MD, encoding="utf-8")

        found = discover(tmp_path)
        assert len(found) == 1
        assert found[0].name == "pdf-processing"

    def test_html_escaping_in_catalog(self):
        md = '---\nname: test-skill\ndescription: Use <script> & "quotes"\n---\nBody.\n'
        skill = loads(md)
        xml = to_catalog([skill])
        assert "&lt;script&gt;" in xml
        assert "&amp;" in xml
        assert "&quot;" in xml
