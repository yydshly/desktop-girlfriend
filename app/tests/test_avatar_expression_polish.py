"""Tests for avatar expression polish (Phase 2-H)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.avatar_action import AvatarAction
from app.ui.avatar_expression_view import build_avatar_expression_view
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestAvatarExpressionView:
    """Tests for avatar_expression_view module."""

    def test_idle_expression_label(self) -> None:
        """IDLE expression label is '安静陪着你'."""
        expr = build_avatar_expression_view(AvatarAction.IDLE)
        assert expr.label == "安静陪着你"

    def test_listening_expression_label(self) -> None:
        """LISTENING expression label is '认真听你说'."""
        expr = build_avatar_expression_view(AvatarAction.LISTENING)
        assert expr.label == "认真听你说"

    def test_thinking_expression_label(self) -> None:
        """THINKING expression label is '想一想'."""
        expr = build_avatar_expression_view(AvatarAction.THINKING)
        assert expr.label == "想一想"

    def test_speaking_expression_label(self) -> None:
        """SPEAKING expression label is '回应你'."""
        expr = build_avatar_expression_view(AvatarAction.SPEAKING)
        assert expr.label == "回应你"

    def test_proactive_expression_label(self) -> None:
        """PROACTIVE expression label is '来陪你一下'."""
        expr = build_avatar_expression_view(AvatarAction.PROACTIVE)
        assert expr.label == "来陪你一下"

    def test_error_expression_label(self) -> None:
        """ERROR expression label is '有点小状况'."""
        expr = build_avatar_expression_view(AvatarAction.ERROR)
        assert expr.label == "有点小状况"

    def test_all_expressions_have_emoji(self) -> None:
        """All avatar expressions have non-empty emoji."""
        for action in AvatarAction:
            expr = build_avatar_expression_view(action)
            assert expr.emoji, f"Missing emoji for {action}"
            assert len(expr.emoji) > 0

    def test_all_expressions_have_aria_text(self) -> None:
        """All avatar expressions have non-empty aria_text."""
        for action in AvatarAction:
            expr = build_avatar_expression_view(action)
            assert expr.aria_text, f"Missing aria_text for {action}"
            assert len(expr.aria_text) > 0

    def test_all_expressions_have_mood(self) -> None:
        """All avatar expressions have non-empty mood."""
        for action in AvatarAction:
            expr = build_avatar_expression_view(action)
            assert expr.mood, f"Missing mood for {action}"
            assert len(expr.mood) > 0


class TestWindowAvatarExpression:
    """Tests for DesktopWindow avatar expression display."""

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
    def test_avatar_expression_label_exists(qapp: QApplication) -> None:
        """Avatar expression label exists."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_avatar_expression_label")

    @staticmethod
    def test_avatar_label_shows_idle_text(qapp: QApplication) -> None:
        """Idle state shows '安静陪着你' label."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "安静陪着你"

    @staticmethod
    def test_status_button_still_works(qapp: QApplication) -> None:
        """Status button remains functional."""
        vm = DesktopViewModel()

        def on_status() -> None:
            vm.toggle_product_status_visible()
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
        )
        window.show()

        assert not vm.product_status_visible
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

    @staticmethod
    def test_settings_button_still_works(qapp: QApplication) -> None:
        """Settings button remains functional."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert not vm.settings_visible
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True

    @staticmethod
    def test_compact_mode_switches(qapp: QApplication) -> None:
        """Compact mode can be switched on and off."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert not vm.compact_mode

        window._handle_compact_clicked()
        qapp.processEvents()
        assert vm.compact_mode

        window._handle_compact_clicked()
        qapp.processEvents()
        assert not vm.compact_mode

    @staticmethod
    def test_hide_button_still_safe(qapp: QApplication) -> None:
        """Hide button is safe when callback is None."""
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
    def test_avatar_expression_updates_with_state(qapp: QApplication) -> None:
        """Avatar expression label updates when avatar_action changes."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        # Initial state should be IDLE
        vm.avatar_action = AvatarAction.IDLE
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "安静陪着你"

        # Change to LISTENING
        vm.avatar_action = AvatarAction.LISTENING
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "认真听你说"

        # Change to SPEAKING
        vm.avatar_action = AvatarAction.SPEAKING
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "回应你"

        # Change to PROACTIVE
        vm.avatar_action = AvatarAction.PROACTIVE
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "来陪你一下"

        # Change to ERROR
        vm.avatar_action = AvatarAction.ERROR
        window.update_from_view_model()
        assert window._avatar_expression_label.text() == "有点小状况"
