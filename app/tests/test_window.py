"""Tests for DesktopWindow empty input guard logic and chat rendering."""

from app.ui.chat_message import ChatMessage
from app.ui.window import render_chat_messages, should_submit_user_text


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


class TestRenderChatMessages:
    """Tests for render_chat_messages() — no Qt required."""

    def test_empty_list_returns_placeholder(self) -> None:
        """Test empty message list returns placeholder text."""
        result = render_chat_messages([])
        assert result == "还没有对话，和小云说句话吧。"

    def test_single_user_message(self) -> None:
        """Test single user message renders correctly."""
        result = render_chat_messages([ChatMessage(role="user", text="你好")])
        assert "你：" in result
        assert "你好" in result
        assert "小云：" not in result

    def test_single_assistant_message(self) -> None:
        """Test single assistant message renders correctly."""
        result = render_chat_messages([ChatMessage(role="assistant", text="你好，很高兴见到你。")])
        assert "小云：" in result
        assert "你好，很高兴见到你。" in result
        assert "你：" not in result

    def test_multiple_messages_preserve_order(self) -> None:
        """Test multiple messages preserve order with blank line separation."""
        messages = [
            ChatMessage(role="user", text="你好"),
            ChatMessage(role="assistant", text="你好，很高兴见到你。"),
            ChatMessage(role="user", text="再见"),
            ChatMessage(role="assistant", text="再见！"),
        ]
        result = render_chat_messages(messages)
        lines = result.split("\n")
        user1_idx = lines.index("你：")
        assistant1_idx = lines.index("小云：")
        user2_idx = lines.index("你：", user1_idx + 1)
        assistant2_idx = lines.index("小云：", assistant1_idx + 1)
        assert user1_idx < assistant1_idx < user2_idx < assistant2_idx

    def test_messages_separated_by_blank_line(self) -> None:
        """Test that messages are separated by blank lines."""
        messages = [
            ChatMessage(role="user", text="Hello"),
            ChatMessage(role="assistant", text="Hi there!"),
        ]
        result = render_chat_messages(messages)
        assert "Hello" in result
        assert "Hi there!" in result

