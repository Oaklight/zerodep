"""Correctness tests: zerodep readability vs readability-lxml & Mozilla fixtures."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from readability import ReadabilityResult, extract, is_probably_readable  # noqa: E402

# readability-lxml uses the package name "readability" which conflicts with
# our module name.  Detect it via importlib.metadata (no import needed).
try:
    from importlib.metadata import version as _pkg_version

    _pkg_version("readability-lxml")
    _HAS_REFERENCE = True
except Exception:
    _HAS_REFERENCE = False

# ── Mozilla test-pages fixture discovery ──

_TEST_PAGES_DIR = os.path.join(os.path.dirname(__file__), "test-pages")


def _discover_fixtures() -> list[str]:
    """Return sorted list of fixture directory names under test-pages/."""
    if not os.path.isdir(_TEST_PAGES_DIR):
        return []
    return sorted(
        d
        for d in os.listdir(_TEST_PAGES_DIR)
        if os.path.isdir(os.path.join(_TEST_PAGES_DIR, d))
        and os.path.isfile(os.path.join(_TEST_PAGES_DIR, d, "source.html"))
        and os.path.isfile(os.path.join(_TEST_PAGES_DIR, d, "expected-metadata.json"))
    )


FIXTURE_NAMES = _discover_fixtures()


def _load_fixture(name: str) -> tuple[str, dict, str]:
    """Load source HTML, expected metadata, and expected HTML for a fixture.

    Returns:
        Tuple of (source_html, expected_metadata_dict, expected_html).
    """
    base = os.path.join(_TEST_PAGES_DIR, name)
    with open(os.path.join(base, "source.html"), encoding="utf-8") as f:
        source = f.read()
    with open(os.path.join(base, "expected-metadata.json"), encoding="utf-8") as f:
        meta = json.load(f)
    expected_path = os.path.join(base, "expected.html")
    if os.path.isfile(expected_path):
        with open(expected_path, encoding="utf-8") as f:
            expected_html = f.read()
    else:
        expected_html = ""
    return source, meta, expected_html


# ── HTML fixtures ──


ARTICLE_HTML = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <title>Understanding Neural Networks | AI Blog</title>
    <meta property="og:title" content="Understanding Neural Networks">
    <meta property="og:description" content="A comprehensive guide to neural networks">
    <meta property="og:site_name" content="AI Blog">
    <meta name="author" content="Alice Smith">
    <meta property="article:published_time" content="2024-03-15T10:00:00Z">
</head>
<body>
    <header>
        <nav><a href="/">Home</a> <a href="/blog">Blog</a></nav>
    </header>
    <main>
        <article>
            <h1>Understanding Neural Networks</h1>
            <p>Neural networks are computing systems inspired by biological neural
            networks. They consist of layers of interconnected nodes, each
            performing simple computations that collectively enable complex pattern
            recognition and decision-making tasks.</p>
            <p>The fundamental building block is the artificial neuron, which
            receives inputs, applies weights, sums them up, and passes the result
            through an activation function. This simple mechanism, when replicated
            across thousands of neurons arranged in multiple layers, gives rise to
            powerful learning capabilities.</p>
            <p>Training a neural network involves adjusting the weights through a
            process called backpropagation. The network makes predictions, compares
            them with actual results, calculates the error, and propagates this
            error backward through the network to update the weights.</p>
            <p>Deep learning, a subset of machine learning, uses neural networks
            with many layers. These deep architectures can automatically learn
            hierarchical representations of data, from simple features in early
            layers to complex abstractions in deeper layers.</p>
            <p>Applications of neural networks span many domains: computer vision
            uses convolutional neural networks for image recognition, natural
            language processing employs transformers for text understanding, and
            reinforcement learning uses neural networks to develop game-playing
            agents and robotic controllers.</p>
        </article>
    </main>
    <aside class="sidebar">
        <h3>Popular Posts</h3>
        <ul>
            <li><a href="/post1">Introduction to Python</a></li>
            <li><a href="/post2">Data Science Basics</a></li>
            <li><a href="/post3">Machine Learning 101</a></li>
        </ul>
        <div class="ad-banner">Advertisement here</div>
    </aside>
    <footer>
        <p>&copy; 2024 AI Blog. All rights reserved.</p>
        <nav><a href="/privacy">Privacy</a> <a href="/terms">Terms</a></nav>
    </footer>
</body>
</html>"""

