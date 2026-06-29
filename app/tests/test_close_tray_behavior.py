"""Tests for close-to-tray behavior (Phase 3-A)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.close_behavior import (
    CloseBehaviorDecision,
    decide_close_behavior,
    render_close_to_tray_hint,
)
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestDecideCloseBehavior:
    """Tests for decide_close_behavior pure function."""

    def test_tray_available_hide_to_tray(self) -> None:
        """tray_available=True, force_quit=False -> hide to tray."""
        result = decide_close_behavior(tray_available=True, force_quit=False)
        assert result.should_hide_to_tray is True
        assert result.should_accept_close is False
        assert "tray" in result.reason.lower()

    def test_tray_unavailable_accept_close(self) -> None:
        """tray_available=False, force_quit=False -> accept close."""
        result = decide_close_behavior(tray_available=False, force_quit=False)
        assert result.should_hide_to_tray is False
        assert result.should_accept_close is True
        assert "unavailable" in result.reason.lower()

    def test_force_quit_accept_close(self) -> None:
        """force_quit=True -> accept close even if tray available."""
        result = decide_close_behavior(tray_available=True, force_quit=True)
        assert result.should_hide_to_tray is False
        assert result.should_accept_close is True
        assert "force" in result.reason.lower()

    def test_result_is_frozen(self) -> None:
        """CloseBehaviorDecision is immutable."""
        result = decide_close_behavior(tray_available=True, force_quit=False)
        assert isinstance(result, CloseBehaviorDecision)


class TestRenderCloseToTrayHint:
    """Tests for render_close_to_tray_hint."""

    def test_hint_with_tray_mentions_tray(self) -> None:
        """Hint when tray available mentions hiding to tray."""
        hint = render_close_to_tray_hint(tray_available=True)
        assert "托盘" in hint

    def test_hint_without_tray_mentions_exit(self) -> None:
        """Hint when tray unavailable mentions exit."""
        hint = render_close_to_tray_hint(tray_available=False)
        assert "退出" in hint


class TestViewModelForceQuit:
    """Tests for ViewModel force_quit_requested field."""

    def test_default_force_quit_is_false(self) -> None:
        """ViewModel defaults force_quit_requested to False."""
        vm = DesktopViewModel()
        assert vm.force_quit_requested is False

    def test_request_force_quit_sets_true(self) -> None:
        """request_force_quit sets force_quit_requested to True."""
        vm = DesktopViewModel()
        vm.request_force_quit()
        assert vm.force_quit_requested is True

    def test_clear_force_quit_request_sets_false(self) -> None:
        """clear_force_quit_request sets force_quit_requested to False."""
        vm = DesktopViewModel()
        vm.request_force_quit()
        vm.clear_force_quit_request()
        assert vm.force_quit_requested is False


class TestWindowCloseEvent:
    """Tests for DesktopWindow closeEvent handling."""

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
    def test_close_callback_returns_true_accepts(qapp: QApplication) -> None:
        """closeEvent accepts when callback returns True."""
        vm = DesktopViewModel()
        accepted = [False]

        def on_close() -> bool:
            accepted[0] = True
            return True

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_close_requested=on_close,
        )
        window.show()

        # Simulate close
        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        window.closeEvent(event)
        assert accepted[0] is True

    @staticmethod
    def test_close_callback_returns_false_ignores(qapp: QApplication) -> None:
        """closeEvent ignores when callback returns False."""
        vm = DesktopViewModel()
        accepted = [True]

        def on_close() -> bool:
            accepted[0] = False
            return False

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_close_requested=on_close,
        )
        window.show()

        # Simulate close
        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        window.closeEvent(event)
        assert accepted[0] is False

    @staticmethod
    def test_close_no_callback_accepts(qapp: QApplication) -> None:
        """closeEvent accepts when no callback set."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        # Should not crash
        window.close()


class TestWindowButtonsStillWork:
    """Tests that existing buttons are unaffected by close behavior."""

    @staticmethod
    def test_settings_button_still_works(qapp: QApplication) -> None:
        """Settings button still opens/closes settings panel."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_close_requested=lambda: True,
        )
        window.show()

        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True

        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is False

    @staticmethod
    def test_status_button_still_works(qapp: QApplication) -> None:
        """Status button still opens/closes product status panel."""
        vm = DesktopViewModel()

        def on_status() -> None:
            vm.toggle_product_status_visible()
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
            on_close_requested=lambda: True,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is False

    @staticmethod
    def test_compact_mode_still_works(qapp: QApplication) -> None:
        """Compact mode toggle still works."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_close_requested=lambda: True,
        )
        window.show()

        window._handle_compact_clicked()
        qapp.processEvents()
        assert vm.compact_mode is True

        window._handle_compact_clicked()
        qapp.processEvents()
        assert vm.compact_mode is False

    @staticmethod
    def test_hide_button_exists(qapp: QApplication) -> None:
        """Hide button still exists and is accessible."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
            on_close_requested=lambda: True,
        )
        window.show()
        assert hasattr(window, "_hide_button")
