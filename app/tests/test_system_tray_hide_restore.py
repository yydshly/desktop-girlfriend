"""Tests for system tray hide/restore functionality (Phase 2-F)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.tray_view import build_tray_view, render_tray_availability_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestTrayView:
    """Tests for tray_view module."""

    def test_build_tray_view_default_tooltip_contains_xiaoyun(self) -> None:
        """Default tooltip contains '小云'."""
        view = build_tray_view()
        assert "小云" in view.tooltip

    def test_build_tray_view_show_text_is_show_xiaoyun(self) -> None:
        """show_text equals '显示小云'."""
        view = build_tray_view()
        assert view.show_text == "显示小云"

    def test_build_tray_view_hide_text_is_hide_xiaoyun(self) -> None:
        """hide_text equals '隐藏小云'."""
        view = build_tray_view()
        assert view.hide_text == "隐藏小云"

    def test_build_tray_view_quit_text_is_exit(self) -> None:
        """quit_text equals '退出'."""
        view = build_tray_view()
        assert view.quit_text == "退出"

    def test_build_tray_view_custom_companion_name(self) -> None:
        """Custom companion name appears in tooltip."""
        view = build_tray_view(companion_name="小雪")
        assert "小雪" in view.tooltip

    def test_render_tray_availability_text_true(self) -> None:
        """render_tray_availability_text(True) returns '托盘可用'."""
        assert render_tray_availability_text(True) == "托盘可用"

    def test_render_tray_availability_text_false(self) -> None:
        """render_tray_availability_text(False) returns '托盘不可用'."""
        assert render_tray_availability_text(False) == "托盘不可用"


class TestViewModelTrayFields:
    """Tests for ViewModel tray-related fields and methods."""

    def test_default_tray_available_is_false(self) -> None:
        """ViewModel defaults tray_available to False."""
        vm = DesktopViewModel()
        assert vm.tray_available is False

    def test_default_hidden_to_tray_is_false(self) -> None:
        """ViewModel defaults hidden_to_tray to False."""
        vm = DesktopViewModel()
        assert vm.hidden_to_tray is False

    def test_set_tray_available_true(self) -> None:
        """set_tray_available(True) updates tray_available."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        assert vm.tray_available is True

    def test_set_tray_available_false(self) -> None:
        """set_tray_available(False) updates tray_available."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        vm.set_tray_available(False)
        assert vm.tray_available is False

    def test_set_hidden_to_tray_true(self) -> None:
        """set_hidden_to_tray(True) updates hidden_to_tray."""
        vm = DesktopViewModel()
        vm.set_hidden_to_tray(True)
        assert vm.hidden_to_tray is True

    def test_set_hidden_to_tray_false(self) -> None:
        """set_hidden_to_tray(False) updates hidden_to_tray."""
        vm = DesktopViewModel()
        vm.set_hidden_to_tray(True)
        vm.set_hidden_to_tray(False)
        assert vm.hidden_to_tray is False

    def test_tray_fields_do_not_affect_chat_messages(self) -> None:
        """Tray fields do not affect chat_messages."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        vm.set_hidden_to_tray(True)
        assert vm.chat_messages == []

    def test_tray_fields_do_not_affect_compact_mode(self) -> None:
        """Tray fields do not affect compact_mode."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        assert vm.compact_mode is False
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        vm.set_hidden_to_tray(True)
        assert vm.compact_mode is True

    def test_tray_fields_do_not_affect_always_on_top(self) -> None:
        """Tray fields do not affect always_on_top."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        assert vm.always_on_top is False

    def test_tray_fields_do_not_affect_settings_visible(self) -> None:
        """Tray fields do not affect settings_visible."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        vm.set_hidden_to_tray(True)
        assert vm.settings_visible is False


class TestSystemTrayControllerCallbacks:
    """Tests for tray controller state callbacks."""

    @staticmethod
    def test_restore_window_calls_restore_callback(qapp: QApplication) -> None:
        """Restoring from tray notifies app state."""
        from app.ui.system_tray import DesktopSystemTrayController

        restored = False

        def on_restore() -> None:
            nonlocal restored
            restored = True

        controller = DesktopSystemTrayController(
            window=None,
            on_quit=lambda: None,
            on_restore=on_restore,
        )

        controller.restore_window()

        assert restored is True


class TestWindowHideButton:
    """Tests for DesktopWindow hide button."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_hide_button_exists_with_callback(qapp: QApplication) -> None:
        """Hide button exists when on_hide_requested is provided."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        assert hasattr(window, "_hide_button")
        assert window._hide_button.text() == "隐藏"

    @staticmethod
    def test_hide_button_hidden_without_callback(qapp: QApplication) -> None:
        """Hide button is hidden when on_hide_requested is None."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=None,
        )
        window.show()
        assert hasattr(window, "_hide_button")
        assert not window._hide_button.isVisible()

    @staticmethod
    def test_hide_button_triggers_callback(qapp: QApplication) -> None:
        """Clicking hide button triggers on_hide_requested callback."""
        vm = DesktopViewModel()
        vm.set_tray_available(True)
        hide_called = False

        def on_hide() -> None:
            nonlocal hide_called
            hide_called = True

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=on_hide,
        )
        window.show()
        window.update_from_view_model()

        window._hide_button.clicked.emit()
        qapp.processEvents()

        assert hide_called is True

    @staticmethod
    def test_hide_button_disabled_when_tray_unavailable(qapp: QApplication) -> None:
        """Hide button is disabled when the system tray is unavailable."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        window.update_from_view_model()

        assert window._hide_button.isEnabled() is False
        assert "托盘不可用" in window._hide_button.toolTip()

    @staticmethod
    def test_status_button_still_works(qapp: QApplication) -> None:
        """Status button remains functional after hide button is added."""
        vm = DesktopViewModel()

        def on_status() -> None:
            vm.toggle_product_status_visible()
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
            on_hide_requested=lambda: None,
        )
        window.show()

        assert not vm.product_status_visible
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

    @staticmethod
    def test_settings_button_still_works(qapp: QApplication) -> None:
        """Settings button remains functional after hide button is added."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()

        assert not vm.settings_visible
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True

    @staticmethod
    def test_compact_mode_hides_hide_button(qapp: QApplication) -> None:
        """Compact mode hides the hide button along with aux button row."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()

        assert window._hide_button.isVisible()

        window._handle_compact_clicked()
        qapp.processEvents()

        assert not window._hide_button.isVisible()

    @staticmethod
    def test_compact_mode_does_not_clear_chat_messages(qapp: QApplication) -> None:
        """Compact mode does not clear chat messages."""
        from app.ui.chat_message import ChatMessage

        vm = DesktopViewModel()
        vm.chat_messages.append(ChatMessage(role="user", text="test message"))

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()

        window._handle_compact_clicked()
        qapp.processEvents()

        assert len(vm.chat_messages) == 1
        assert vm.chat_messages[0].text == "test message"