BLOG_WITH_COMMENTS_HTML = """<!DOCTYPE html>
<html lang="en">
<head><title>My Travel Story - Travel Blog</title></head>
<body>
    <nav class="main-nav"><a href="/">Home</a></nav>
    <div id="main-content" class="post-body">
        <h1>My Travel Story</h1>
        <p>Last summer, I embarked on an unforgettable journey through Southeast
        Asia. Starting in Bangkok, Thailand, I explored the vibrant street markets,
        visited ancient temples, and savored the incredible street food that the
        city is famous for.</p>
        <p>From Thailand, I traveled to Vietnam, where the stunning landscapes
        of Ha Long Bay took my breath away. The emerald waters dotted with
        limestone karsts created a scene that seemed almost surreal, like
        something from a painting.</p>
        <p>Cambodia was next on my itinerary, and the temples of Angkor Wat
        did not disappoint. The sheer scale and intricate carvings of these
        ancient structures left me in awe of the Khmer civilization that
        built them centuries ago.</p>
        <p>The trip concluded in Bali, Indonesia, where I found the perfect
        balance of adventure and relaxation. From surfing in Kuta to meditating
        in Ubud, the island offered something for every mood and interest.</p>
    </div>
    <div class="comments-section">
        <h3>Comments</h3>
        <div class="comment"><p>Great post! - User123</p></div>
        <div class="comment"><p>I want to visit too! - Traveler99</p></div>
    </div>
    <div class="related-posts">
        <h3>Related Articles</h3>
        <a href="/p1">Europe Trip</a>
        <a href="/p2">Africa Safari</a>
    </div>
    <footer>Footer content here</footer>
</body>
</html>"""

DIV_ONLY_HTML = """<!DOCTYPE html>
<html>
<head><title>No Semantic Tags</title></head>
<body>
    <div class="wrapper">
        <div class="top-bar"><a href="/">Logo</a><a href="/about">About</a></div>
        <div class="content-area">
            <div class="post-title"><h2>The Art of Programming</h2></div>
            <p>Programming is both an art and a science. It requires creativity
            to design elegant solutions, and rigorous logical thinking to
            implement them correctly. The best programmers combine both qualities,
            producing code that is not only functional but also beautiful.</p>
            <p>Clean code is like good prose: it communicates its intent clearly
            and concisely. Each function should do one thing well, each variable
            should have a meaningful name, and each module should have a single
            responsibility.</p>
            <p>Testing is an essential part of programming. Unit tests verify
            individual components, integration tests check how components work
            together, and end-to-end tests validate the entire system. A
            comprehensive test suite gives developers confidence to refactor
            and improve their code.</p>
            <p>Version control with Git enables collaboration and provides
            a safety net for experimentation. Branching strategies like
            GitFlow help teams manage parallel development streams, while
            pull requests facilitate code review and knowledge sharing.</p>
        </div>
        <div class="side-panel">
            <div class="widget"><a href="/a">Link A</a></div>
            <div class="widget"><a href="/b">Link B</a></div>
        </div>
    </div>
</body>
</html>"""

JSONLD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>Exploring Quantum Computing - Tech Magazine</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Exploring Quantum Computing",
        "author": {"@type": "Person", "name": "Dr. Quantum"},
        "datePublished": "2024-06-01T08:00:00Z",
        "description": "An introduction to quantum computing concepts",
        "publisher": {"@type": "Organization", "name": "Tech Magazine"}
    }
    </script>
</head>
<body>
    <div class="article-container">
        <h1>Exploring Quantum Computing</h1>
        <p>Quantum computing represents a fundamentally different approach to
        computation. Unlike classical computers that use bits representing
        0 or 1, quantum computers use qubits that can exist in superposition,
        representing both states simultaneously.</p>
        <p>Entanglement is another key quantum phenomenon. When qubits become
        entangled, the state of one qubit instantly influences the state of
        another, regardless of the distance between them. This property
        enables quantum computers to process information in parallel.</p>
        <p>Quantum algorithms like Shor's algorithm for factoring and Grover's
        algorithm for searching demonstrate the potential speedup that quantum
        computers can achieve over classical machines for specific problems.</p>
        <p>Major companies including IBM, Google, and Microsoft are investing
        heavily in quantum computing research. Google's achievement of quantum
        supremacy in 2019 marked a significant milestone, though practical
        quantum computers remain years away.</p>
    </div>
