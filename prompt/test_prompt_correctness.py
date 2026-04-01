"""Correctness tests: zerodep prompt."""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from prompt import (
    _ANSI_BOLD,
    _ANSI_ITALIC,
    _ANSI_RESET,
    _ANSI_UNDERLINE,
    _NAMED_COLORS,
    Style,
    _hex_to_ansi_fg,
    _normalise_choices,
    _parse_confirm_input,
    _parse_style_string,
    _read_key,
    _render_select,
    confirm,
    select,
    text,
)

# ── TestStyle ──


class TestStyle:
    """Tests for the Style class."""

    def test_default_style_creation(self):
        """Default style has all expected roles."""
        sty = Style()
        for role in ("question", "answer", "pointer", "highlighted", "error"):
            assert sty.get(role) != "", f"role '{role}' should have a default"

    def test_custom_style(self):
        """Custom style overrides a role."""
        sty = Style([("question", "fg:#ff0000 bold")])
        code = sty.get("question")
        assert "\033[38;2;255;0;0m" in code
        assert _ANSI_BOLD in code

    def test_apply_wraps_text(self):
        """apply() should wrap text with ANSI prefix and reset suffix."""
        sty = Style([("answer", "bold")], colors=True)
        result = sty.apply("answer", "hello")
        assert result.startswith(_ANSI_BOLD)
        assert result.endswith(_ANSI_RESET)
        assert "hello" in result

    def test_apply_no_color(self):
        """apply() returns plain text when colors are disabled."""
        sty = Style([("answer", "bold")], colors=False)
        result = sty.apply("answer", "hello")
        assert result == "hello"

    def test_apply_unknown_role(self):
        """apply() on an unknown role returns plain text."""
        sty = Style()
        assert sty.apply("nonexistent", "hello") == "hello"

    def test_get_unknown_role(self):
        """get() on an unknown role returns empty string."""
        sty = Style()
        assert sty.get("nonexistent") == ""

    def test_style_none_list(self):
        """Style(None) should produce the default style."""
        sty = Style(None)
        assert sty.get("question") != ""

    def test_multiple_overrides(self):
        """Multiple roles can be overridden at once."""
        sty = Style(
            [
                ("question", "fg:red"),
                ("answer", "fg:blue underline"),
            ]
        )
        q = sty.get("question")
        assert f"\033[{_NAMED_COLORS['red']}m" in q
        a = sty.get("answer")
        assert f"\033[{_NAMED_COLORS['blue']}m" in a
        assert _ANSI_UNDERLINE in a


# ── TestAnsiHelpers ──


class TestAnsiHelpers:
    """Tests for ANSI escape code helpers."""

    def test_hex_to_ansi_fg_red(self):
        assert _hex_to_ansi_fg("#ff0000") == "\033[38;2;255;0;0m"

    def test_hex_to_ansi_fg_green(self):
        assert _hex_to_ansi_fg("#00ff00") == "\033[38;2;0;255;0m"

    def test_hex_to_ansi_fg_blue(self):
        assert _hex_to_ansi_fg("#0000ff") == "\033[38;2;0;0;255m"

    def test_hex_to_ansi_fg_with_hash(self):
        """Leading '#' should be optional / tolerated."""
        assert _hex_to_ansi_fg("aabbcc") == "\033[38;2;170;187;204m"

    def test_hex_to_ansi_fg_invalid(self):
        with pytest.raises(ValueError):
            _hex_to_ansi_fg("#xyz")

    def test_hex_to_ansi_fg_short(self):
        with pytest.raises(ValueError):
            _hex_to_ansi_fg("#fff")

    def test_parse_style_string_bold(self):
        assert _parse_style_string("bold") == _ANSI_BOLD

    def test_parse_style_string_italic(self):
        assert _parse_style_string("italic") == _ANSI_ITALIC

    def test_parse_style_string_underline(self):
        assert _parse_style_string("underline") == _ANSI_UNDERLINE

    def test_parse_style_string_combined(self):
        result = _parse_style_string("fg:#ff0000 bold underline")
        assert "\033[38;2;255;0;0m" in result
        assert _ANSI_BOLD in result
        assert _ANSI_UNDERLINE in result

    def test_parse_style_string_named_color(self):
        result = _parse_style_string("fg:green")
        assert f"\033[{_NAMED_COLORS['green']}m" in result

    def test_parse_style_string_empty(self):
        assert _parse_style_string("") == ""

    def test_parse_style_string_unknown_token(self):
        """Unknown tokens are silently ignored."""
        result = _parse_style_string("unknown_token bold")
        assert result == _ANSI_BOLD

    def test_parse_style_case_insensitive(self):
        """Style tokens should be case-insensitive."""
        result = _parse_style_string("BOLD")
        assert result == _ANSI_BOLD


# ── TestConfirmParsing ──


