"""Tests for DesktopWindow empty input guard logic."""

from app.ui.window import should_submit_user_text


class TestShouldSubmitUserText:
    """Tests for should_submit_user_text() — no Qt required."""

    def test_empty_string_returns_false(self) -> None:
        """Test empty string returns False."""
        assert should_submit_user_text("") is False

    def test_whitespace_only_returns_false(self) -> None:
        """Test whitespace-only string returns False."""
        assert should_submit_user_text("   ") is False

    def test_newline_tab_whitespace_returns_false(self) -> None:
        """Test newline/tab whitespace returns False."""
        assert should_submit_user_text("\n\t") is False

    def test_valid_chinese_text_returns_true(self) -> None:
        """Test valid Chinese text returns True."""
        assert should_submit_user_text("你好") is True

    def test_valid_padded_text_returns_true(self) -> None:
        """Test whitespace-padded text returns True."""
        assert should_submit_user_text("  你好  ") is True

    def test_valid_english_text_returns_true(self) -> None:
        """Test valid English text returns True."""
        assert should_submit_user_text("Hello") is True
