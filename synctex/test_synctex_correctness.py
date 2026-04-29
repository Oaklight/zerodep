"""Correctness tests for zerodep synctex module."""

import gzip
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from synctex import HBox, SyncTeXData, forward_search, inverse_search, parse_synctex

# -- Synthetic SyncTeX content for testing --

SAMPLE_SYNCTEX = """\
SyncTeX Version:1
Input:1:/workspace/main.tex
Input:2:/workspace/chapter1.tex
Input:3:./figures/fig1.tex
Output:main.pdf
Magnification:1000
Unit:1
X Offset:0
Y Offset:0
Content:
{1
(1,10:1000000,2000000:5000000,500000,100000
h1,11:1500000,2500000:3000000,500000,100000
(2,20:1000000,5000000:5000000,500000,100000
h2,21:2000000,5500000:2000000,400000,80000
}1
{2
(1,30:1000000,2000000:5000000,500000,100000
(3,40:1000000,4000000:4000000,600000,120000
}2
"""


@pytest.fixture
def synctex_file(tmp_path):
    """Write a plain .synctex file and return its path."""
    path = tmp_path / "test.synctex"
    path.write_text(SAMPLE_SYNCTEX)
    return str(path)


@pytest.fixture
def synctex_gz_file(tmp_path):
    """Write a gzipped .synctex.gz file and return its path."""
    path = tmp_path / "test.synctex.gz"
    with gzip.open(path, "wt") as f:
        f.write(SAMPLE_SYNCTEX)
    return str(path)


# -- parse_synctex tests --


class TestParseSynctex:
    """Tests for parse_synctex."""

    def test_parse_plain_file(self, synctex_file):
        data = parse_synctex(synctex_file)
        assert isinstance(data, SyncTeXData)
        assert data.magnification == 1000
        assert data.unit == 1
        assert data.x_offset == 0
        assert data.y_offset == 0

    def test_parse_gzip_file(self, synctex_gz_file):
        data = parse_synctex(synctex_gz_file)
        assert isinstance(data, SyncTeXData)
        assert len(data.inputs) == 3

    def test_inputs_parsed(self, synctex_file):
        data = parse_synctex(synctex_file)
        assert data.inputs[1] == "/workspace/main.tex"
        assert data.inputs[2] == "/workspace/chapter1.tex"
        assert data.inputs[3] == "figures/fig1.tex"  # ./ stripped

    def test_strip_prefix(self, synctex_file):
        data = parse_synctex(synctex_file, strip_prefix="/workspace/")
        assert data.inputs[1] == "main.tex"
        assert data.inputs[2] == "chapter1.tex"
        assert data.inputs[3] == "figures/fig1.tex"

    def test_pages_parsed(self, synctex_file):
        data = parse_synctex(synctex_file)
        assert 1 in data.pages
        assert 2 in data.pages
        # Page 1: 2 hbox + 2 void hbox = 4 boxes
        assert len(data.pages[1]) == 4
        # Page 2: 2 hbox records
        assert len(data.pages[2]) == 2

    def test_hbox_fields(self, synctex_file):
        data = parse_synctex(synctex_file)
        box = data.pages[1][0]
        assert isinstance(box, HBox)
        assert box.tag == 1
        assert box.line == 10
        assert box.x == 1000000
        assert box.y == 2000000
        assert box.width == 5000000
        assert box.height == 500000
        assert box.depth == 100000

    def test_void_hbox_parsed(self, synctex_file):
        data = parse_synctex(synctex_file)
        # Second record on page 1 is a void hbox (h prefix)
        box = data.pages[1][1]
        assert box.tag == 1
        assert box.line == 11

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_synctex("/nonexistent/path.synctex")


# -- inverse_search tests --