class TestConfirmParsing:
    """Tests for confirm input parsing logic."""

    def test_empty_default_true(self):
        assert _parse_confirm_input("", default=True) is True

    def test_empty_default_false(self):
        assert _parse_confirm_input("", default=False) is False

    def test_yes_variants(self):
        for val in ("y", "Y", "yes", "YES", "Yes"):
            assert _parse_confirm_input(val, default=False) is True

    def test_no_variants(self):
        for val in ("n", "N", "no", "NO", "No"):
            assert _parse_confirm_input(val, default=True) is False

    def test_unrecognised(self):
        assert _parse_confirm_input("maybe", default=True) is None

    def test_whitespace_stripped(self):
        assert _parse_confirm_input("  y  ", default=False) is True


class TestConfirmFunction:
    """Tests for the confirm() function with simulated input."""

    def test_confirm_yes(self):
        inp = io.StringIO("y\n")
        out = io.StringIO()
        result = confirm("Continue?", input_stream=inp, output_stream=out)
        assert result is True

    def test_confirm_no(self):
        inp = io.StringIO("n\n")
        out = io.StringIO()
        result = confirm("Continue?", input_stream=inp, output_stream=out)
        assert result is False

    def test_confirm_default_enter(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        result = confirm("Continue?", default=True, input_stream=inp, output_stream=out)
        assert result is True

    def test_confirm_default_false_enter(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        result = confirm(
            "Continue?", default=False, input_stream=inp, output_stream=out
        )
        assert result is False

    def test_confirm_eof(self):
        inp = io.StringIO("")
        out = io.StringIO()
        result = confirm("Continue?", input_stream=inp, output_stream=out)
        assert result is None

    def test_confirm_invalid_then_valid(self):
        inp = io.StringIO("maybe\ny\n")
        out = io.StringIO()
        result = confirm("Continue?", input_stream=inp, output_stream=out)
        assert result is True

    def test_confirm_output_contains_hint(self):
        inp = io.StringIO("y\n")
        out = io.StringIO()
        confirm("Continue?", default=True, input_stream=inp, output_stream=out)
        output = out.getvalue()
        assert "Y/n" in output

    def test_confirm_output_hint_default_false(self):
        inp = io.StringIO("n\n")
        out = io.StringIO()
        confirm("Continue?", default=False, input_stream=inp, output_stream=out)
        output = out.getvalue()
        assert "y/N" in output


# ── TestSelectChoices ──


class TestSelectChoices:
    """Tests for choice normalisation logic."""

    def test_string_choices(self):
        result = _normalise_choices(["a", "b", "c"])
        assert len(result) == 3
        assert result[0] == {"name": "a", "value": "a"}
        assert result[2] == {"name": "c", "value": "c"}

    def test_dict_choices_name_value(self):
        result = _normalise_choices(
            [
                {"name": "Apple", "value": "apple"},
                {"name": "Banana", "value": "banana"},
            ]
        )
        assert result[0]["name"] == "Apple"
        assert result[0]["value"] == "apple"

    def test_dict_choices_name_only(self):
        result = _normalise_choices([{"name": "Apple"}])
        assert result[0]["value"] == "Apple"

    def test_dict_choices_value_only(self):
        result = _normalise_choices([{"value": "apple"}])
        assert result[0]["name"] == "apple"

    def test_empty_choices_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _normalise_choices([])

    def test_mixed_types_cast_to_string(self):
        """Non-string, non-dict items are cast to str."""
        result = _normalise_choices([42])  # type: ignore
        assert result[0] == {"name": "42", "value": "42"}


class TestSelectFallback:
    """Tests for select() in fallback (non-TTY) mode."""

    def test_select_valid_number(self):
        inp = io.StringIO("2\n")
        out = io.StringIO()
        result = select("Pick:", ["a", "b", "c"], input_stream=inp, output_stream=out)
        assert result == "b"

    def test_select_empty_uses_default(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        result = select(
            "Pick:", ["a", "b", "c"], default="b", input_stream=inp, output_stream=out
        )
        assert result == "b"

    def test_select_empty_no_default_uses_first(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        result = select("Pick:", ["a", "b", "c"], input_stream=inp, output_stream=out)
        assert result == "a"

    def test_select_eof(self):
        inp = io.StringIO("")
        out = io.StringIO()
        result = select("Pick:", ["a", "b", "c"], input_stream=inp, output_stream=out)
        assert result is None

    def test_select_invalid_number_falls_to_default(self):
        inp = io.StringIO("99\n")
        out = io.StringIO()
        result = select("Pick:", ["a", "b", "c"], input_stream=inp, output_stream=out)
        assert result == "a"

    def test_select_non_numeric_falls_to_default(self):
        inp = io.StringIO("xyz\n")
        out = io.StringIO()
        result = select("Pick:", ["a", "b", "c"], input_stream=inp, output_stream=out)
        assert result == "a"

    def test_select_with_dict_choices(self):
        inp = io.StringIO("1\n")
        out = io.StringIO()
        result = select(
            "Pick:",
            [
                {"name": "Apple", "value": "apple"},
                {"name": "Banana", "value": "banana"},
            ],
            input_stream=inp,
            output_stream=out,
        )
        assert result == "apple"


class TestSelectRendering:
    """Tests for the select menu rendering function."""

    def test_render_highlights_current(self):
        choices = _normalise_choices(["a", "b", "c"])
        sty = Style()
        rendered = _render_select(choices, 0, sty)
        assert "❯" in rendered

    def test_render_non_selected_no_pointer(self):
        choices = _normalise_choices(["a", "b", "c"])
        sty = Style()
        rendered = _render_select(choices, 0, sty)
        lines = rendered.split("\n")
        # lines[1] and lines[2] should NOT have the pointer
        assert "❯" not in lines[1]
        assert "❯" not in lines[2]

    def test_render_all_choices_present(self):
        choices = _normalise_choices(["alpha", "beta", "gamma"])
        sty = Style()
        rendered = _render_select(choices, 1, sty)
        assert "alpha" in rendered
        assert "beta" in rendered
        assert "gamma" in rendered


# ── TestTextValidation ──


class TestTextValidation:
    """Tests for text() with validation."""

    def test_text_no_validation(self):
        inp = io.StringIO("hello\n")
        out = io.StringIO()
        result = text("Name:", input_stream=inp, output_stream=out)
        assert result == "hello"

    def test_text_default_value(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        result = text("Name:", default="world", input_stream=inp, output_stream=out)
        assert result == "world"

    def test_text_validation_pass(self):
        inp = io.StringIO("ok\n")
        out = io.StringIO()
        result = text(
            "Name:", validate=lambda s: True, input_stream=inp, output_stream=out
        )
        assert result == "ok"

    def test_text_validation_fail_then_pass(self):
        inp = io.StringIO("\nhello\n")
        out = io.StringIO()
        result = text(
            "Name:",
            validate=lambda s: True if s else "Required",
            input_stream=inp,
            output_stream=out,
        )
        assert result == "hello"

    def test_text_validation_error_message(self):
        inp = io.StringIO("bad\ngood\n")
        out = io.StringIO()

        def validator(s: str) -> bool | str:
            return True if s == "good" else "Must be 'good'"

        result = text("Word:", validate=validator, input_stream=inp, output_stream=out)
        assert result == "good"
        assert "Must be 'good'" in out.getvalue()

    def test_text_validation_false_shows_generic(self):
        inp = io.StringIO("bad\ngood\n")
        out = io.StringIO()

        call_count = 0

        def validator(s: str) -> bool | str:
            nonlocal call_count
            call_count += 1
            return call_count > 1

        result = text("Word:", validate=validator, input_stream=inp, output_stream=out)
        assert result == "good"
        assert "Invalid input" in out.getvalue()

    def test_text_eof(self):
        inp = io.StringIO("")
        out = io.StringIO()
        result = text("Name:", input_stream=inp, output_stream=out)
        assert result is None

    def test_text_prompt_shows_default(self):
        inp = io.StringIO("\n")
        out = io.StringIO()
        text("Name:", default="Alice", input_stream=inp, output_stream=out)
        assert "Alice" in out.getvalue()


# ── TestReadKey ──


class TestReadKey:
    """Tests for the _read_key helper with simulated streams."""

    def test_read_key_enter(self):
        stream = io.StringIO("\n")
        assert _read_key(input_stream=stream) == "enter"

    def test_read_key_carriage_return(self):
        stream = io.StringIO("\r")
        assert _read_key(input_stream=stream) == "enter"

    def test_read_key_ctrl_c(self):
        stream = io.StringIO("\x03")
        assert _read_key(input_stream=stream) == "ctrl-c"

    def test_read_key_ctrl_d(self):
        stream = io.StringIO("\x04")
        assert _read_key(input_stream=stream) == "ctrl-d"

    def test_read_key_eof(self):
        stream = io.StringIO("")
        assert _read_key(input_stream=stream) == "ctrl-d"

    def test_read_key_arrow_up(self):
        stream = io.StringIO("\x1b[A")
        assert _read_key(input_stream=stream) == "up"

    def test_read_key_arrow_down(self):
        stream = io.StringIO("\x1b[B")
        assert _read_key(input_stream=stream) == "down"

    def test_read_key_arrow_right(self):
        stream = io.StringIO("\x1b[C")
        assert _read_key(input_stream=stream) == "right"

    def test_read_key_arrow_left(self):
        stream = io.StringIO("\x1b[D")
        assert _read_key(input_stream=stream) == "left"

    def test_read_key_regular_char(self):
        stream = io.StringIO("a")
        assert _read_key(input_stream=stream) == "a"

    def test_read_key_escape_alone(self):
        # ESC followed by a non-'[' character
        stream = io.StringIO("\x1bx")
        assert _read_key(input_stream=stream) == "esc"
