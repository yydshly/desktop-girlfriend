"""Memory UX v1 Probe (Phase 3-C).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.brain.memory.controller import MemorySuggestionController
from app.brain.memory.repository import LocalJsonMemoryRepository
from app.brain.memory.runtime import create_local_memory_runtime
from app.contracts.events import MEMORY_ADD_REQUESTED, MEMORY_ADDED, BaseEvent
from app.core.event_bus import EventBus
from app.ui.memory_record_view import MemoryRecordView
from app.ui.memory_ux_view import (
    build_memory_suggestion_copy,
)
from app.ui.onboarding_view import build_onboarding_view, render_onboarding_text
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Memory UX v1 Probe\n")

    # Test memory UX copy builders
    suggestion = build_memory_suggestion_copy()
    if len(suggestion.title) > 0 and len(suggestion.body) > 10:
        print("memory copy: OK")
    else:
        print("memory copy: FAIL")
        return 1

    if len(suggestion.privacy_hint) > 10:
        print("privacy copy: OK")
    else:
        print("privacy copy: FAIL")
        return 1

    # Test settings view memory section
    from app.core.config import AppConfig
    cfg = AppConfig()
    settings_view = build_settings_view(cfg)
    settings_text = render_settings_view_text(settings_view)
    # Find memory section by title
    memory_section = None
    for section in settings_view.sections:
        if "记忆" in section.title or "Memory" in section.title:
            memory_section = section
            break
    if memory_section is None:
        print("settings copy: FAIL (memory section not found)")
        return 1
    # Check memory-related lines exist
    lines_text = "\n".join(memory_section.lines)
    has_context = "memory_context" in lines_text.lower() or "记忆上下文" in lines_text
    has_suggestions = "memory_suggestion" in lines_text.lower() or "记忆建议" in lines_text
    has_management = "memory_management" in lines_text.lower() or "记忆管理" in lines_text
    if has_context and has_suggestions and has_management:
        print("settings copy: OK")
    else:
        print("settings copy: FAIL")
        return 1

    # Settings privacy section should have substantial content (more than before Phase 3-C)
    privacy_lines = [line for line in memory_section.lines if len(line) > 20]
    if len(privacy_lines) >= 1:
        print("settings privacy: OK")
    else:
        print("settings privacy: FAIL")
        return 1

    # Test all settings sections are present
    if "记忆设置" in settings_text and "主动陪伴设置" in settings_text and "配置示例" in settings_text:
        print("settings sections: OK")
    else:
        print("settings sections: FAIL")
        return 1

    # Test onboarding memory copy
    onboarding = build_onboarding_view()
    onboarding_text = render_onboarding_text(onboarding)
    # Verify onboarding has the memory bullet point (non-empty, substantial)
    memory_bullets = [b for b in onboarding.bullets if "记忆" in b or "memory" in b.lower() or "确认" in b]
    if len(memory_bullets) > 0 and len(memory_bullets[0]) > 5:
        print("onboarding: OK")
    else:
        print("onboarding: FAIL")
        return 1

    QApplication.instance() or QApplication(sys.argv)

    # Test window initialization with memory UX
    vm = DesktopViewModel()
    vm.set_onboarding_text(onboarding_text)
    vm.set_settings_text(settings_text)

    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window.show()
    window.update_from_view_model()
    QApplication.instance().processEvents()

    # Verify memory widgets exist
    if hasattr(window, "_memory_suggestion_widget") and hasattr(window, "_memory_panel_widget"):
        print("memory widgets: OK")
    else:
        print("memory widgets: FAIL")
        return 1

    # Verify memory panel shows privacy hint when opened
    window._on_memory_panel_clicked()
    QApplication.instance().processEvents()
    privacy = window._memory_panel_privacy.text()
    if len(privacy) > 0 and ("本地" in privacy or "不会" in privacy):
        print("memory panel privacy: OK")
    else:
        print("memory panel privacy: FAIL")
        return 1

    # Verify manual add input and button exist
    if hasattr(window, "_memory_manual_input") and hasattr(window, "_memory_add_button"):
        print("manual add memory: OK")
    else:
        print("manual add memory: FAIL")
        return 1

    # Verify delete button text is per-record
    if "删除第 1 条记忆" in window._memory_delete_first_button.text():
        print("delete button: OK")
    else:
        print("delete button: FAIL")
        return 1

    # Test per-record delete buttons exist
    if hasattr(window, "_memory_delete_record_buttons") and len(window._memory_delete_record_buttons) >= 5:
        print("memory delete per-record: OK")
    else:
        print("memory delete per-record: FAIL")
        return 1

    # Test per-record delete with 3 records - click 2nd button
    vm.memory_records = [
        MemoryRecordView(
            record_id="record-1", kind="preference", importance="medium",
            text="我喜欢短回复", created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        ),
        MemoryRecordView(
            record_id="record-2", kind="preference", importance="medium",
            text="我喜欢长回复", created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        ),
        MemoryRecordView(
            record_id="record-3", kind="preference", importance="medium",
            text="我喜欢emoji", created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00",
        ),
    ]
    vm.memory_panel_visible = True
    deleted: list[str] = []

    def on_delete(record_id: str) -> None:
        deleted.append(record_id)

    window2 = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_memory_delete_requested=on_delete,
    )
    window2.show()
    window2.update_from_view_model()
    QApplication.instance().processEvents()

    # Verify first 3 buttons are visible
    if (
        window2._memory_delete_record_buttons[0].isVisible()
        and window2._memory_delete_record_buttons[1].isVisible()
        and window2._memory_delete_record_buttons[2].isVisible()
        and not window2._memory_delete_record_buttons[3].isVisible()
    ):
        print("memory delete per-record visibility: OK")
    else:
        print("memory delete per-record visibility: FAIL")
        return 1

    # Click 2nd delete button using real mouse click, verify it calls record-2
    QTest.mouseClick(window2._memory_delete_record_buttons[1], Qt.MouseButton.LeftButton)
    QApplication.instance().processEvents()
    if deleted == ["record-2"]:
        print("memory delete per-record index 2: OK")
    else:
        print(f"memory delete per-record index 2: FAIL (got {deleted})")
        return 1

    # Test manual memory keyboard input focus
    vm3 = DesktopViewModel()
    window3 = DesktopWindow(
        view_model=vm3,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window3.show()
    window3._on_memory_panel_clicked()
    QApplication.instance().processEvents()
    if QApplication.focusWidget() is window3._memory_manual_input:
        print("memory manual input focus: OK")
    else:
        print(f"memory manual input focus: FAIL (focus={QApplication.focusWidget()})")
        return 1

    # Test real keyboard typing in memory input
    QTest.mouseClick(window3._memory_manual_input, Qt.MouseButton.LeftButton)
    QApplication.instance().processEvents()
    QTest.keyClicks(window3._memory_manual_input, "test idol")
    QApplication.instance().processEvents()
    if window3._memory_manual_input.text() == "test idol":
        print("memory manual input key typing: OK")
    else:
        print(f"memory manual input key typing: FAIL (got {window3._memory_manual_input.text()!r})")
        return 1

    # Test manual memory Enter shortcut with real keyboard
    callback_results: list[str] = []

    def on_add(text: str) -> None:
        callback_results.append(text)

    vm4 = DesktopViewModel()
    window4 = DesktopWindow(
        view_model=vm4,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_add_manual_memory_requested=on_add,
    )
    window4.show()
    window4._on_memory_panel_clicked()
    QApplication.instance().processEvents()
    input_widget = window4._memory_manual_input
    QTest.mouseClick(input_widget, Qt.MouseButton.LeftButton)
    QApplication.instance().processEvents()
    QTest.keyClicks(input_widget, "test idol")
    QApplication.instance().processEvents()
    QTest.keyClick(input_widget, Qt.Key.Key_Return)
    QApplication.instance().processEvents()
    if callback_results == ["test idol"] and input_widget.text() == "":
        print("memory manual input enter submit: OK")
    else:
        print(f"memory manual input enter submit: FAIL (callback={callback_results}, input={input_widget.text()!r})")
        return 1

    # Test full persistence chain: EventBus → Controller → Repository
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = LocalJsonMemoryRepository(Path(tmpdir) / "memory.json")
        runtime = create_local_memory_runtime(repo)
        bus = EventBus()
        dispatched: list[BaseEvent] = []

        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=bus.subscribe,
            unsubscribe=bus.unsubscribe,
            dispatch_event=lambda e: dispatched.append(e),
        )
        controller.start()

        # Publish MEMORY_ADD_REQUESTED directly (simulating what DesktopWindow does)
        bus.publish(
            BaseEvent(
                event_type=MEMORY_ADD_REQUESTED,
                request_id="probe-req-1",
                source="probe",
                payload={"text": "test memory persistence"},
            )
        )

        added_events = [e for e in dispatched if e.event_type == MEMORY_ADDED]
        if len(added_events) == 1 and added_events[0].payload["text"] == "test memory persistence":
            print("memory add persistence chain: OK")
        else:
            print(f"memory add persistence chain: FAIL (events={[(e.event_type, e.payload) for e in dispatched]})")
            return 1

        records = repo.list_active()
        if len(records) == 1 and records[0].text == "test memory persistence" and records[0].source == "manual_ui":
            print("memory add repository write: OK")
        else:
            print(f"memory add repository write: FAIL (records={[(r.text, r.source) for r in records]})")
            return 1

    # Test chat Enter shortcut with real keyboard
    submitted: list[str] = []
    vm5 = DesktopViewModel()
    window5 = DesktopWindow(
        view_model=vm5,
        on_user_text_submitted=submitted.append,
        on_conversation_cleared=lambda: None,
    )
    window5.show()
    window5.activateWindow()
    window5.raise_()
    QApplication.instance().processEvents()
    chat_input = window5._input_field
    QTest.mouseClick(chat_input, Qt.MouseButton.LeftButton)
    QApplication.instance().processEvents()
    QTest.keyClicks(chat_input, "hello")
    QApplication.instance().processEvents()
    QTest.keyClick(chat_input, Qt.Key.Key_Return)
    QApplication.instance().processEvents()
    if submitted == ["hello"] and chat_input.text() == "":
        print("chat enter shortcut: OK")
    else:
        print(f"chat enter shortcut: FAIL (submitted={submitted})")
        return 1

    # Test memory status feedback
    vm5 = DesktopViewModel()
    window5 = DesktopWindow(
        view_model=vm5,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window5.show()
    vm5.handle_memory_added(
        BaseEvent(
            event_type=MEMORY_ADDED,
            request_id="req",
            source="test",
            payload={"record_id": "record-1", "kind": "other", "importance": "medium", "text": "我喜欢短回复"},
        )
    )
    # Open memory panel so status label is visible
    window5._on_memory_panel_clicked()
    window5.update_from_view_model()
    QApplication.instance().processEvents()
    if window5._memory_panel_status.text() == "已添加记忆" and window5._memory_panel_status.isVisible():
        print("memory status feedback: OK")
    else:
        print(f"memory status feedback: FAIL (text={window5._memory_panel_status.text()!r}, visible={window5._memory_panel_status.isVisible()})")
        return 1

    # Test hide button tray_available
    vm6 = DesktopViewModel()
    vm6.tray_available = False
    window6 = DesktopWindow(
        view_model=vm6,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_hide_requested=lambda: None,
    )
    window6.show()
    window6.update_from_view_model()
    QApplication.instance().processEvents()
    if not window6._hide_button.isEnabled():
        print("hide button tray unavailable: OK")
    else:
        print("hide button tray unavailable: FAIL")
        return 1

    vm7 = DesktopViewModel()
    vm7.tray_available = True
    window7 = DesktopWindow(
        view_model=vm7,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_hide_requested=lambda: None,
    )
    window7.show()
    window7.update_from_view_model()
    QApplication.instance().processEvents()
    if window7._hide_button.isEnabled():
        print("hide button tray available: OK")
    else:
        print("hide button tray available: FAIL")
        return 1

    # Verify onboarding still shows on first frame
    if window._onboarding_card.isVisible():
        print("onboarding visible: OK")
    else:
        print("onboarding visible: FAIL")
        return 1

    # Verify settings button still works
    vm8 = DesktopViewModel()
    vm8.set_settings_text(settings_text)
    window8 = DesktopWindow(
        view_model=vm8,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window8.show()
    window8.update_from_view_model()
    window8._settings_button.clicked.emit()
    QApplication.instance().processEvents()
    if vm8.settings_visible and window8._settings_panel.isVisible():
        print("settings button: OK")
    else:
        print("settings button: FAIL")
        return 1

    # Verify status button still works
    def on_status() -> None:
        vm8.toggle_product_status_visible()
        window8.update_from_view_model()

    window9 = DesktopWindow(
        view_model=vm8,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status,
    )
    window9.show()
    window9.update_from_view_model()
    window9._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if vm8.product_status_visible:
        print("status button: OK")
    else:
        print("status button: FAIL")
        return 1

    # Verify compact mode still works
    vm10 = DesktopViewModel()
    window10 = DesktopWindow(
        view_model=vm10,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window10.show()
    window10.update_from_view_model()
    window10._handle_compact_clicked()
    QApplication.instance().processEvents()
    if vm10.compact_mode and not window10._onboarding_card.isVisible():
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