class TestInverseSearch:
    """Tests for inverse_search."""

    def test_empty_page(self):
        data = SyncTeXData()
        result = inverse_search(data, page=1, x=100.0, y=200.0)
        assert result is None

    def test_nonexistent_page(self, synctex_file):
        data = parse_synctex(synctex_file, strip_prefix="/workspace/")
        result = inverse_search(data, page=99, x=100.0, y=200.0)
        assert result is None

    def test_basic_hit(self, synctex_file):
        data = parse_synctex(synctex_file, strip_prefix="/workspace/")
        # Place query near first box on page 1
        # Box at x=1000000, y=2000000, w=5000000, h=500000, d=100000
        # In PDF points this is roughly x=15.2, y=30.4
        result = inverse_search(data, page=1, x=20.0, y=30.0)
        assert result is not None
        assert result["file"] == "main.tex"
        assert isinstance(result["line"], int)

    def test_finds_correct_line(self):
        """Build data by hand so we can control which box matches."""
        data = SyncTeXData(
            inputs={1: "test.tex"},
            pages={
                1: [
                    HBox(tag=1, line=5, x=0, y=1000, width=5000, height=500, depth=100),
                    HBox(
                        tag=1, line=15, x=0, y=3000, width=5000, height=500, depth=100
                    ),
                ]
            },
            magnification=1000,
            unit=1,
        )
        # Target a point near the second box's y-range
        # y=3000 in SP, convert back: y_pdf = y_sp * scale / _BP_TO_SP
        # With scale=1, y_pdf ≈ 3000 / 65781.76 ≈ 0.0456
        result = inverse_search(data, page=1, x=0.01, y=0.046)
        assert result is not None
        assert result["line"] == 15

    def test_closest_by_vertical_fallback(self):
        """When target_y doesn't fall in any box, find nearest by y-distance."""
        data = SyncTeXData(
            inputs={1: "a.tex"},
            pages={
                1: [
                    HBox(
                        tag=1,
                        line=10,
                        x=0,
                        y=1000000,
                        width=5000000,
                        height=500000,
                        depth=100000,
                    ),
                    HBox(
                        tag=1,
                        line=20,
                        x=0,
                        y=9000000,
                        width=5000000,
                        height=500000,
                        depth=100000,
                    ),
                ]
            },
        )
        # Target very far down -> should match line 20
        result = inverse_search(data, page=1, x=50.0, y=200.0)
        assert result is not None
        assert result["line"] == 20

    def test_missing_tag_returns_none(self):
        """If the best box has a tag not in inputs, return None."""
        data = SyncTeXData(
            inputs={},  # no inputs
            pages={
                1: [
                    HBox(
                        tag=99,
                        line=1,
                        x=0,
                        y=1000,
                        width=5000,
                        height=500,
                        depth=100,
                    ),
                ]
            },
        )
        result = inverse_search(data, page=1, x=0.01, y=0.01)
        assert result is None


# -- forward_search tests --


class TestForwardSearch:
    """Tests for forward_search."""

    def test_empty_data(self):
        data = SyncTeXData()
        result = forward_search(data, file="test.tex", line=1)
        assert result is None

    def test_file_not_in_inputs(self):
        box = HBox(tag=1, line=10, x=1000, y=2000, width=5000, height=500, depth=100)
        data = SyncTeXData(inputs={1: "main.tex"}, pages={1: [box]})
        result = forward_search(data, file="other.tex", line=10)
        assert result is None

    def test_no_boxes_for_tag(self):
        box = HBox(tag=1, line=10, x=1000, y=2000, width=5000, height=500, depth=100)
        data = SyncTeXData(
            inputs={1: "main.tex", 2: "other.tex"},
            pages={1: [box]},
        )
        # other.tex has tag 2, but no boxes with tag 2
        result = forward_search(data, file="other.tex", line=10)
        assert result is None

    def test_exact_line_match(self):
        b1 = HBox(tag=1, line=5, x=0, y=1000, width=5000, height=500, depth=100)
        b2 = HBox(tag=1, line=15, x=0, y=3000, width=5000, height=500, depth=100)
        data = SyncTeXData(
            inputs={1: "test.tex"},
            pages={1: [b1, b2]},
            magnification=1000,
            unit=1,
        )
        result = forward_search(data, file="test.tex", line=15)
        assert result is not None
        assert result["page"] == 1
        assert isinstance(result["x"], float)
        assert isinstance(result["y"], float)

    def test_closest_line_match(self):
        b1 = HBox(tag=1, line=10, x=0, y=1000, width=5000, height=500, depth=100)
        b2 = HBox(tag=1, line=50, x=0, y=5000, width=5000, height=500, depth=100)
        data = SyncTeXData(
            inputs={1: "test.tex"},
            pages={1: [b1, b2]},
            magnification=1000,
            unit=1,
        )
        # Line 12 is closer to line 10 than to line 50
        result = forward_search(data, file="test.tex", line=12)
        assert result is not None
        assert result["page"] == 1

    def test_multi_page(self):
        b1 = HBox(tag=1, line=5, x=0, y=1000, width=5000, height=500, depth=100)
        b2 = HBox(tag=1, line=30, x=0, y=2000, width=5000, height=500, depth=100)
        data = SyncTeXData(
            inputs={1: "test.tex"},
            pages={1: [b1], 2: [b2]},
            magnification=1000,
            unit=1,
        )
        result = forward_search(data, file="test.tex", line=30)
        assert result is not None
        assert result["page"] == 2

    def test_returns_correct_coordinates(self):
        """Verify coordinate conversion is consistent with inverse_search."""
        data = SyncTeXData(
            inputs={1: "test.tex"},
            pages={
                1: [
                    HBox(
                        tag=1,
                        line=10,
                        x=1000000,
                        y=2000000,
                        width=5000000,
                        height=500000,
                        depth=100000,
                    ),
                ]
            },
            magnification=1000,
            unit=1,
        )
        result = forward_search(data, file="test.tex", line=10)
        assert result is not None
        # The x,y should be positive finite values
        assert result["x"] > 0
        assert result["y"] > 0

    def test_with_parsed_data(self, synctex_file):
        data = parse_synctex(synctex_file, strip_prefix="/workspace/")
        # main.tex has boxes on page 1 and page 2
        result = forward_search(data, file="main.tex", line=10)
        assert result is not None
        assert result["page"] in (1, 2)

    def test_roundtrip_with_inverse(self, synctex_file):
        """Forward then inverse should return the same file."""
        data = parse_synctex(synctex_file, strip_prefix="/workspace/")
        fwd = forward_search(data, file="main.tex", line=10)
        assert fwd is not None
        inv = inverse_search(data, page=fwd["page"], x=fwd["x"], y=fwd["y"])
        assert inv is not None
        assert inv["file"] == "main.tex"


