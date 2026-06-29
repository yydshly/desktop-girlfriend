"""Tests for settings runtime controls (Phase 2-E)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.settings_view import (
    build_settings_view,
    render_enabled,
    render_provider_mode,
    render_settings_view_text,
)
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestRenderHelpers:
    """Tests for render_enabled and render_provider_mode helpers."""

    def test_render_enabled_true(self) -> None:
        """render_enabled(True) returns '已启用'."""
        assert render_enabled(True) == "已启用"

    def test_render_enabled_false(self) -> None:
        """render_enabled(False) returns '未启用'."""
        assert render_enabled(False) == "未启用"

    def test_render_provider_mode_fake(self) -> None:
        """render_provider_mode('fake') includes '测试模式'."""
        result = render_provider_mode("fake")
        assert "fake" in result
        assert "测试模式" in result

    def test_render_provider_mode_real(self) -> None:
        """render_provider_mode('minimax') returns 'minimax'."""
        assert render_provider_mode("minimax") == "minimax"


class TestSettingsView:
    """Tests for build_settings_view and render_settings_view_text."""

    def test_settings_view_has_basic_section(self) -> None:
        """Settings view includes a basic info section."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        section_titles = [s.title for s in view.sections]
        assert "基础信息" in section_titles

    def test_settings_view_has_memory_section(self) -> None:
        """Settings view includes a memory settings section."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        section_titles = [s.title for s in view.sections]
        assert "记忆设置" in section_titles

    def test_settings_view_has_proactive_section(self) -> None:
        """Settings view includes a proactive settings section."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        section_titles = [s.title for s in view.sections]
        assert "主动陪伴设置" in section_titles

    def test_settings_view_has_example_section(self) -> None:
        """Settings view includes a configuration example section."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        section_titles = [s.title for s in view.sections]
        assert "配置示例" in section_titles

    def test_render_settings_view_text_does_not_leak_api_key(self) -> None:
        """Rendered settings text does not contain real API key values."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        # Config with a fake key set to a non-trivial value
        cfg.minimax_api_key = "sk-abcdefghijk1234567890"
        cfg.mimo_api_key = "sk-xyz1234567890abcdefgh"
        view = build_settings_view(cfg)
        text = render_settings_view_text(view)
        # Should show "已配置" but NOT the actual key value
        assert "sk-abcdefghijk1234567890" not in text
        assert "sk-xyz1234567890abcdefgh" not in text
        assert "已配置" in text


class TestViewModelSettingsMethods:
    """Tests for ViewModel settings toggle methods."""

    def test_toggle_settings_visible(self) -> None:
        """toggle_settings_visible flips settings_visible."""
        vm = DesktopViewModel()
        assert vm.settings_visible is False
        vm.toggle_settings_visible()
        assert vm.settings_visible is True
        vm.toggle_settings_visible()
        assert vm.settings_visible is False

    def test_enter_settings_closes_product_status(self) -> None:
        """Opening settings closes product status panel."""
        vm = DesktopViewModel()
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        vm.toggle_settings_visible()
        assert vm.settings_visible is True
        assert vm.product_status_visible is False

    def test_enter_product_status_closes_settings(self) -> None:
        """Opening product status closes settings panel."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        vm.toggle_settings_visible()
        assert vm.settings_visible is True
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        assert vm.settings_visible is False

    def test_toggle_settings_does_not_affect_memory_panel(self) -> None:
        """Toggling settings does not affect memory panel visibility."""
        vm = DesktopViewModel()
        vm.toggle_memory_panel()
        assert vm.memory_panel_visible is True
        vm.toggle_settings_visible()
        assert vm.settings_visible is True
        assert vm.memory_panel_visible is True  # memory panel unaffected

    def test_toggle_product_status_does_not_affect_memory_panel(self) -> None:
        """Toggling product status does not affect memory panel visibility."""
        vm = DesktopViewModel()
        vm.toggle_memory_panel()
        assert vm.memory_panel_visible is True
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        assert vm.memory_panel_visible is True  # memory panel unaffected

    def test_compact_mode_closes_settings(self) -> None:
        """Entering compact mode closes settings panel."""
        vm = DesktopViewModel()
        vm.toggle_settings_visible()
        assert vm.settings_visible is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        assert vm.settings_visible is False

    def test_compact_mode_closes_product_status(self) -> None:
        """Entering compact mode closes product status panel."""
        vm = DesktopViewModel()
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        assert vm.product_status_visible is False

    def test_set_settings_text(self) -> None:
        """set_settings_text updates settings_text."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings content")
        assert vm.settings_text == "test settings content"


class TestWindowSettingsPanel:
    """Tests for DesktopWindow settings panel."""

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
    def test_settings_button_present(qapp: QApplication) -> None:
        """Settings button exists in aux button row."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_settings_button")
        assert window._settings_button.text() == "设置"

    @staticmethod
    def test_settings_button_first_click_expands(qapp: QApplication) -> None:
        """First click on settings button opens the settings panel."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings content")

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
        assert window._settings_panel.isVisible() is True

    @staticmethod
    def test_settings_button_second_click_collapses(qapp: QApplication) -> None:
        """Second click on settings button closes the settings panel."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings content")

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

    @staticmethod
    def test_settings_panel_shows_settings_text(qapp: QApplication) -> None:
        """Settings panel displays the settings text."""
        vm = DesktopViewModel()
        vm.set_settings_text("【基础信息】\n版本：0.1.0-rc.3")

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window._settings_button.clicked.emit()
        qapp.processEvents()

        assert "0.1.0-rc.3" in vm.settings_text

    @staticmethod
    def test_settings_does_not_break_status_button(qapp: QApplication) -> None:
        """Opening settings does not break status button functionality."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        def on_status() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
            )
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
        )
        window.show()

        # Open settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True

        # Close settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is False

        # Status button should still work
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

    @staticmethod
    def test_settings_status_mutual_exclusion_settings_first(qapp: QApplication) -> None:
        """Settings and product status panels are mutually exclusive - settings opens first."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        def on_status() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
            )
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
        )
        window.show()

        # Open settings
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        assert vm.product_status_visible is False
        assert window._settings_panel.isVisible() is True
        assert window._product_status_panel.isVisible() is False

        # Click status - settings should close, status should open
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.settings_visible is False
        assert vm.product_status_visible is True
        assert window._settings_panel.isVisible() is False
        assert window._product_status_panel.isVisible() is True

        # Click settings - status should close, settings should open
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        assert vm.product_status_visible is False
        assert window._settings_panel.isVisible() is True
        assert window._product_status_panel.isVisible() is False

    @staticmethod
    def test_settings_status_mutual_exclusion_status_first(qapp: QApplication) -> None:
        """Settings and product status panels are mutually exclusive - status opens first."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        def on_status() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
            )
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status,
        )
        window.show()

        # Open status first
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True
        assert vm.settings_visible is False
        assert window._product_status_panel.isVisible() is True
        assert window._settings_panel.isVisible() is False

        # Click settings - status should close, settings should open
        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True
        assert vm.product_status_visible is False
        assert window._settings_panel.isVisible() is True
        assert window._product_status_panel.isVisible() is False

        # Click status again - settings should close, status should open
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True
        assert vm.settings_visible is False
        assert window._product_status_panel.isVisible() is True
        assert window._settings_panel.isVisible() is False

    @staticmethod
    def test_compact_mode_hides_settings_button(qapp: QApplication) -> None:
        """Compact mode hides the settings button."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._settings_button.isVisible()

        window._handle_compact_clicked()
        qapp.processEvents()

        assert not window._settings_button.isVisible()
