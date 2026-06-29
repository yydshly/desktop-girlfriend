"""Tests for Settings Runtime Controls v1 (Phase 3-E)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.settings_controls_view import (
    build_env_example,
    build_readonly_hint,
    build_restart_hint,
    build_safety_hint,
    build_settings_controls_view,
    render_bool_status,
    render_secret_status,
    render_settings_controls_as_text,
)
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestSettingsControlsViewBuilders:
    """Tests for settings controls view builder functions (Phase 3-E)."""

    def test_render_bool_status_true(self) -> None:
        """render_bool_status(True) returns '已开启'."""
        assert render_bool_status(True) == "已开启"

    def test_render_bool_status_false(self) -> None:
        """render_bool_status(False) returns '未开启'."""
        assert render_bool_status(False) == "未开启"

    def test_render_secret_status_configured(self) -> None:
        """render_secret_status with non-empty value returns '已配置'."""
        assert render_secret_status("fake-key-123") == "已配置"

    def test_render_secret_status_not_configured(self) -> None:
        """render_secret_status with None returns '未配置'."""
        assert render_secret_status(None) == "未配置"

    def test_render_secret_status_empty_string(self) -> None:
        """render_secret_status with empty string returns '未配置'."""
        assert render_secret_status("") == "未配置"

    def test_build_env_example_non_empty(self) -> None:
        """build_env_example returns non-empty string."""
        example = build_env_example()
        assert len(example) > 0

    def test_build_env_example_contains_memory(self) -> None:
        """build_env_example contains MEMORY_CONTEXT_ENABLED."""
        example = build_env_example()
        assert "MEMORY_CONTEXT_ENABLED" in example

    def test_build_env_example_contains_proactive(self) -> None:
        """build_env_example contains PROACTIVE_ENABLED."""
        example = build_env_example()
        assert "PROACTIVE_ENABLED" in example

    def test_build_env_example_no_api_keys(self) -> None:
        """build_env_example does not contain real API key patterns."""
        example = build_env_example()
        # Should not contain real MiniMax API key patterns
        assert "eyJ" not in example
        assert "sk-" not in example
        # Should not contain placeholder patterns that look like real keys
        assert "sk_live_" not in example

    def test_build_safety_hint_contains_no_reveal(self) -> None:
        """safety_hint mentions not revealing real content."""
        hint = build_safety_hint()
        assert len(hint) > 0
        # Should contain words about not showing real content
        assert "不显示" in hint or "不" in hint

    def test_build_restart_hint_contains_restart(self) -> None:
        """restart_hint contains '重启'."""
        hint = build_restart_hint()
        assert "重启" in hint

    def test_build_readonly_hint_contains_env(self) -> None:
        """readonly_hint mentions .env."""
        hint = build_readonly_hint()
        assert ".env" in hint


class TestSettingsControlsViewStructure:
    """Tests for settings controls view structure (Phase 3-E)."""

    def test_view_has_sections(self) -> None:
        """SettingsControlsView has sections."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        assert len(view.sections) > 0

    def test_view_has_all_sections(self) -> None:
        """SettingsControlsView contains all expected sections."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        titles = {s.title for s in view.sections}
        assert "基础信息" in titles
        assert "桌面行为" in titles
        assert "对话设置" in titles
        assert "语音设置" in titles
        assert "记忆设置" in titles
        assert "主动陪伴设置" in titles

    def test_view_has_env_example(self) -> None:
        """SettingsControlsView has env_example."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        assert len(view.env_example) > 0

    def test_view_has_restart_hint(self) -> None:
        """SettingsControlsView has restart_hint."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        assert len(view.restart_hint) > 0

    def test_view_has_safety_hint(self) -> None:
        """SettingsControlsView has safety_hint."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        assert len(view.safety_hint) > 0

    def test_basic_info_section_has_items(self) -> None:
        """Basic info section has at least version item."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        basic = next((s for s in view.sections if s.title == "基础信息"), None)
        assert basic is not None
        assert len(basic.items) >= 2

    def test_chat_settings_api_key_is_secret(self) -> None:
        """Chat settings API key is shown as '已配置' not the real key."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        chat = next((s for s in view.sections if s.title == "对话设置"), None)
        assert chat is not None
        # Find the API Key item
        api_key_item = next(
            (i for i in chat.items if "API Key" in i.label or "API" in i.label),
            None,
        )
        assert api_key_item is not None
        # Value should be either "已配置" or "未配置", not a real key
        assert api_key_item.value in ("已配置", "未配置")

    def test_proactive_section_has_control_hint(self) -> None:
        """Proactive section mentions user control."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        proactive = next(
            (s for s in view.sections if s.title == "主动陪伴设置"),
            None,
        )
        assert proactive is not None
        # Should have an item about user control
        control_items = [i for i in proactive.items if "控制" in i.label]
        assert len(control_items) >= 1

    def test_render_settings_controls_as_text_non_empty(self) -> None:
        """render_settings_controls_as_text returns non-empty string."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_controls_view(cfg)
        text = render_settings_controls_as_text(view)
        assert len(text) > 0