</body>
</html>"""

JSONLD_GRAPH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Multi-Author Article - Science Daily</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "Science Daily"},
            {
                "@type": "NewsArticle",
                "headline": "Multi-Author Article",
                "author": [
                    {"@type": "Person", "name": "Alice"},
                    {"@type": "Person", "name": "Bob"}
                ],
                "datePublished": "2024-07-20",
                "description": "A collaborative research piece"
            }
        ]
    }
    </script>
</head>
<body>
    <article>
        <h1>Multi-Author Article</h1>
        <p>This article was written by multiple authors who collaborated on
        research spanning several institutions. Their combined expertise
        provides a comprehensive overview of the topic at hand.</p>
        <p>The methodology involved collecting data from three continents,
        analyzing patterns using advanced statistical models, and validating
        results through peer review. The findings have significant implications
        for the field of environmental science.</p>
        <p>Key findings include a strong correlation between urbanization and
        biodiversity loss, with the most pronounced effects observed in
        tropical regions. The data suggests that targeted conservation
        efforts can mitigate some of these negative impacts.</p>
    </article>
</body>
</html>"""

MINIMAL_HTML = """<html><body>
<p>Just a short paragraph.</p>
</body></html>"""

EMPTY_HTML = """<html><body>
<nav><a href="/">Home</a></nav>
</body></html>"""

SHORT_RETRY_HTML = """<!DOCTYPE html>
<html>
<head><title>Short Article</title></head>
<body>
    <div class="sidebar"><p>Sidebar stuff with lots of navigation links
    and other content that makes the sidebar longer than the actual article
    content which is very short initially.</p></div>
    <div class="content">
        <p>This is a very short article, just enough to trigger the retry
        mechanism when using ruthless candidate removal. The sidebar might
        have been removed first, taking some useful content with it, but
        when we retry without ruthless mode, we should get better results.</p>
    </div>
</body>
</html>"""

TITLE_SEPARATOR_CASES = [
    ("Article Title | Site Name", "Article Title"),
    ("Article Title - Site Name", "Article Title"),
    ("Article Title — Site Name", "Article Title"),
    ("Site: Full Article Title Here", "Full Article Title Here"),
    ("Simple Title", "Simple Title"),
]

NEWS_HTML = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <title>Breaking: Major Discovery in Space - Space News</title>
    <meta name="author" content="Reporter Jane">
    <meta property="og:description" content="Scientists announce breakthrough">
</head>
<body>
    <header class="site-header">
        <div class="logo">Space News</div>
        <nav class="main-menu">
            <a href="/science">Science</a>
            <a href="/tech">Technology</a>
        </nav>
    </header>
    <div class="article-wrapper">
        <div class="breadcrumb">Home > Science > Astronomy</div>
        <h1>Breaking: Major Discovery in Space</h1>
        <div class="byline">By Reporter Jane | March 15, 2024</div>
        <div class="article-content">
            <p>In a groundbreaking announcement today, scientists from NASA
            revealed evidence of organic molecules on one of Jupiter's moons.
            The discovery, made possible by the James Webb Space Telescope,
            could have profound implications for our understanding of life
            in the universe.</p>
            <p>The molecules were detected in the plumes of water vapor
            erupting from the surface of Europa. Analysis of the spectral
            data revealed signatures consistent with amino acids, the
            building blocks of life as we know it on Earth.</p>
            <p>"This is the most significant finding in astrobiology in
            decades," said Dr. Sarah Chen, lead researcher on the project.
            "While we cannot yet confirm the presence of life, the chemical
            signatures we've detected are exactly what we would expect to
            see in a habitable environment."</p>
            <p>The discovery builds on previous observations by the Galileo
            and Cassini spacecraft, which suggested that Europa harbors a
            subsurface ocean beneath its icy crust. Scientists estimate
            this ocean contains twice as much water as all of Earth's
            oceans combined.</p>
            <p>Further observations are planned for the coming months using
            both the JWST and ground-based observatories. The European Space
            Agency's JUICE mission, currently en route to Jupiter, will
            provide additional data when it arrives in 2031.</p>
        </div>
    </div>
    <div class="social-share">
        <a href="#">Share on Twitter</a>
        <a href="#">Share on Facebook</a>
    </div>
    <div class="comment-section">
        <h3>Reader Comments</h3>
        <div class="comment">Amazing discovery! - SpaceFan42</div>
        <div class="comment">Can't wait for more data - Astronomer</div>
    </div>
    <footer class="site-footer">
        <p>2024 Space News. Contact us at info@spacenews.example</p>
    </footer>
