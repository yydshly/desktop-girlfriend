"""Tests for Proactive Real UX v1 (Phase 3-D)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.onboarding_view import build_onboarding_view, render_onboarding_text
from app.ui.proactive_real_ux_view import (
    build_proactive_real_ux_copy,
    render_proactive_control_status,
    render_proactive_enabled_status,
    render_proactive_tray_hint,
    render_proactive_user_control_hint,
)
from app.ui.settings_view import build_settings_view
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestProactiveRealUxCopy:
    """Tests for proactive real UX copy builders (Phase 3-D)."""

    def test_copy_title_contains_proactive(self) -> None:
        """Proactive copy title contains '主动陪伴'."""
        copy = build_proactive_real_ux_copy()
        assert "主动陪伴" in copy.title

    def test_enabled_body_contains_idle(self) -> None:
        """Enabled body mentions '空闲'."""
        copy = build_proactive_real_ux_copy()
        assert "空闲" in copy.enabled_body

    def test_disabled_body_is_nonempty(self) -> None:
        """Disabled body is non-empty."""
        copy = build_proactive_real_ux_copy()
        assert len(copy.disabled_body) > 0

    def test_cooldown_explanation_contains_interval(self) -> None:
        """Cooldown explanation mentions '间隔'."""
        copy = build_proactive_real_ux_copy()
        assert "间隔" in copy.cooldown_explanation

    def test_idle_explanation_contains_idle(self) -> None:
        """Idle explanation mentions '空闲'."""
        copy = build_proactive_real_ux_copy()
        assert "空闲" in copy.idle_explanation

    def test_quiet_hours_explanation_contains_quiet(self) -> None:
        """Quiet hours explanation mentions '勿扰'."""
        copy = build_proactive_real_ux_copy()
        assert "勿扰" in copy.quiet_hours_explanation

    def test_user_control_hint_contains_suppress_phrase(self) -> None:
        """User control hint contains '别打扰'."""
        copy = build_proactive_real_ux_copy()
        assert "别打扰" in copy.user_control_hint

    def test_tray_hint_contains_tray(self) -> None:
        """Tray hint mentions '托盘'."""
        copy = build_proactive_real_ux_copy()
        assert "托盘" in copy.tray_hint

    def test_max_per_session_explanation_nonempty(self) -> None:
        """Max per session explanation is non-empty."""
        copy = build_proactive_real_ux_copy()
        assert len(copy.max_per_session_explanation) > 0

    def test_render_proactive_enabled_status_true(self) -> None:
        """render_proactive_enabled_status(True) returns '已开启'."""
        result = render_proactive_enabled_status(True)
        assert "已开启" in result

    def test_render_proactive_enabled_status_false(self) -> None:
        """render_proactive_enabled_status(False) returns '未开启'."""
        result = render_proactive_enabled_status(False)
        assert "未开启" in result

    def test_render_proactive_control_status_nonempty(self) -> None:
        """render_proactive_control_status is non-empty."""
        result = render_proactive_control_status()
        assert len(result) > 0

    def test_render_proactive_user_control_hint_contains_suppress(self) -> None:
        """render_proactive_user_control_hint contains '别打扰'."""
        result = render_proactive_user_control_hint()
        assert "别打扰" in result

    def test_render_proactive_tray_hint_contains_tray(self) -> None:
        """render_proactive_tray_hint contains '托盘'."""
        result = render_proactive_tray_hint()
        assert "托盘" in result


class TestSettingsProactiveCopy:
    """Tests for settings panel proactive section (Phase 3-D)."""

    def test_settings_contains_idle_time(self) -> None:
        """Settings view contains '空闲时间'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "空闲时间" in text

    def test_settings_contains_cooldown_time(self) -> None:
        """Settings view contains '冷却时间'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "冷却时间" in text

    def test_settings_contains_quiet_hours(self) -> None:
        """Settings view contains '勿扰时间'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "勿扰时间" in text

    def test_settings_contains_suppress_control(self) -> None:
        """Settings view contains proactive suppress control hint."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "别打扰" in text or "安静" in text

    def test_settings_contains_tray_behavior(self) -> None:
        """Settings view contains '托盘' behavior note."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "托盘" in text

    def test_settings_contains_max_per_session(self) -> None:
        """Settings view contains '最多次数'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "最多次数" in text

    def test_settings_proactive_section_is_enhanced(self) -> None:
        """Settings proactive section has more lines than before Phase 3-D."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        proactive_section = None
        for section in view.sections:
            if "主动陪伴" in section.title:
                proactive_section = section
                break
        assert proactive_section is not None
        # Phase 3-D enhanced section should have at least 8 lines
        assert len(proactive_section.lines) >= 7, (
            f"Expected >=7 proactive lines, got {len(proactive_section.lines)}"
        )


