"""Tests for first run onboarding (Phase 3-B)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.onboarding_view import (
    build_onboarding_view,
    render_onboarding_text,
)
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestOnboardingView:
    """Tests for onboarding view module."""

    def test_build_onboarding_view_title_contains_xiaoyun(self) -> None:
        """Onboarding title contains the companion name."""
        view = build_onboarding_view(companion_name="小云")
        assert "小云" in view.title

    def test_build_onboarding_view_bullets_nonempty(self) -> None:
        """Onboarding bullets are non-empty."""
        view = build_onboarding_view()
        assert len(view.bullets) > 0

    def test_render_onboarding_text_contains_voice_input(self) -> None:
        """Rendered text contains '语音输入'."""
        view = build_onboarding_view()
        text = render_onboarding_text(view)
        assert "语音输入" in text

    def test_render_onboarding_text_contains_settings(self) -> None:
        """Rendered text contains '设置'."""
        view = build_onboarding_view()
        text = render_onboarding_text(view)
        assert "设置" in text

    def test_render_onboarding_text_contains_status(self) -> None:
        """Rendered text contains '状态'."""
        view = build_onboarding_view()
        text = render_onboarding_text(view)
        assert "状态" in text

    def test_render_onboarding_text_contains_tray(self) -> None:
        """Rendered text contains '托盘'."""
        view = build_onboarding_view()
        text = render_onboarding_text(view)
        assert "托盘" in text


class TestViewModelOnboarding:
    """Tests for ViewModel onboarding fields and methods."""

    def test_default_onboarding_visible_is_true(self) -> None:
        """ViewModel defaults onboarding_visible to True."""
        vm = DesktopViewModel()
        assert vm.onboarding_visible is True

    def test_set_onboarding_text(self) -> None:
        """set_onboarding_text updates onboarding_text."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding content")
        assert vm.onboarding_text == "test onboarding content"

    def test_dismiss_onboarding(self) -> None:
        """dismiss_onboarding sets onboarding_visible to False."""
        vm = DesktopViewModel()
        assert vm.onboarding_visible is True
        vm.dismiss_onboarding()
        assert vm.onboarding_visible is False

    def test_open_settings_from_onboarding(self) -> None:
        """open_settings_from_onboarding closes onboarding and opens settings."""
        vm = DesktopViewModel()
        assert vm.onboarding_visible is True
        assert vm.settings_visible is False
        vm.open_settings_from_onboarding()
        assert vm.onboarding_visible is False
        assert vm.settings_visible is True
        assert vm.product_status_visible is False

    def test_compact_mode_closes_onboarding(self) -> None:
        """Entering compact mode closes onboarding."""
        vm = DesktopViewModel()
        assert vm.onboarding_visible is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        assert vm.onboarding_visible is False


class TestWindowOnboardingCard:
    """Tests for DesktopWindow onboarding card."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_onboarding_card_visible_by_default(qapp: QApplication) -> None:
        """Onboarding card is visible by default."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        assert window._onboarding_card.isVisible() is True

    @staticmethod
    def test_onboarding_card_hidden_after_dismiss(qapp: QApplication) -> None:
        """Onboarding card is hidden after clicking '知道了'."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._onboarding_dismiss_button.clicked.emit()
        qapp.processEvents()
        assert vm.onboarding_visible is False

    @staticmethod
    def test_open_settings_from_onboarding(qapp: QApplication) -> None:
        """Clicking '打开设置' opens settings panel and hides onboarding."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._onboarding_settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.onboarding_visible is False
        assert vm.settings_visible is True
        assert vm.product_status_visible is False


class TestWindowButtonsStillWorkWithOnboarding:
    """Tests that existing buttons are unaffected by onboarding."""

    @staticmethod
    def test_status_button_still_works(qapp: QApplication) -> None:
        """Status button still opens/closes product status panel."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")

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

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

    @staticmethod
    def test_settings_button_still_works(qapp: QApplication) -> None:
        """Settings button still opens/closes settings panel."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window._settings_button.clicked.emit()
        qapp.processEvents()
        assert vm.settings_visible is True

    @staticmethod
    def test_hide_button_exists(qapp: QApplication) -> None:
        """Hide button still exists and is accessible."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        assert hasattr(window, "_hide_button")