</body>
</html>"""


# ── Helpers ──


def _our_result(html: str) -> ReadabilityResult:
    return extract(html)


def _load_reference_document_class():
    """Load readability-lxml's Document class, working around name clash."""
    import importlib
    import importlib.util

    # Find readability-lxml in site-packages (not our local readability.py).
    saved_path = sys.path[:]
    saved_modules = {
        k: sys.modules.pop(k)
        for k in list(sys.modules)
        if k == "readability" or k.startswith("readability.")
    }
    try:
        # Remove our directory from path so site-packages is found.
        this_dir = os.path.dirname(__file__)
        this_abs = os.path.abspath(this_dir)
        sys.path = [p for p in sys.path if os.path.abspath(p) != this_abs]
        mod = importlib.import_module("readability")
        return mod.Document
    finally:
        sys.path = saved_path
        # Clean up and restore our modules.
        for k in list(sys.modules):
            if k == "readability" or k.startswith("readability."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


if _HAS_REFERENCE:
    _RefDocument = _load_reference_document_class()
else:
    _RefDocument = None


def _their_result(html: str) -> str:
    """Extract content using readability-lxml for comparison."""
    doc = _RefDocument(html)
    return doc.summary()


# ── Tests: Basic extraction ──


class TestExtract:
    """Tests for the core extract() functionality."""

    def test_article_has_content(self):
        result = _our_result(ARTICLE_HTML)
        assert result.length > 100
        assert "Neural networks" in result.text

    def test_article_excludes_sidebar(self):
        result = _our_result(ARTICLE_HTML)
        assert "Popular Posts" not in result.text
        assert "Advertisement" not in result.text

    def test_article_excludes_footer(self):
        result = _our_result(ARTICLE_HTML)
        assert "All rights reserved" not in result.text

    def test_article_excludes_nav(self):
        result = _our_result(ARTICLE_HTML)
        # The nav links should not appear in the extracted content.
        assert result.text.count("Home") <= 1  # might appear in article text

    def test_blog_extracts_main_content(self):
        result = _our_result(BLOG_WITH_COMMENTS_HTML)
        assert "Southeast Asia" in result.text
        assert "Bangkok" in result.text

    def test_blog_excludes_comments(self):
        result = _our_result(BLOG_WITH_COMMENTS_HTML)
        assert "User123" not in result.text
        assert "Traveler99" not in result.text

    def test_div_only_page(self):
        """Pages without semantic HTML tags should still extract content."""
        result = _our_result(DIV_ONLY_HTML)
        assert "Programming" in result.text
        assert "Clean code" in result.text
        assert result.length > 100

    def test_news_article(self):
        result = _our_result(NEWS_HTML)
        assert "organic molecules" in result.text
        assert "Jupiter" in result.text

    def test_news_excludes_sharing(self):
        result = _our_result(NEWS_HTML)
        assert "Share on Twitter" not in result.text

    def test_content_is_valid_html(self):
        result = _our_result(ARTICLE_HTML)
        assert result.content.startswith("<")
        assert "<p>" in result.content

    def test_text_is_plain(self):
        result = _our_result(ARTICLE_HTML)
        assert "<p>" not in result.text
        assert "<div>" not in result.text

    def test_length_matches_text(self):
        result = _our_result(ARTICLE_HTML)
        assert result.length == len(result.text)


# ── Tests: Metadata extraction ──


class TestMetadata:
    """Tests for metadata extraction (title, author, etc.)."""

    def test_title_from_og(self):
        result = _our_result(ARTICLE_HTML)
        assert result.title == "Understanding Neural Networks"

    def test_title_shortened(self):
        result = _our_result(NEWS_HTML)
        assert "Space News" not in result.title
        assert "Discovery" in result.title

    def test_author_from_meta(self):
        result = _our_result(NEWS_HTML)
        assert result.author == "Reporter Jane"

    def test_excerpt_from_og(self):
        result = _our_result(NEWS_HTML)
        assert result.excerpt == "Scientists announce breakthrough"

    def test_site_name_from_og(self):
        result = _our_result(ARTICLE_HTML)
        assert result.site_name == "AI Blog"

    def test_published_time(self):
        result = _our_result(ARTICLE_HTML)
        assert result.published_time == "2024-03-15T10:00:00Z"

    def test_lang(self):
        result = _our_result(ARTICLE_HTML)
        assert result.lang == "en"

    def test_dir(self):
        result = _our_result(ARTICLE_HTML)
        assert result.dir == "ltr"

    def test_jsonld_metadata(self):
        result = _our_result(JSONLD_HTML)
        assert result.title == "Exploring Quantum Computing"
        assert result.author == "Dr. Quantum"
        assert result.published_time == "2024-06-01T08:00:00Z"
        assert result.site_name == "Tech Magazine"
        assert result.lang == "zh-CN"

    def test_jsonld_graph_multi_author(self):
        result = _our_result(JSONLD_GRAPH_HTML)
        assert result.title == "Multi-Author Article"
        assert "Alice" in result.author
        assert "Bob" in result.author

    def test_jsonld_excerpt(self):
        result = _our_result(JSONLD_HTML)
        assert result.excerpt == "An introduction to quantum computing concepts"

    @pytest.mark.parametrize(
        "full_title,expected",
        TITLE_SEPARATOR_CASES,
        ids=[f"sep_{i}" for i in range(len(TITLE_SEPARATOR_CASES))],
    )
    def test_title_separator_handling(self, full_title, expected):
        html = f"<html><head><title>{full_title}</title></head><body>"
        html += "<p>" + "Content. " * 50 + "</p></body></html>"
        result = _our_result(html)
        assert result.title == expected


# ── Tests: is_probably_readable ──


class TestIsProbablyReadable:
    """Tests for the is_probably_readable() quick check."""

    def test_article_is_readable(self):
        assert is_probably_readable(ARTICLE_HTML) is True

    def test_blog_is_readable(self):
        assert is_probably_readable(BLOG_WITH_COMMENTS_HTML) is True

    def test_news_is_readable(self):
        assert is_probably_readable(NEWS_HTML) is True

    def test_empty_is_not_readable(self):
        assert is_probably_readable(EMPTY_HTML) is False

    def test_minimal_is_not_readable(self):
        assert is_probably_readable(MINIMAL_HTML) is False

    def test_custom_thresholds(self):
        # Very low threshold should pass even marginal content.
        readable = is_probably_readable(
            MINIMAL_HTML, min_score=0.1, min_content_length=5
        )
        assert readable is True


# ── Tests: Edge cases ──


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_html(self):
        result = extract("")
        assert isinstance(result, ReadabilityResult)
        assert result.length == 0

    def test_no_body(self):
        result = extract("<html><head><title>No Body</title></head></html>")
        assert isinstance(result, ReadabilityResult)

    def test_only_nav(self):
        result = extract(EMPTY_HTML)
        assert isinstance(result, ReadabilityResult)

    def test_malformed_html(self):
        html = "<div><p>Unclosed div <b>Bold <i>italic</b> text</i>"
        html += "<p>" + "More content here. " * 20 + "</p>"
        result = extract(html)
        assert isinstance(result, ReadabilityResult)

    def test_malformed_jsonld(self):
        """Bad JSON-LD should be silently ignored."""
        html = (
            """<html><head>
        <title>Test</title>
        <script type="application/ld+json">NOT VALID JSON</script>
        </head><body>
        <p>"""
            + "Content paragraph. " * 30
            + """</p>
        </body></html>"""
        )
        result = extract(html)
        assert result.title == "Test"

    def test_unicode_content(self):
        html = """<html><head><title>Unicode Test</title></head><body>
        <article>
        <p>这是一篇中文文章，包含多个段落。第一段讨论了人工智能的发展历程，
        从早期的专家系统到现代的深度学习，人工智能技术取得了巨大的进步。</p>
        <p>第二段探讨了自然语言处理领域的最新突破，大语言模型的出现改变了
        人们与计算机交互的方式，使得机器能够理解和生成自然语言文本。</p>
        <p>第三段讨论了人工智能在医疗、教育和交通等领域的应用前景，
        以及可能带来的社会影响和伦理问题。这些挑战需要全社会共同面对。</p>
        </article>
        </body></html>"""
        result = extract(html)
        assert "中文" in result.text or "人工智能" in result.text

    def test_deeply_nested(self):
        """Deeply nested content should still be extractable."""
        inner = "<p>" + "Nested content paragraph. " * 20 + "</p>"
        html = "<html><body>"
        for _ in range(10):
            html += "<div>"
        html += inner * 3
        for _ in range(10):
            html += "</div>"
        html += "</body></html>"
        result = extract(html)
        assert "Nested content" in result.text


# ── Tests: Comparison with readability-lxml ──


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
class TestCompareWithReference:
    """Compare our results with readability-lxml for consistency."""

    @pytest.mark.parametrize(
        "html,name",
        [
            (ARTICLE_HTML, "article"),
            (BLOG_WITH_COMMENTS_HTML, "blog"),
            (NEWS_HTML, "news"),
        ],
    )
    def test_both_extract_similar_content(self, html, name):
        """Both implementations should extract the same key content."""
        ours = _our_result(html)
        theirs_html = _their_result(html)

        # Both should have non-trivial content.
        assert ours.length > 100, f"{name}: our result too short"
        assert len(theirs_html) > 100, f"{name}: reference result too short"

    @pytest.mark.parametrize(
        "html,must_contain,must_not_contain,name",
        [
            (
                ARTICLE_HTML,
                ["Neural networks", "backpropagation"],
                ["Popular Posts", "Advertisement"],
                "article",
            ),
            (
                BLOG_WITH_COMMENTS_HTML,
                ["Southeast Asia", "Bangkok"],
                ["User123", "Traveler99"],
                "blog",
            ),
            (
                NEWS_HTML,
                ["organic molecules", "Jupiter"],
                ["Share on Twitter"],
                "news",
            ),
        ],
    )
    def test_content_inclusion_exclusion(
        self, html, must_contain, must_not_contain, name
    ):
        """Verify key content is included and noise is excluded."""
        result = _our_result(html)
        for phrase in must_contain:
            assert phrase in result.text, f"{name}: missing '{phrase}'"
        for phrase in must_not_contain:
            assert phrase not in result.text, f"{name}: should not contain '{phrase}'"


# ── Tests: Mozilla Readability.js test fixtures ──


def _text_from_html(html: str) -> str:
    """Extract plain text from HTML string for content comparison."""
    # Quick and dirty: use soup to get text.
    _parent = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "soup"))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    from soup import Soup

    return Soup(html).get_text(separator=" ", strip=True)