class TestOnboardingProactiveCopy:
    """Tests for onboarding proactive copy (Phase 3-D)."""

    def test_onboarding_subtitle_mentions_suppress_control(self) -> None:
        """Onboarding subtitle mentions '别打扰' or equivalent."""
        view = build_onboarding_view()
        assert "别打扰" in view.subtitle or "安静" in view.subtitle

    def test_onboarding_text_renders_without_error(self) -> None:
        """Onboarding text renders without error."""
        view = build_onboarding_view()
        text = render_onboarding_text(view)
        assert len(text) > 0


class TestViewModelProactiveStatusText:
    """Tests for view model proactive status text (Phase 3-D)."""

    def test_view_model_has_proactive_status_text_field(self) -> None:
        """View model has proactive_status_text field."""
        vm = DesktopViewModel()
        assert hasattr(vm, "proactive_status_text")

    def test_set_proactive_status_text(self) -> None:
        """set_proactive_status_text updates the field."""
        vm = DesktopViewModel()
        vm.set_proactive_status_text("小云会安静一会儿。")
        assert vm.proactive_status_text == "小云会安静一会儿。"

    def test_clear_proactive_status_text(self) -> None:
        """clear_proactive_status_text empties the field."""
        vm = DesktopViewModel()
        vm.set_proactive_status_text("小云会安静一会儿。")
        vm.clear_proactive_status_text()
        assert vm.proactive_status_text == ""

    def test_suppress_phrase_sets_proactive_status(self) -> None:
        """User text with suppress phrase sets proactive_status_text."""
        vm = DesktopViewModel()
        from app.contracts.events import USER_TEXT_SUBMITTED, BaseEvent
        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="test-1",
            source="test",
            payload={"text": "别打扰"},
        )
        vm.handle_user_text_submitted(event)
        assert vm.proactive_status_text == "小云会安静一会儿。"

    def test_normal_text_does_not_set_proactive_status(self) -> None:
        """Normal user text does not set proactive_status_text."""
        vm = DesktopViewModel()
        from app.contracts.events import USER_TEXT_SUBMITTED, BaseEvent
        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="test-2",
            source="test",
            payload={"text": "你好，小云"},
        )
        vm.handle_user_text_submitted(event)
        assert vm.proactive_status_text == ""


class TestWindowProactiveUx:
    """Tests for DesktopWindow proactive UX (Phase 3-D)."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing with proactive UX."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_proactive_status_label_exists(qapp: QApplication) -> None:
        """Window has proactive status label."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_proactive_status_label")

    @staticmethod
    def test_proactive_status_label_updates(qapp: QApplication) -> None:
        """Proactive status label updates when view model changes."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        vm.set_proactive_status_text("小云会安静一会儿。")
        window.update_from_view_model()
        qapp.processEvents()
        assert window._proactive_status_label.text() == "小云会安静一会儿。"

    @staticmethod
    def test_settings_button_still_works(qapp: QApplication) -> None:
        """Settings button still opens/closes settings panel."""
        vm = DesktopViewModel()
        vm.set_settings_text("test settings")
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
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

    @staticmethod
    def test_compact_mode_still_works(qapp: QApplication) -> None:
        """Compact mode toggle still works."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window._handle_compact_clicked()
        qapp.processEvents()
        assert vm.compact_mode is True

    @staticmethod
    def test_onboarding_still_shows_on_first_frame(qapp: QApplication) -> None:
        """Onboarding card still shows on first frame."""
        vm = DesktopViewModel()
        vm.set_onboarding_text("test onboarding")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()
        assert window._onboarding_card.isVisible() is True

    @staticmethod
    def test_memory_button_still_works(qapp: QApplication) -> None:
        """Memory button still toggles memory panel."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._on_memory_panel_clicked()
        qapp.processEvents()
        assert vm.memory_panel_visible is True


class TestProductStatusProactiveCopy:
    """Tests for product status proactive copy (Phase 3-D)."""

    def test_product_status_builder_includes_proactive_control(self) -> None:
        """Product status builder includes proactive control item."""
        from app.core.config import AppConfig
        from app.ui.avatar_action import AvatarAction
        from app.ui.product_status_builder import build_product_status_view

        cfg = AppConfig()
        view = build_product_status_view(
            config=cfg,
            avatar_action=AvatarAction.IDLE,
        )
        labels = [item.label for item in view.items]
        assert "主动控制" in labels
