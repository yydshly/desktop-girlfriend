"""Tests for DesktopWindow empty input guard logic and chat rendering."""

from unittest.mock import MagicMock

import pytest

from app.contracts.states import AppState
from app.ui.chat_message import ChatMessage
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow, render_chat_messages, should_submit_user_text

# Qt GUI tests require a display; skip if not available
_QT_AVAILABLE: bool | None = None


def _qt_available() -> bool:
    global _QT_AVAILABLE
    if _QT_AVAILABLE is None:
        _QT_AVAILABLE = True
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is None:
                QApplication([])
        except Exception:
            _QT_AVAILABLE = False
    return _QT_AVAILABLE


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


class TestDesktopWindowNewConversation:
    """Tests for DesktopWindow new conversation button."""

    @pytest.fixture(autouse=True)
    def _check_qt(self) -> None:
        """Skip all tests in this class if Qt display is not available."""
        if not _qt_available():
            pytest.skip("No Qt display available")

    def _make_window(self) -> tuple[DesktopWindow, MagicMock, MagicMock]:
        """Create a DesktopWindow with mock callbacks."""
        vm = DesktopViewModel()
        on_submit = MagicMock()
        on_clear = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=on_submit,
            on_conversation_cleared=on_clear,
        )
        return window, on_submit, on_clear

    def test_constructor_accepts_on_conversation_cleared_callback(self) -> None:
        """Test DesktopWindow can be constructed with on_conversation_cleared callback."""
        vm = DesktopViewModel()
        on_clear = MagicMock()
        # Should not raise
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=on_clear,
        )
        assert window is not None

    def test_new_conversation_button_clicked_invokes_callback(self) -> None:
        """Test clicking new conversation button invokes the callback."""
        window, _, on_clear = self._make_window()
        window._new_conversation_button.click()
        on_clear.assert_called_once()

    def test_new_conversation_button_disabled_while_thinking(self) -> None:
        """Test new conversation button is disabled while THINKING."""
        vm = DesktopViewModel()
        on_clear = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=on_clear,
        )

        # Simulate THINKING state
        vm.state = AppState.THINKING
        window.update_from_view_model()

        assert not window._new_conversation_button.isEnabled()

    def test_new_conversation_button_enabled_while_idle(self) -> None:
        """Test new conversation button is enabled while IDLE."""
        vm = DesktopViewModel()
        on_clear = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=on_clear,
        )

        # Already IDLE
        window.update_from_view_model()

        assert window._new_conversation_button.isEnabled()


class TestDesktopWindowStopSpeaking:
    """Tests for DesktopWindow stop speaking button."""

    @pytest.fixture(autouse=True)
    def _check_qt(self) -> None:
        """Skip all tests in this class if Qt display is not available."""
        if not _qt_available():
            pytest.skip("No Qt display available")

    def _make_window_with_stop(self) -> tuple[DesktopWindow, MagicMock, MagicMock, MagicMock]:
        """Create a DesktopWindow with stop callback."""
        vm = DesktopViewModel()
        on_submit = MagicMock()
        on_clear = MagicMock()
        on_stop = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=on_submit,
            on_conversation_cleared=on_clear,
            on_tts_stop_requested=on_stop,
        )
        return window, on_submit, on_clear, on_stop

    def test_window_has_stop_speaking_button(self) -> None:
        """Test DesktopWindow has stop speaking button."""
        window, _, _, _ = self._make_window_with_stop()
        assert hasattr(window, "_stop_speaking_button")

    def test_stop_button_disabled_when_idle(self) -> None:
        """Test stop button is disabled when IDLE."""
        window, _, _, _ = self._make_window_with_stop()
        window.update_from_view_model()
        assert not window._stop_speaking_button.isEnabled()

    def test_stop_button_disabled_when_thinking(self) -> None:
        """Test stop button is disabled when THINKING."""
        vm = DesktopViewModel()
        on_stop = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=MagicMock(),
            on_tts_stop_requested=on_stop,
        )
        vm.state = AppState.THINKING
        window.update_from_view_model()
        assert not window._stop_speaking_button.isEnabled()

    def test_stop_button_enabled_when_speaking(self) -> None:
        """Test stop button is enabled when SPEAKING."""
        vm = DesktopViewModel()
        on_stop = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=MagicMock(),
            on_tts_stop_requested=on_stop,
        )
        vm.state = AppState.SPEAKING
        window.update_from_view_model()
        assert window._stop_speaking_button.isEnabled()

    def test_stop_button_clicked_invokes_callback(self) -> None:
        """Test clicking stop button invokes on_tts_stop_requested."""
        vm = DesktopViewModel()
        on_stop = MagicMock()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=MagicMock(),
            on_tts_stop_requested=on_stop,
        )
        # Set SPEAKING so button is enabled
        vm.state = AppState.SPEAKING
        window.update_from_view_model()
        window._stop_speaking_button.click()
        on_stop.assert_called_once()

    def test_speaking_send_and_input_disabled(self) -> None:
        """Test send and input are disabled when SPEAKING."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=MagicMock(),
            on_tts_stop_requested=MagicMock(),
        )
        vm.state = AppState.SPEAKING
        window.update_from_view_model()
        assert not window._send_button.isEnabled()
        assert not window._input_field.isEnabled()
        assert not window._new_conversation_button.isEnabled()

    def test_stop_button_no_callback_when_none(self) -> None:
        """Test stop button click with no callback does not raise."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            vm,
            on_user_text_submitted=MagicMock(),
            on_conversation_cleared=MagicMock(),
            on_tts_stop_requested=None,
        )
        # Should not raise
        window._stop_speaking_button.click()