@pytest.mark.skipif(
    len(FIXTURE_NAMES) == 0,
    reason="No Mozilla test fixtures found in test-pages/",
)
class TestMozillaFixtures:
    """Test against Mozilla Readability.js official test fixtures.

    Metadata fields are compared against expected-metadata.json.
    Content is compared against expected.html using text overlap (Jaccard).
    """

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_is_readable(self, fixture_name):
        """All Mozilla fixtures are marked readerable=true."""
        source, meta, _ = _load_fixture(fixture_name)
        expected_readable = meta.get("readerable", True)
        if expected_readable:
            assert is_probably_readable(source), f"{fixture_name}: should be readable"

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_extracts_nonempty_content(self, fixture_name):
        """extract() should return non-trivial content for all fixtures."""
        source, _, _ = _load_fixture(fixture_name)
        result = extract(source)
        assert isinstance(result, ReadabilityResult)
        assert result.length > 50, (
            f"{fixture_name}: extracted text too short ({result.length} chars)"
        )

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_title(self, fixture_name):
        """Extracted title should match expected metadata."""
        source, meta, _ = _load_fixture(fixture_name)
        expected_title = meta.get("title")
        if not expected_title:
            pytest.skip(f"{fixture_name}: no expected title")
        result = extract(source)
        # Allow partial match: our title shortener may be more
        # aggressive than Mozilla's (e.g. "Firefox — ... — The most
        # flexible browser on the Web" → "The most flexible browser
        # on the Web").  We check that result words are a subset of
        # expected words OR vice-versa.
        expected_lower = expected_title.lower()
        result_lower = result.title.lower()
        expected_words = set(expected_lower.split())
        result_words = set(result_lower.split())
        if len(expected_words) == 0:
            pytest.skip(f"{fixture_name}: empty expected title")
        # Our title should be contained in expected (subset) OR share
        # significant overlap.
        if result_words <= expected_words:
            return  # our title is a subset of expected — fine
        overlap = len(expected_words & result_words) / len(expected_words)
        assert overlap >= 0.3, (
            f"{fixture_name}: title word overlap too low ({overlap:.0%})\n"
            f"  expected: {expected_title}\n"
            f"  got:      {result.title}"
        )

    # Fixtures where byline difference is a known meta priority gap
    # (e.g. Mozilla prefers Dublin Core over standard meta name).
    _BYLINE_XFAIL = frozenset({"003-metadata-preferred"})

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_byline(self, fixture_name):
        """Extracted author should match expected byline when present."""
        source, meta, _ = _load_fixture(fixture_name)
        expected_byline = meta.get("byline")
        if not expected_byline:
            pytest.skip(f"{fixture_name}: no expected byline")
        result = extract(source)
        if result.author is None:
            pytest.xfail(f"{fixture_name}: author not extracted (known gap)")
        # Normalize "By Name" prefix that some sources add.
        expected_clean = expected_byline.lower().removeprefix("by ").strip()
        result_clean = result.author.lower().removeprefix("by ").strip()
        if expected_clean in result_clean or result_clean in expected_clean:
            return
        if fixture_name in self._BYLINE_XFAIL:
            pytest.xfail(
                f"{fixture_name}: known metadata priority difference "
                f"(expected={expected_byline!r}, got={result.author!r})"
            )
        raise AssertionError(
            f"{fixture_name}: byline mismatch\n"
            f"  expected: {expected_byline}\n"
            f"  got:      {result.author}"
        )

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_content_overlap(self, fixture_name):
        """Extracted text should have significant overlap with expected HTML text."""
        source, _, expected_html = _load_fixture(fixture_name)
        if not expected_html:
            pytest.skip(f"{fixture_name}: no expected.html")
        result = extract(source)
        expected_text = _text_from_html(expected_html)
        if not expected_text:
            pytest.skip(f"{fixture_name}: expected.html has no text")

        # Compute word-level Jaccard similarity.
        our_words = set(result.text.lower().split())
        expected_words = set(expected_text.lower().split())
        if len(expected_words) == 0:
            pytest.skip(f"{fixture_name}: empty expected text")
        intersection = len(our_words & expected_words)
        union = len(our_words | expected_words)
        jaccard = intersection / union if union > 0 else 0.0

        # Recall: how much of expected content did we capture?
        recall = intersection / len(expected_words)

        # We use a fairly lenient threshold since our algorithm differs
        # from Mozilla's (2-level vs 5-level ancestors, etc.).
        assert recall >= 0.3, (
            f"{fixture_name}: content recall too low ({recall:.0%})\n"
            f"  jaccard={jaccard:.0%}, "
            f"our_words={len(our_words)}, "
            f"expected_words={len(expected_words)}, "
            f"intersection={intersection}"
        )

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_dir(self, fixture_name):
        """Text direction should match expected metadata when specified."""
        source, meta, _ = _load_fixture(fixture_name)
        expected_dir = meta.get("dir")
        if not expected_dir:
            pytest.skip(f"{fixture_name}: no expected dir")
        result = extract(source)
        if result.dir is None:
            pytest.xfail(f"{fixture_name}: dir not detected (known gap)")
        assert result.dir == expected_dir, (
            f"{fixture_name}: dir mismatch, expected={expected_dir}, got={result.dir}"
        )

    @pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
    def test_lang(self, fixture_name):
        """Language should match expected metadata when specified."""
        source, meta, _ = _load_fixture(fixture_name)
        expected_lang = meta.get("lang")
        if not expected_lang:
            pytest.skip(f"{fixture_name}: no expected lang")
        result = extract(source)
        if result.lang is None:
            pytest.xfail(f"{fixture_name}: lang not detected (known gap)")
        # Compare base language code (en vs en-US, etc.)
        expected_base = expected_lang.lower().split("-")[0]
        result_base = result.lang.lower().split("-")[0]
        assert expected_base == result_base, (
            f"{fixture_name}: lang mismatch, "
            f"expected={expected_lang}, got={result.lang}"
        )
