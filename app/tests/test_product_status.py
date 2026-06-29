"""Tests for product status panel (V11-A)."""

from __future__ import annotations

from app.contracts.states import AppState
from app.core.config import get_config
from app.ui.avatar_action import AvatarAction
from app.ui.product_status import (
    ProductStatusItem,
    ProductStatusView,
    render_status_item,
    render_status_view,
)
from app.ui.product_status_builder import build_product_status_view
from app.ui.view_model import DesktopViewModel


class TestProductStatusItem:
    """Tests for ProductStatusItem and render functions."""

    def test_render_enabled_item_with_detail(self) -> None:
        """ProductStatusItem enabled=True renders with ✅."""
        item = ProductStatusItem("对话", True, "已启用")
        result = render_status_item(item)
        assert result == "✅ 对话：已启用"

    def test_render_disabled_item(self) -> None:
        """ProductStatusItem enabled=False renders with ❌."""
        item = ProductStatusItem("记忆上下文", False)
        result = render_status_item(item)
        assert result == "❌ 记忆上下文"

    def test_render_item_without_detail(self) -> None:
        """ProductStatusItem without detail renders just prefix + label."""
        item = ProductStatusItem("主动陪伴", True)
        result = render_status_item(item)
        assert result == "✅ 主动陪伴"


class TestRenderStatusView:
    """Tests for render_status_view."""

    def test_render_multiple_items(self) -> None:
        """render_status_view renders multiple items separated by newlines."""
        view = ProductStatusView(
            items=(
                ProductStatusItem("对话", True, "已启用"),
                ProductStatusItem("记忆上下文", False),
                ProductStatusItem("主动陪伴", True),
            )
        )
        result = render_status_view(view)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[0] == "✅ 对话：已启用"
        assert lines[1] == "❌ 记忆上下文"
        assert lines[2] == "✅ 主动陪伴"


class TestBuildProductStatusView:
    """Tests for build_product_status_view."""

    def test_contains_dialogue(self) -> None:
        """build_product_status_view includes 对话 item."""
        config = get_config()
        view = build_product_status_view(config=config, avatar_action=AvatarAction.IDLE)
        labels = [item.label for item in view.items]
        assert "对话" in labels

    def test_contains_memory_context(self) -> None:
        """build_product_status_view includes 记忆上下文 item."""
        config = get_config()
        view = build_product_status_view(config=config, avatar_action=AvatarAction.IDLE)
        labels = [item.label for item in view.items]
        assert "记忆上下文" in labels

    def test_contains_proactive(self) -> None:
        """build_product_status_view includes 主动陪伴 item."""
        config = get_config()
        view = build_product_status_view(config=config, avatar_action=AvatarAction.IDLE)
        labels = [item.label for item in view.items]
        assert "主动陪伴" in labels

    def test_contains_avatar_action_state(self) -> None:
        """build_product_status_view includes 当前角色状态 with avatar_action value."""
        config = get_config()
        view = build_product_status_view(config=config, avatar_action=AvatarAction.LISTENING)
        avatar_item = next(item for item in view.items if item.label == "当前角色状态")
        assert avatar_item.detail == "listening"


class TestViewModelProductStatus:
    """Tests for ViewModel product status state (V11-A)."""

    def test_initial_product_status_visible_is_false(self) -> None:
        """ViewModel initial product_status_visible is False."""
        vm = DesktopViewModel()
        assert vm.product_status_visible is False

    def test_toggle_product_status_visible(self) -> None:
        """toggle_product_status_visible toggles the visibility flag."""
        vm = DesktopViewModel()
        assert vm.product_status_visible is False
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is False

    def test_set_product_status_view_updates_text(self) -> None:
        """set_product_status_view updates product_status_text."""
        vm = DesktopViewModel()
        view = ProductStatusView(
            items=(
                ProductStatusItem("对话", True, "已启用"),
                ProductStatusItem("记忆上下文", False),
            )
        )
        vm.set_product_status_view(view)
        assert "✅ 对话：已启用" in vm.product_status_text
        assert "❌ 记忆上下文" in vm.product_status_text

    def test_product_status_does_not_change_app_state(self) -> None:
        """Product status operations do not change AppState."""
        vm = DesktopViewModel()
        assert vm.state == AppState.IDLE
        vm.toggle_product_status_visible()
        assert vm.state == AppState.IDLE
        view = ProductStatusView(items=())
        vm.set_product_status_view(view)
        assert vm.state == AppState.IDLE

    def test_product_status_does_not_clear_chat_messages(self) -> None:
        """Product status operations do not clear chat_messages."""
        vm = DesktopViewModel()
        from app.ui.chat_message import ChatMessage

        vm.chat_messages.append(ChatMessage(role="user", text="Hello"))
        assert len(vm.chat_messages) == 1
        vm.toggle_product_status_visible()
        assert len(vm.chat_messages) == 1
        view = ProductStatusView(items=())
        vm.set_product_status_view(view)
        assert len(vm.chat_messages) == 1
