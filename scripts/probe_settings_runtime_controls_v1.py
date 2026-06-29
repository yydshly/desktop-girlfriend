"""Settings Runtime Controls v1 Probe (Phase 3-E).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.settings_controls_view import (
    build_env_example,
    build_readonly_hint,
    build_restart_hint,
    build_safety_hint,
    build_settings_controls_view,
)
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Settings Runtime Controls v1 Probe\n")

    # 1. Verify settings controls view builds correctly
    from app.core.config import AppConfig
    cfg = AppConfig()
    controls_view = build_settings_controls_view(cfg)
    if len(controls_view.sections) >= 6:
        print("settings controls view: OK")
    else:
        print(f"settings controls view: FAIL (got {len(controls_view.sections)} sections)")
        return 1

    # 2. Verify safety — API keys not revealed
    # Check that chat section has only "已配置"/"未配置" for API key
    chat_section = next(
        (s for s in controls_view.sections if s.title == "对话设置"),
        None,
    )
    if chat_section is None:
        print("settings controls view: FAIL (chat section not found)")
        return 1
    api_key_item = next(
        (i for i in chat_section.items if "API Key" in i.label),
        None,
    )
    if api_key_item is None:
        print("settings controls view: FAIL (API key item not found)")
        return 1
    if api_key_item.value in ("已配置", "未配置"):
        print("secret safety: OK")
    else:
        print(f"secret safety: FAIL (API key value: {api_key_item.value})")
        return 1

    # 3. Verify env example is safe (no real keys)
    example = build_env_example()
    if "eyJ" not in example and "sk-" not in example and len(example) > 50:
        print("env example: OK")
    else:
        print("env example: FAIL")
        return 1

    # 4. Verify restart hint
    restart_hint = build_restart_hint()
    if "重启" in restart_hint:
        print("restart hint: OK")
    else:
        print("restart hint: FAIL")
        return 1

    # 5. Verify readonly hint
    readonly_hint = build_readonly_hint()
    if ".env" in readonly_hint:
        print("readonly hint: OK")
    else:
        print("readonly hint: FAIL")
        return 1

    # 6. Verify safety hint
    safety_hint = build_safety_hint()
    if len(safety_hint) > 0:
        print("safety hint: OK")
    else:
        print("safety hint: FAIL")
        return 1

    # 7. Verify settings view has the hints
    settings_view = build_settings_view(cfg)
    settings_text = render_settings_view_text(settings_view)
    if "重启" in settings_text and ".env" in settings_text:
        print("settings view hints: OK")
    else:
        print("settings view hints: FAIL")
        return 1

    # 8. Verify window initializes and copy config button exists
    QApplication.instance() or QApplication(sys.argv)
    vm = DesktopViewModel()
    vm.set_settings_text(settings_text)
    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window.show()
    window.update_from_view_model()
    if window._name_label.text() == "小云":
        print("window: OK")
    else:
        print("window: FAIL")
        return 1

    if not hasattr(window, "_settings_copy_button"):
        print("copy config button: FAIL")
        return 1
    if window._settings_copy_button.text() == "复制配置示例":
        print("copy config button: OK")
    else:
        print(f"copy config button: FAIL (text: {window._settings_copy_button.text()})")
        return 1

    # 9. Verify copy config button does not crash
    vm.toggle_settings_visible()
    window.update_from_view_model()
    try:
        window._settings_copy_button.clicked.emit()
        QApplication.instance().processEvents()
        print("copy config: OK")
    except Exception as e:
        print(f"copy config: FAIL ({e})")
        return 1

    # 10. Verify settings panel is visible and has content
    if vm.settings_visible and len(window._settings_text.text()) > 0:
        print("panel content: OK")
    else:
        print("panel content: FAIL")
        return 1

    # 11. Verify mutual exclusion — settings closes product status
    def on_status() -> None:
        vm2.toggle_product_status_visible()
        window2.update_from_view_model()

    vm2 = DesktopViewModel()
    window2 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status,
    )
    window2.show()
    window2.update_from_view_model()
    # Open product status first
    window2._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    # Open settings — should close product status
    window2._settings_button.clicked.emit()
    QApplication.instance().processEvents()
    if vm2.settings_visible and not vm2.product_status_visible:
        print("panel compatibility: OK")
    else:
        print("panel compatibility: FAIL")
        return 1

    # 12. Verify compact mode closes settings
    vm3 = DesktopViewModel()
    window3 = DesktopWindow(
        view_model=vm3,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window3.show()
    window3.update_from_view_model()
    window3._settings_button.clicked.emit()
    QApplication.instance().processEvents()
    assert vm3.settings_visible is True
    window3._handle_compact_clicked()
    QApplication.instance().processEvents()
    if not vm3.settings_visible:
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
