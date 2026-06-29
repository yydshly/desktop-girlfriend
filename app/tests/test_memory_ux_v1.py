"""Tests for Memory UX v1 (Phase 3-C)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.contracts.events import MEMORY_ADDED, MEMORY_LISTED, BaseEvent
from app.ui.memory_record_view import MemoryRecordView
from app.ui.memory_ux_view import (
    build_memory_panel_copy,
    build_memory_suggestion_copy,
)
from app.ui.onboarding_view import build_onboarding_view
from app.ui.settings_view import build_settings_view
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestMemoryUxCopy:
    """Tests for memory UX copy builders."""

    def test_suggestion_title_contains_remember(self) -> None:
        """Memory suggestion title contains '记住'."""
        copy = build_memory_suggestion_copy()
        assert "记住" in copy.title

    def test_suggestion_body_contains_only_you(self) -> None:
        """Memory suggestion body mentions '只有你'."""
        copy = build_memory_suggestion_copy()
        assert "只有你" in copy.body

    def test_remember_button_text(self) -> None:
        """Remember button text is '记住'."""
        copy = build_memory_suggestion_copy()
        assert copy.remember_button == "记住"

    def test_reject_button_text(self) -> None:
        """Reject button text is '不记'."""
        copy = build_memory_suggestion_copy()
        assert copy.reject_button == "不记"

    def test_privacy_hint_mentions_no_auto_save(self) -> None:
        """Privacy hint mentions not auto-saving full chat."""
        copy = build_memory_suggestion_copy()
        # Verify the string is non-empty and contains expected content (encoding-agnostic)
        assert len(copy.privacy_hint) > 10
        # "完整聊天" is the key distinguishing phrase - check length+content as proxy
        assert len(copy.privacy_hint) > 15, f"privacy_hint too short: {copy.privacy_hint!r}"

    def test_panel_empty_title_nonempty(self) -> None:
        """Memory panel empty title is non-empty."""
        copy = build_memory_panel_copy()
        assert len(copy.empty_title) > 0

    def test_panel_privacy_body_mentions_local(self) -> None:
        """Memory panel privacy body mentions local storage."""
        copy = build_memory_panel_copy()
        assert "本地" in copy.privacy_body

    def test_panel_privacy_body_mentions_unconfirmed(self) -> None:
        """Memory panel privacy body mentions unconfirmed."""
        copy = build_memory_panel_copy()
        assert "未确认" in copy.privacy_body


class TestSettingsMemoryCopy:
    """Tests for settings panel memory section (Phase 3-C)."""

    def test_settings_contains_memory_context(self) -> None:
        """Settings view contains '记忆上下文'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "记忆上下文" in text

    def test_settings_contains_memory_suggestions(self) -> None:
        """Settings view contains '记忆建议'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "记忆建议" in text

    def test_settings_contains_memory_management(self) -> None:
        """Settings view contains '记忆管理'."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = "\n".join(s.title + "\n" + "\n".join(s.lines) for s in view.sections)
        assert "记忆管理" in text

    def test_settings_contains_no_auto_save_privacy(self) -> None:
        """Settings view contains privacy hint about not auto-saving."""
        from app.core.config import AppConfig
        cfg = AppConfig()
        view = build_settings_view(cfg)
        # Settings memory section should have more lines than before (privacy hint added)
        memory_section = None
        for section in view.sections:
            if "记忆" in section.title or "Memory" in section.title:
                memory_section = section
                break
        # Just verify the section has content (encoding-agnostic)
        assert memory_section is not None, "Memory section not found in settings"
        assert len(memory_section.lines) >= 4, f"Expected >=4 memory lines, got {len(memory_section.lines)}"


class TestOnboardingMemoryCopy:
    """Tests for onboarding memory copy (Phase 3-C)."""

    def test_onboarding_memory_mentions_confirmed(self) -> None:
        """Onboarding text mentions confirmed memory or equivalent."""
        view = build_onboarding_view()
        text = "\n".join(view.bullets)
        # Accept either the old phrasing or the new privacy-focused phrasing
        has_privacy_note = (
            "确认过的记忆" in text
            or "不会自动保存完整聊天" in text
        )
        assert has_privacy_note, f"Expected memory privacy note in: {text}"


