"""Tests for DesktopWindow empty input handling."""

from unittest.mock import MagicMock

from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def _make_vm() -> DesktopViewModel:
    return DesktopViewModel()


class TestOnSendClickedEmptyInput:
    """Tests for _on_send_clicked empty input behavior."""

    def test_empty_string_does_not_call_callback(self) -> None:
        """Test empty string does not call on_user_text_submitted."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("")
        window._on_send_clicked()

        callback.assert_not_called()

    def test_whitespace_only_does_not_call_callback(self) -> None:
        """Test whitespace-only string does not call on_user_text_submitted."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("   ")
        window._on_send_clicked()

        callback.assert_not_called()

    def test_non_empty_text_calls_callback(self) -> None:
        """Test non-empty text calls on_user_text_submitted."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("你好")
        window._on_send_clicked()

        callback.assert_called_once_with("你好")

    def test_trimmed_text_calls_callback(self) -> None:
        """Test whitespace-padded text calls callback with trimmed text."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("  你好  ")
        window._on_send_clicked()

        callback.assert_called_once_with("  你好  ")

    def test_non_empty_input_clears_field(self) -> None:
        """Test non-empty input clears the input field."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("Hello")
        window._on_send_clicked()

        assert window._input_field.text() == ""

    def test_empty_input_does_not_clear_field(self) -> None:
        """Test empty input does not clear the input field."""
        callback = MagicMock()
        vm = _make_vm()
        window = DesktopWindow(vm, on_user_text_submitted=callback)

        window._input_field.setText("Hello")
        window._input_field.setText("")
        window._on_send_clicked()

        assert window._input_field.text() == ""