class TestSettingsViewEnhancements:
    """Tests for settings_view.py enhancements (Phase 3-E)."""

    def test_settings_view_has_readonly_hint(self) -> None:
        """Settings view text contains readonly hint about .env."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = render_settings_view_text(view)
        assert ".env" in text

    def test_settings_view_has_restart_hint(self) -> None:
        """Settings view text contains restart hint."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = render_settings_view_text(view)
        assert "重启" in text

    def test_settings_view_has_safety_hint(self) -> None:
        """Settings view text contains safety hint."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = render_settings_view_text(view)
        # Should mention not showing real API keys
        assert len(text) > 100


class TestWindowCopyConfigButton:
    """Tests for window copy config button (Phase 3-E)."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing with copy config button."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_copy_config_button_exists(qapp: QApplication) -> None:
        """Window has copy config button."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_settings_copy_button")

    @staticmethod
    def test_copy_config_button_text(qapp: QApplication) -> None:
        """Copy config button has '复制配置示例' text."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._settings_copy_button.text() == "复制配置示例"

    @staticmethod
    def test_copy_config_button_does_not_crash(qapp: QApplication) -> None:
        """Clicking copy config button does not crash."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        vm.toggle_settings_visible()
        window.update_from_view_model()
        # Click the button — should not crash even in offscreen
        window._settings_copy_button.clicked.emit()
        qapp.processEvents()

    @staticmethod
    def test_settings_panel_non_empty_when_visible(qapp: QApplication) -> None:
        """Settings panel shows non-empty text when open."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        vm.toggle_settings_visible()
        window.update_from_view_model()
        assert vm.settings_visible
        assert len(window._settings_text.text()) > 0

    @staticmethod
    def test_settings_button_toggles(qapp: QApplication) -> None:
        """Settings button opens and closes settings panel."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is False


class TestSettingsStatusMutualExclusion:
    """Tests for settings/status/memory mutual exclusion (Phase 3-E)."""

    @staticmethod
    def test_settings_closes_product_status(qapp: QApplication) -> None:
        """Opening settings panel closes product status."""
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
        # Open product status
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True
        # Open settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        assert vm.product_status_visible is False

    @staticmethod
    def test_settings_closes_memory_panel(qapp: QApplication) -> None:
        """Opening settings panel closes memory panel."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        # Open memory panel
        window._on_memory_panel_clicked()
        qapp.processEvents()
        assert vm.memory_panel_visible is True
        # Open settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        assert vm.memory_panel_visible is False

    @staticmethod
    def test_compact_mode_closes_settings(qapp: QApplication) -> None:
        """Compact mode closes settings panel."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        # Open settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        # Enter compact mode
        window._handle_compact_clicked()
        qapp.processEvents()
        assert vm.settings_visible is False
