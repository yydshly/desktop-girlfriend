"""Tests for proactive companion UX (Phase 2-G)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.companion_presence import render_companion_status_text
from app.ui.proactive_companion_view import (
    build_proactive_companion_view,
    render_proactive_message_prefix,
    render_proactive_status_text,
)
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestProactiveCompanionView:
    """Tests for proactive_companion_view module."""

    def test_build_proactive_companion_view_enabled(self) -> None:
        """build_proactive_companion_view(enabled=true) indicates enabled."""
        view = build_proactive_companion_view(
            enabled=True,
            quiet_hours_enabled=False,
            cooldown_seconds=300,
        )
        assert "小云会在你空闲时轻轻出现。" in view.subtitle

    def test_build_proactive_companion_view_disabled(self) -> None:
        """build_proactive_companion_view(enabled=false) indicates disabled."""
        view = build_proactive_companion_view(
            enabled=False,
            quiet_hours_enabled=False,
            cooldown_seconds=300,
        )
        assert "主动陪伴当前未启用。" in view.subtitle

    def test_render_proactive_message_prefix(self) -> None:
        """render_proactive_message_prefix() returns '小云主动来陪你：'."""
        assert render_proactive_message_prefix() == "小云主动来陪你："

    def test_render_proactive_status_text_nonempty(self) -> None:
        """render_proactive_status_text() returns non-empty Chinese text."""
        text = render_proactive_status_text()
        assert text
        assert len(text) > 0
        assert "。" in text or "！" in text or "？" in text


class TestProactiveCompanionSettingsView:
    """Tests for proactive companion settings panel content."""

    def test_settings_view_includes_proactive_section(self) -> None:
        """Settings view includes an '主动陪伴设置' section."""
        from app.core.config import AppConfig

        config = AppConfig()
        view = build_settings_view(config)
        section_titles = [s.title for s in view.sections]
        assert "主动陪伴设置" in section_titles

    def test_settings_view_includes_cooldown_explanation(self) -> None:
        """Settings view includes cooldown time explanation."""
        from app.core.config import AppConfig

        config = AppConfig()
        config.proactive_enabled = True
        view = build_settings_view(config)
        text = render_settings_view_text(view)
        assert "冷却时间" in text

    def test_settings_view_includes_quiet_hours_explanation(self) -> None:
        """Settings view includes quiet hours explanation."""
        from app.core.config import AppConfig

        config = AppConfig()
        config.proactive_enabled = True
        view = build_settings_view(config)
        text = render_settings_view_text(view)
        assert "勿扰" in text

    def test_settings_view_includes_proactive_description(self) -> None:
        """Settings view includes proactive companion description when enabled."""
        from app.core.config import AppConfig

        config = AppConfig()
        config.proactive_enabled = True
        view = build_settings_view(config)
        text = render_settings_view_text(view)
        assert "小云会在你空闲" in text

    def test_settings_view_includes_user_control_hint(self) -> None:
        """Settings view includes user control hint for proactive."""
        from app.core.config import AppConfig

        config = AppConfig()
        config.proactive_enabled = True
        view = build_settings_view(config)
        text = render_settings_view_text(view)
        assert "别打扰" in text or "安静" in text

    def test_settings_view_does_not_leak_api_keys(self) -> None:
        """Settings view does not contain real API key values."""
        from app.core.config import AppConfig

        config = AppConfig()
        config.minimax_api_key = "sk-abcdefghijk1234567890"
        config.mimo_api_key = "sk-xyz1234567890abcdefgh"
        view = build_settings_view(config)
        text = render_settings_view_text(view)
        assert "sk-abcdefghijk1234567890" not in text
        assert "sk-xyz1234567890abcdefgh" not in text


class TestProactiveCompanionStatusText:
    """Tests for proactive companion status text."""

    def test_proactive_status_text_is_natural(self) -> None:
        """Proactive status text is natural and friendly."""
        from app.ui.avatar_action import AvatarAction

        text = render_companion_status_text(AvatarAction.PROACTIVE)
        assert "主动" in text or "出现" in text or "陪你" in text


class TestWindowProactiveUX:
    """Tests for DesktopWindow proactive UX compatibility."""

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
    def test_compact_mode_does_not_clear_chat(qapp: QApplication) -> None:
        """Compact mode does not clear chat messages."""
        from app.ui.chat_message import ChatMessage

        vm = DesktopViewModel()
        vm.chat_messages.append(ChatMessage(role="user", text="test message"))

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window._handle_compact_clicked()
        qapp.processEvents()

        assert len(vm.chat_messages) == 1
        assert vm.chat_messages[0].text == "test message"

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
    def test_proactive_avatar_action_shows_natural_status(
        qapp: QApplication,
    ) -> None:
        """Proactive avatar action shows natural status text."""
        from app.ui.avatar_action import AvatarAction

        vm = DesktopViewModel()
        # Simulate proactive state
        vm.avatar_action = AvatarAction.PROACTIVE
        vm.avatar_action_label = "小云来陪你一下"
        vm.companion_status_text = "我看到你安静了一会儿，就来陪你一下。"

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window.update_from_view_model()
        assert vm.companion_status_text == "我看到你安静了一会儿，就来陪你一下。"