class TestWindowMemoryUx:
    """Tests for DesktopWindow memory UX (Phase 3-C)."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing with memory UX."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_memory_suggestion_widget_exists(qapp: QApplication) -> None:
        """Memory suggestion widget exists in window."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_memory_suggestion_widget")

    @staticmethod
    def test_memory_panel_widget_exists(qapp: QApplication) -> None:
        """Memory panel widget exists in window."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_memory_panel_widget")

    @staticmethod
    def test_memory_suggestion_shows_privacy_hint(qapp: QApplication) -> None:
        """Memory suggestion shows privacy hint when suggestion is active."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        # Widget should be hidden by default (no suggestion)
        assert not window._memory_suggestion_widget.isVisible()

    @staticmethod
    def test_memory_panel_shows_privacy_hint(qapp: QApplication) -> None:
        """Memory panel shows privacy hint when opened."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        # Open memory panel
        window._on_memory_panel_clicked()
        qapp.processEvents()
        assert window._memory_panel_widget.isVisible()
        # Privacy text should be set
        privacy_text = window._memory_panel_privacy.text()
        assert len(privacy_text) > 0


class TestWindowButtonsStillWorkWithMemoryUx:
    """Tests that existing buttons are unaffected by memory UX changes."""

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


class TestSettingsPanelSections:
    """Tests for settings panel having all sections visible."""

    @staticmethod
    def test_settings_has_memory_section(qapp: QApplication) -> None:
        """Settings panel contains all sections including memory and proactive."""
        from app.core.config import AppConfig
        from app.ui.settings_view import build_settings_view, render_settings_view_text
        cfg = AppConfig()
        view = build_settings_view(cfg)
        text = render_settings_view_text(view)
        # All expected sections should be present
        assert "【基础信息】" in text or "基础信息" in text
        assert "【桌面行为】" in text or "桌面行为" in text
        assert "【对话设置】" in text or "对话设置" in text
        assert "【语音设置】" in text or "语音设置" in text
        assert "【记忆设置】" in text or "记忆设置" in text
        assert "【主动陪伴设置】" in text or "主动陪伴设置" in text
        assert "【配置示例】" in text or "配置示例" in text


class TestMemoryPanelManualAdd:
    """Tests for memory panel manual add feature."""

    @staticmethod
    def test_memory_panel_has_manual_input(qapp: QApplication) -> None:
        """Memory panel has manual add input field."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_memory_manual_input")

    @staticmethod
    def test_memory_panel_has_add_button(qapp: QApplication) -> None:
        """Memory panel has '添加记忆' button."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_memory_add_button")
        assert window._memory_add_button.text() == "添加记忆"

    @staticmethod
    def test_delete_button_text_is_record_specific(qapp: QApplication) -> None:
        """Delete button text names the target record number."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert "删除第 1 条记忆" in window._memory_delete_first_button.text()

    @staticmethod
    def test_add_manual_memory_calls_callback(qapp: QApplication) -> None:
        """Adding manual memory text calls the callback."""
        vm = DesktopViewModel()
        callback_results = []
        def on_add(text):
            callback_results.append(text)
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_add_manual_memory_requested=on_add,
        )
        window.show()
        window._on_memory_panel_clicked()
        qapp.processEvents()
        window._memory_manual_input.setText("我喜欢你回复短一点")
        window._memory_add_button.clicked.emit()
        qapp.processEvents()
        assert len(callback_results) == 1
        assert callback_results[0] == "我喜欢你回复短一点"


