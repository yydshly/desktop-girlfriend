r"""Product status panel probe script (V11-A).

Run locally (no Qt, no network, no LLM, no TTS, no memory):
    .venv\Scripts\python.exe scripts/probe_product_status.py
"""

from __future__ import annotations

from app.core.config import get_config
from app.ui.avatar_action import AvatarAction
from app.ui.product_status_builder import build_product_status_view
from app.ui.view_model import DesktopViewModel


def main() -> None:
    """Run product status panel probe flow."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    # 1. Create AppConfig and DesktopViewModel
    config = get_config()
    vm = DesktopViewModel()

    # 2. Initial state: product_status_visible should be False
    assert vm.product_status_visible is False, f"Expected False, got {vm.product_status_visible}"
    print("[OK] Initial: product_status_visible=False")

    # 3. Build and set product status view
    view = build_product_status_view(config=config, avatar_action=AvatarAction.IDLE)
    vm.set_product_status_view(view)
    assert vm.product_status_text != "", "product_status_text should be non-empty after set"
    print(f"[OK] set_product_status_view: text non-empty ({len(vm.product_status_text)} chars)")

    # 4. Toggle visible
    vm.toggle_product_status_visible()
    assert vm.product_status_visible is True, f"Expected True, got {vm.product_status_visible}"
    print("[OK] toggle_product_status_visible: product_status_visible=True")

    # 5. Confirm product_status_text contains key items
    assert "对话" in vm.product_status_text, "product_status_text should contain 对话"
    assert "主动陪伴" in vm.product_status_text, "product_status_text should contain 主动陪伴"
    assert "当前角色状态" in vm.product_status_text, "product_status_text should contain 当前角色状态"
    print("[OK] product_status_text contains 对话 / 主动陪伴 / 当前角色状态")

    # 6. Toggle back
    vm.toggle_product_status_visible()
    assert vm.product_status_visible is False
    print("[OK] toggle_product_status_visible: product_status_visible=False (toggle back)")

    print("PASS")


if __name__ == "__main__":
    main()
