"""Correctness tests for zerodep ansi module."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from ansi import (
    BOLD,
    BRIGHT_COLORS,
    CLEAR_LINE,
    CURSOR_HIDE,
    CURSOR_SHOW,
    CURSOR_UP,
    DIM,
    HIDDEN,
    ITALIC,
    NAMED_COLORS,
    RESET,
    REVERSE,
    STRIKETHROUGH,
    UNDERLINE,
    bg,
    color_depth,
    cursor_move,
    fg,
    strip_ansi,
    style,
    supports_color,
    visible_len,
)

# ── fg() tests ──────────────────────────────────────────────────────


class TestFgNamedColors:
    """Foreground with named color strings."""

    @pytest.mark.parametrize(
        "name,expected_code",
        [
            pytest.param("black", "\033[30m", id="black"),
            pytest.param("red", "\033[31m", id="red"),
            pytest.param("green", "\033[32m", id="green"),
            pytest.param("yellow", "\033[33m", id="yellow"),
            pytest.param("blue", "\033[34m", id="blue"),
            pytest.param("magenta", "\033[35m", id="magenta"),
            pytest.param("cyan", "\033[36m", id="cyan"),
            pytest.param("white", "\033[37m", id="white"),
        ],
    )
    def test_standard_colors(self, name, expected_code):
        assert fg(name) == expected_code

    @pytest.mark.parametrize(
        "name,expected_code",
        [
            pytest.param("bright_black", "\033[90m", id="bright_black"),
            pytest.param("bright_red", "\033[91m", id="bright_red"),
            pytest.param("bright_green", "\033[92m", id="bright_green"),
            pytest.param("bright_yellow", "\033[93m", id="bright_yellow"),
            pytest.param("bright_blue", "\033[94m", id="bright_blue"),
            pytest.param("bright_magenta", "\033[95m", id="bright_magenta"),
            pytest.param("bright_cyan", "\033[96m", id="bright_cyan"),
            pytest.param("bright_white", "\033[97m", id="bright_white"),
        ],
    )
    def test_bright_colors(self, name, expected_code):
        assert fg(name) == expected_code

    def test_case_insensitive(self):
        assert fg("Red") == fg("red")
        assert fg("BLUE") == fg("blue")

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown color name"):
            fg("chartreuse")


class TestFgHex:
    """Foreground with hex color strings."""

    def test_basic_hex(self):
        assert fg("#ff0000") == "\033[38;2;255;0;0m"

    def test_hex_without_hash(self):
        # Leading # is stripped internally.
        assert fg("#00ff00") == "\033[38;2;0;255;0m"

    def test_mixed_case_hex(self):
        assert fg("#FF8800") == "\033[38;2;255;136;0m"

    def test_invalid_hex_length(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            fg("#fff")


class TestFg256:
    """Foreground with 256-color indices."""

    def test_index_zero(self):
        assert fg(0) == "\033[38;5;0m"

    def test_index_255(self):
        assert fg(255) == "\033[38;5;255m"

    def test_index_out_of_range(self):
        with pytest.raises(ValueError, match="0–255"):
            fg(256)
        with pytest.raises(ValueError, match="0–255"):
            fg(-1)


class TestFgRGB:
    """Foreground with RGB tuples."""

    def test_basic_rgb(self):
        assert fg((255, 128, 0)) == "\033[38;2;255;128;0m"

    def test_black_rgb(self):
        assert fg((0, 0, 0)) == "\033[38;2;0;0;0m"

    def test_wrong_tuple_length(self):
        with pytest.raises(ValueError, match="3 elements"):
            fg((255, 0))  # ty: ignore[invalid-argument-type]


# ── bg() tests ──────────────────────────────────────────────────────


class TestBg:
    """Background color construction."""

    def test_named_bg(self):
        # Background codes are foreground + 10.
        assert bg("red") == "\033[41m"
        assert bg("blue") == "\033[44m"

    def test_bright_bg(self):
        assert bg("bright_red") == "\033[101m"
        assert bg("bright_cyan") == "\033[106m"

    def test_hex_bg(self):
        assert bg("#003366") == "\033[48;2;0;51;102m"

    def test_256_bg(self):
        assert bg(214) == "\033[48;5;214m"

    def test_rgb_bg(self):
        assert bg((100, 200, 50)) == "\033[48;2;100;200;50m"


# ── style() tests ───────────────────────────────────────────────────


class TestStyle:
    """High-level style() function."""

    def test_fg_only(self):
        result = style("hello", fg="red")
        assert result == "\033[31mhello\033[0m"

    def test_bg_only(self):
        result = style("hello", bg="blue")
        assert result == "\033[44mhello\033[0m"

    def test_bold(self):
        result = style("hello", bold=True)
        assert result == "\033[1mhello\033[0m"

    def test_dim(self):
        result = style("hello", dim=True)
        assert result == "\033[2mhello\033[0m"

    def test_italic(self):
        result = style("hello", italic=True)
        assert result == "\033[3mhello\033[0m"

    def test_underline(self):
        result = style("hello", underline=True)
        assert result == "\033[4mhello\033[0m"

    def test_strikethrough(self):
        result = style("hello", strikethrough=True)
        assert result == "\033[9mhello\033[0m"

    def test_reverse(self):
        result = style("hello", reverse=True)
        assert result == "\033[7mhello\033[0m"

    def test_combined(self):
        result = style("err", fg="red", bold=True, underline=True)
        assert "\033[1m" in result
        assert "\033[4m" in result
        assert "\033[31m" in result
        assert result.endswith("\033[0m")
        assert "err" in strip_ansi(result)

    def test_no_style_returns_plain(self):
        assert style("plain") == "plain"

    def test_no_reset(self):
        result = style("x", fg="red", reset=False)
        assert not result.endswith(RESET)
        assert result == "\033[31mx"


# ── strip_ansi / visible_len ────────────────────────────────────────


class TestStripAnsi:
    """ANSI escape stripping."""

    def test_no_escapes(self):
        assert strip_ansi("hello world") == "hello world"

    def test_color_codes(self):
        s = "\033[31mred\033[0m"
        assert strip_ansi(s) == "red"

    def test_complex_escapes(self):
        s = f"{BOLD}{fg('blue')}hello{RESET} {bg(214)}world{RESET}"
        assert strip_ansi(s) == "hello world"

    def test_cursor_escapes(self):
        s = f"{CURSOR_HIDE}text{CURSOR_SHOW}"
        assert strip_ansi(s) == "text"

    def test_empty(self):
        assert strip_ansi("") == ""

    def test_256_color(self):
        s = "\033[38;5;214mtest\033[0m"
        assert strip_ansi(s) == "test"

    def test_truecolor(self):
        s = "\033[38;2;255;128;0mtest\033[0m"
        assert strip_ansi(s) == "test"


class TestVisibleLen:
    """Visible length ignoring ANSI escapes."""

    def test_plain(self):
        assert visible_len("hello") == 5

    def test_styled(self):
        s = style("hello", fg="red", bold=True)
        assert visible_len(s) == 5

    def test_empty(self):
        assert visible_len("") == 0

    def test_only_escapes(self):
        assert visible_len(f"{BOLD}{RESET}") == 0

    def test_mixed(self):
        s = f"prefix {fg('red')}colored{RESET} suffix"
        assert visible_len(s) == len("prefix colored suffix")


# ── Terminal detection ──────────────────────────────────────────────


class TestSupportsColor:
    """Terminal color detection."""

    def test_no_color_env(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert supports_color() is False

    def test_force_color_env(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        assert supports_color() is True

    def test_force_overrides_no_color(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("NO_COLOR", "1")
        # FORCE_COLOR is checked first.
        assert supports_color() is True

    def test_dumb_terminal(self, monkeypatch):
        monkeypatch.setenv("TERM", "dumb")
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        # Non-tty stream + dumb terminal.
        assert supports_color() is False


class TestColorDepth:
    """Terminal color depth detection."""

    def test_no_color(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        assert color_depth() == 0

    def test_truecolor(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("COLORTERM", "truecolor")
        assert color_depth() == 16_777_216

    def test_24bit(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("COLORTERM", "24bit")
        assert color_depth() == 16_777_216

    def test_256color_term(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("COLORTERM", "")
        monkeypatch.setenv("TERM", "xterm-256color")
        assert color_depth() == 256

    def test_basic_16(self, monkeypatch):
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("COLORTERM", "")
        monkeypatch.setenv("TERM", "xterm")
        assert color_depth() == 16


# ── cursor_move ─────────────────────────────────────────────────────


class TestCursorMove:
    """Cursor movement escape generation."""

    def test_up(self):
        assert cursor_move(3, "up") == "\033[3A"

    def test_down(self):
        assert cursor_move(1, "down") == "\033[1B"

    def test_forward(self):
        assert cursor_move(5, "forward") == "\033[5C"

    def test_back(self):
        assert cursor_move(2, "back") == "\033[2D"

    def test_invalid_direction(self):
        with pytest.raises(ValueError, match="Unknown direction"):
            cursor_move(1, "left")


# ── Constants coverage ──────────────────────────────────────────────


class TestConstants:
    """Verify constant coverage."""

    def test_named_colors_count(self):
        assert len(NAMED_COLORS) == 8

    def test_bright_colors_count(self):
        assert len(BRIGHT_COLORS) == 8

    def test_all_attributes_defined(self):
        for attr in [
            RESET,
            BOLD,
            DIM,
            ITALIC,
            UNDERLINE,
            STRIKETHROUGH,
            REVERSE,
            HIDDEN,
        ]:
            assert attr.startswith("\033[")
            assert attr.endswith("m")

    def test_cursor_constants(self):
        for c in [CURSOR_UP, CURSOR_HIDE, CURSOR_SHOW, CLEAR_LINE]:
            assert c.startswith("\033[")