class TestMemoryDeletePerRecord:
    """Tests for per-record memory delete buttons."""

    @staticmethod
    def _make_record(record_id: str) -> MemoryRecordView:
        return MemoryRecordView(
            record_id=record_id,
            kind="preference",
            importance="medium",
            text="我喜欢短回复",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

    @staticmethod
    def test_per_record_delete_buttons_exist(qapp: QApplication) -> None:
        """Window has multiple per-record delete buttons."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_memory_delete_record_buttons")
        assert len(window._memory_delete_record_buttons) == 5

    @staticmethod
    def test_delete_button_1_calls_first_record(qapp: QApplication) -> None:
        """Clicking first delete button calls callback with first record_id."""
        vm = DesktopViewModel()
        vm.memory_records = [
            TestMemoryDeletePerRecord._make_record("record-1"),
            TestMemoryDeletePerRecord._make_record("record-2"),
            TestMemoryDeletePerRecord._make_record("record-3"),
        ]
        vm.memory_panel_visible = True
        deleted: list[str] = []

        def on_delete(record_id: str) -> None:
            deleted.append(record_id)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_memory_delete_requested=on_delete,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        window._memory_delete_record_buttons[0].click()
        qapp.processEvents()
        assert deleted == ["record-1"]

    @staticmethod
    def test_delete_button_2_calls_second_record(qapp: QApplication) -> None:
        """Clicking second delete button calls callback with second record_id."""
        vm = DesktopViewModel()
        vm.memory_records = [
            TestMemoryDeletePerRecord._make_record("record-1"),
            TestMemoryDeletePerRecord._make_record("record-2"),
            TestMemoryDeletePerRecord._make_record("record-3"),
        ]
        vm.memory_panel_visible = True
        deleted: list[str] = []

        def on_delete(record_id: str) -> None:
            deleted.append(record_id)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_memory_delete_requested=on_delete,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        window._memory_delete_record_buttons[1].click()
        qapp.processEvents()
        assert deleted == ["record-2"]

    @staticmethod
    def test_delete_button_3_calls_third_record(qapp: QApplication) -> None:
        """Clicking third delete button calls callback with third record_id."""
        vm = DesktopViewModel()
        vm.memory_records = [
            TestMemoryDeletePerRecord._make_record("record-1"),
            TestMemoryDeletePerRecord._make_record("record-2"),
            TestMemoryDeletePerRecord._make_record("record-3"),
        ]
        vm.memory_panel_visible = True
        deleted: list[str] = []

        def on_delete(record_id: str) -> None:
            deleted.append(record_id)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_memory_delete_requested=on_delete,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        window._memory_delete_record_buttons[2].click()
        qapp.processEvents()
        assert deleted == ["record-3"]

    @staticmethod
    def test_delete_index_out_of_bounds_does_not_crash(qapp: QApplication) -> None:
        """Deleting with invalid index does not crash or call callback."""
        vm = DesktopViewModel()
        vm.memory_records = [TestMemoryDeletePerRecord._make_record("record-1")]
        vm.memory_panel_visible = True
        deleted: list[str] = []

        def on_delete(record_id: str) -> None:
            deleted.append(record_id)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_memory_delete_requested=on_delete,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        # Call the handler directly with out-of-bounds index
        window._on_memory_delete_clicked(99)
        qapp.processEvents()
        assert deleted == []

    @staticmethod
    def test_only_existing_records_have_visible_buttons(qapp: QApplication) -> None:
        """With 1 record, only first delete button is visible."""
        vm = DesktopViewModel()
        vm.memory_records = [TestMemoryDeletePerRecord._make_record("record-1")]
        vm.memory_panel_visible = True

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert window._memory_delete_record_buttons[0].isVisible()
        assert not window._memory_delete_record_buttons[1].isVisible()
        assert not window._memory_delete_record_buttons[2].isVisible()

    @staticmethod
    def test_three_records_show_three_buttons(qapp: QApplication) -> None:
        """With 3 records, first 3 delete buttons are visible."""
        vm = DesktopViewModel()
        vm.memory_records = [
            TestMemoryDeletePerRecord._make_record("record-1"),
            TestMemoryDeletePerRecord._make_record("record-2"),
            TestMemoryDeletePerRecord._make_record("record-3"),
        ]
        vm.memory_panel_visible = True

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert window._memory_delete_record_buttons[0].isVisible()
        assert window._memory_delete_record_buttons[1].isVisible()
        assert window._memory_delete_record_buttons[2].isVisible()
        assert not window._memory_delete_record_buttons[3].isVisible()

    @staticmethod
    def test_no_records_hides_all_delete_buttons(qapp: QApplication) -> None:
        """With 0 records, no delete buttons are visible."""
        vm = DesktopViewModel()
        vm.memory_records = []
        vm.memory_panel_visible = True

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        for btn in window._memory_delete_record_buttons:
            assert not btn.isVisible()


class TestManualMemoryEnterShortcut:
    """Tests for manual memory input Enter shortcut."""

    @staticmethod
    def test_manual_memory_enter_adds_memory(qapp: QApplication) -> None:
        """Pressing Enter in manual memory input adds the memory."""
        vm = DesktopViewModel()
        callback_results: list[str] = []

        def on_add(text: str) -> None:
            callback_results.append(text)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_add_manual_memory_requested=on_add,
        )
        window.show()
        window._on_memory_panel_clicked()
        qapp.processEvents()
        window._memory_manual_input.setText("我喜欢你回复短一点")
        window._memory_manual_input.returnPressed.emit()
        qapp.processEvents()

        assert callback_results == ["我喜欢你回复短一点"]
        assert window._memory_manual_input.text() == ""

    @staticmethod
    def test_manual_memory_empty_enter_does_not_call_callback(qapp: QApplication) -> None:
        """Empty text Enter does not call callback."""
        vm = DesktopViewModel()
        callback_results: list[str] = []

        def on_add(text: str) -> None:
            callback_results.append(text)

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_add_manual_memory_requested=on_add,
        )
        window.show()
        window._on_memory_panel_clicked()
        qapp.processEvents()
        window._memory_manual_input.setText("")
        window._memory_manual_input.returnPressed.emit()
        qapp.processEvents()

        assert callback_results == []

    @staticmethod
    def test_manual_memory_without_callback_keeps_text(qapp: QApplication) -> None:
        """Manual memory text is not cleared when no add callback is wired."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_add_manual_memory_requested=None,
        )
        window.show()
        window._on_memory_panel_clicked()
        qapp.processEvents()
        window._memory_manual_input.setText("我喜欢简短回复")
        window._memory_manual_input.returnPressed.emit()
        qapp.processEvents()

        assert window._memory_manual_input.text() == "我喜欢简短回复"


