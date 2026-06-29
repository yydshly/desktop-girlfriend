"""Memory UX v1 Probe (Phase 3-C).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

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

    # Verify delete button text
    if "删除这条记忆" in window._memory_delete_first_button.text():
        print("delete button: OK")
    else:
        print("delete button: FAIL")
        return 1

    # Verify onboarding still shows on first frame
    if window._onboarding_card.isVisible():
        print("onboarding visible: OK")
    else:
        print("onboarding visible: FAIL")
        return 1

    # Verify settings button still works
    vm2 = DesktopViewModel()
    vm2.set_settings_text(settings_text)
    window2 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window2.show()
    window2.update_from_view_model()
    window2._settings_button.clicked.emit()
    QApplication.instance().processEvents()
    if vm2.settings_visible and window2._settings_panel.isVisible():
        print("settings button: OK")
    else:
        print("settings button: FAIL")
        return 1

    # Verify status button still works
    def on_status() -> None:
        vm2.toggle_product_status_visible()
        window2.update_from_view_model()

    window3 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status,
    )
    window3.show()
    window3.update_from_view_model()
    window3._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if vm2.product_status_visible:
        print("status button: OK")
    else:
        print("status button: FAIL")
        return 1

    # Verify compact mode still works
    vm3 = DesktopViewModel()
    window4 = DesktopWindow(
        view_model=vm3,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window4.show()
    window4.update_from_view_model()
    window4._handle_compact_clicked()
    QApplication.instance().processEvents()
    if vm3.compact_mode and not window4._onboarding_card.isVisible():
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