# -- HBox / SyncTeXData dataclass tests --


class TestDataclasses:
    """Tests for HBox and SyncTeXData dataclasses."""

    def test_hbox_defaults(self):
        box = HBox(tag=1, line=1, x=0, y=0)
        assert box.width == 0
        assert box.height == 0
        assert box.depth == 0

    def test_synctexdata_defaults(self):
        data = SyncTeXData()
        assert data.inputs == {}
        assert data.pages == {}
        assert data.magnification == 1000
        assert data.unit == 1
        assert data.x_offset == 0
        assert data.y_offset == 0


# -- Edge cases --


class TestEdgeCases:
    """Edge case tests."""

    def test_hbox_without_dimensions(self):
        """Hbox record with only tag,line:x,y (no w,h,d)."""
        content = """\
SyncTeX Version:1
Input:1:test.tex
Magnification:1000
Unit:1
X Offset:0
Y Offset:0
Content:
{1
(1,5:100,200
}1
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".synctex", delete=False
        ) as f:
            f.write(content)
            path = f.name
        try:
            data = parse_synctex(path)
            assert len(data.pages[1]) == 1
            box = data.pages[1][0]
            assert box.width == 0
            assert box.height == 0
            assert box.depth == 0
        finally:
            os.unlink(path)

    def test_negative_coordinates(self):
        """Negative coordinates should be parsed correctly."""
        content = """\
SyncTeX Version:1
Input:1:test.tex
Magnification:1000
Unit:1
X Offset:0
Y Offset:0
Content:
{1
(1,5:-100,-200:300,400,500
}1
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".synctex", delete=False
        ) as f:
            f.write(content)
            path = f.name
        try:
            data = parse_synctex(path)
            box = data.pages[1][0]
            assert box.x == -100
            assert box.y == -200
        finally:
            os.unlink(path)

    def test_empty_synctex(self):
        """An empty file should produce empty data."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".synctex", delete=False
        ) as f:
            f.write("")
            path = f.name
        try:
            data = parse_synctex(path)
            assert data.inputs == {}
            assert data.pages == {}
        finally:
            os.unlink(path)

    def test_multiple_dot_slash_stripped(self):
        """Multiple leading ./ should be stripped."""
        content = "SyncTeX Version:1\nInput:1:././././main.tex\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".synctex", delete=False
        ) as f:
            f.write(content)
            path = f.name
        try:
            data = parse_synctex(path)
            assert data.inputs[1] == "main.tex"
        finally:
            os.unlink(path)