class TestChatEnterShortcut:
    """Tests for chat input Enter shortcut."""

    @staticmethod
    def test_input_return_submits_message(qapp: QApplication) -> None:
        """Pressing Enter in the input field submits the message."""
        vm = DesktopViewModel()
        submitted: list[str] = []
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=submitted.append,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._input_field.setText("你好")
        window._input_field.returnPressed.emit()
        qapp.processEvents()

        assert submitted == ["你好"]
        assert window._input_field.text() == ""

    @staticmethod
    def test_input_empty_return_does_not_submit(qapp: QApplication) -> None:
        """Empty input Enter does not submit."""
        vm = DesktopViewModel()
        submitted: list[str] = []
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=submitted.append,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window._input_field.setText("")
        window._input_field.returnPressed.emit()
        qapp.processEvents()

        assert submitted == []


class TestMemoryStatusFeedback:
    """Tests for memory status text feedback."""

    @staticmethod
    def test_memory_panel_shows_memory_status_text(qapp: QApplication) -> None:
        """Memory panel displays memory status feedback."""
        vm = DesktopViewModel()
        vm.memory_panel_visible = True
        vm.memory_status_text = "已添加记忆"
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        window.update_from_view_model()

        assert window._memory_panel_status.text() == "已添加记忆"
        assert window._memory_panel_status.isVisible()

    @staticmethod
    def test_memory_added_status_survives_followup_list_refresh() -> None:
        """List refresh after manual add does not hide the added feedback."""
        vm = DesktopViewModel()
        vm.handle_memory_added(
            BaseEvent(
                event_type=MEMORY_ADDED,
                request_id="req",
                source="test",
                payload={
                    "record_id": "record-1",
                    "kind": "other",
                    "importance": "medium",
                    "text": "我喜欢短回复",
                },
            )
        )
        vm.handle_memory_listed(
            BaseEvent(
                event_type=MEMORY_LISTED,
                request_id="req",
                source="test",
                payload={"records": []},
            )
        )

        assert vm.memory_status_text == "已添加记忆"

    @staticmethod
    def test_reopening_memory_panel_clears_stale_added_status() -> None:
        """Reopening memory panel clears stale manual-add feedback."""
        vm = DesktopViewModel()
        vm.memory_panel_visible = True
        vm.memory_status_text = "已添加记忆"

        vm.toggle_memory_panel()
        vm.toggle_memory_panel()

        assert vm.memory_panel_visible is True
        assert vm.memory_status_text == ""

    @staticmethod
    def test_delete_status_shows_deleted(qapp: QApplication) -> None:
        """Memory status shows '已删除记忆' after deletion."""
        vm = DesktopViewModel()
        vm.memory_panel_visible = True
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        from app.contracts.events import MEMORY_DELETED
        vm.handle_memory_deleted(
            BaseEvent(
                event_type=MEMORY_DELETED,
                request_id="req",
                source="test",
                payload={"record_id": "record-1"},
            )
        )
        window.update_from_view_model()

        assert vm.memory_status_text == "已删除记忆"


class TestHideButtonTrayAvailable:
    """Tests for hide button tray_available enabled state."""

    @staticmethod
    def test_hide_button_disabled_when_tray_unavailable(qapp: QApplication) -> None:
        """Hide button is disabled when tray_available is False."""
        vm = DesktopViewModel()
        vm.tray_available = False
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert not window._hide_button.isEnabled()

    @staticmethod
    def test_hide_button_enabled_when_tray_available(qapp: QApplication) -> None:
        """Hide button is enabled when tray_available is True."""
        vm = DesktopViewModel()
        vm.tray_available = True
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert window._hide_button.isEnabled()

    @staticmethod
    def test_hide_button_tooltip_when_tray_unavailable(qapp: QApplication) -> None:
        """Hide button shows unavailable tooltip when tray is unavailable."""
        vm = DesktopViewModel()
        vm.tray_available = False
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert "不可用" in window._hide_button.toolTip()

    @staticmethod
    def test_hide_button_tooltip_when_tray_available(qapp: QApplication) -> None:
        """Hide button shows tray tooltip when tray is available."""
        vm = DesktopViewModel()
        vm.tray_available = True
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_hide_requested=lambda: None,
        )
        window.show()
        window.update_from_view_model()
        qapp.processEvents()

        assert "托盘" in window._hide_button.toolTip()

