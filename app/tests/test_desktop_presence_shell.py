"""Tests for desktop presence shell (Phase 2-D)."""

# ruff: noqa: E402, I001

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PySide6.QtWidgets import QApplication

    HAS_PYSIDE6 = True
except ModuleNotFoundError:
    QApplication = object
    HAS_PYSIDE6 = False

HAS_PY311_ENUM = hasattr(__import__("enum"), "StrEnum")

from app.ui.desktop_presence import (
    COMPACT_MODE_HEIGHT,
    COMPACT_MODE_WIDTH,
    DesktopPresenceState,
    LIVE2D_DESKTOP_HEIGHT,
    LIVE2D_DESKTOP_WIDTH,
    LIVE2D_DESKTOP_QUERY,
    LIVE2D_PROTOTYPE_ROUTE,
    Live2DDesktopShellSpec,
    build_live2d_desktop_shell_spec,
    render_compact_button_text,
    render_live2d_shell_summary,
    render_pin_button_text,
)
if HAS_PY311_ENUM:
    from app.ui.product_status import ProductStatusItem, ProductStatusView
    from app.ui.view_model import DesktopViewModel
else:
    ProductStatusItem = object
    ProductStatusView = object
    DesktopViewModel = object

if HAS_PYSIDE6 and HAS_PY311_ENUM:
    from app.ui.window import DesktopWindow
else:
    DesktopWindow = object


class TestDesktopPresenceState:
    """Tests for DesktopPresenceState."""

    def test_default_always_on_top_false(self) -> None:
        """Default always_on_top is False."""
        state = DesktopPresenceState()
        assert state.always_on_top is False

    def test_default_compact_mode_false(self) -> None:
        """Default compact_mode is False."""
        state = DesktopPresenceState()
        assert state.compact_mode is False


class TestPresenceButtonText:
    """Tests for render_pin_button_text and render_compact_button_text."""

    def test_pin_button_not_on_top(self) -> None:
        """render_pin_button_text(False) returns '置顶'."""
        assert render_pin_button_text(False) == "置顶"

    def test_pin_button_on_top(self) -> None:
        """render_pin_button_text(True) returns '取消置顶'."""
        assert render_pin_button_text(True) == "取消置顶"

    def test_compact_button_normal(self) -> None:
        """render_compact_button_text(False) returns '小窗'."""
        assert render_compact_button_text(False) == "小窗"

    def test_compact_button_compact(self) -> None:
        """render_compact_button_text(True) returns '展开'."""
        assert render_compact_button_text(True) == "展开"


class TestCompactModeDimensions:
    """Tests for compact mode dimensions."""

    def test_compact_width(self) -> None:
        """COMPACT_MODE_WIDTH is 340."""
        assert COMPACT_MODE_WIDTH == 340

    def test_compact_height(self) -> None:
        """COMPACT_MODE_HEIGHT is 320."""
        assert COMPACT_MODE_HEIGHT == 320


class TestLive2DDesktopShellSpec:
    """Tests for the Live2D desktop shell contract."""

    def test_default_shell_spec_matches_desktop_overlay_target(self) -> None:
        """Default spec uses a transparent interactive desktop overlay."""
        spec = Live2DDesktopShellSpec(source_url="file:///tmp/live2d/index.html")

        assert spec.width == LIVE2D_DESKTOP_WIDTH
        assert spec.height == LIVE2D_DESKTOP_HEIGHT
        assert spec.transparent_background is True
        assert spec.frameless is True
        assert spec.always_on_top is True
        assert spec.click_through is False
        assert spec.devtools_enabled is False

    def test_build_shell_spec_points_to_live2d_prototype(self, tmp_path) -> None:
        """Shell spec source URL points at the local Live2D runtime page."""
        target = tmp_path / LIVE2D_PROTOTYPE_ROUTE
        target.parent.mkdir(parents=True)
        target.write_text("<!doctype html>", encoding="utf-8")

        spec = build_live2d_desktop_shell_spec(tmp_path)

        assert spec.source_url == f"{target.resolve().as_uri()}?{LIVE2D_DESKTOP_QUERY}"
        assert spec.source_url.endswith(
            f"/showcase-demo/live2d-prototype/index.html?{LIVE2D_DESKTOP_QUERY}"
        )

    def test_build_shell_spec_can_enable_desktop_debug_options(self, tmp_path) -> None:
        """Debug options are explicit so production desktop mode stays clean."""
        target = tmp_path / LIVE2D_PROTOTYPE_ROUTE
        target.parent.mkdir(parents=True)
        target.write_text("<!doctype html>", encoding="utf-8")

        spec = build_live2d_desktop_shell_spec(
            tmp_path,
            devtools_enabled=True,
            click_through=True,
        )

        assert spec.devtools_enabled is True
        assert spec.click_through is True

    def test_build_shell_spec_applies_scale_and_opacity(self, tmp_path) -> None:
        """Shell spec can size and fade the desktop companion window."""
        target = tmp_path / LIVE2D_PROTOTYPE_ROUTE
        target.parent.mkdir(parents=True)
        target.write_text("<!doctype html>", encoding="utf-8")

        spec = build_live2d_desktop_shell_spec(tmp_path, scale=0.8, opacity=0.7)

        assert spec.width == round(LIVE2D_DESKTOP_WIDTH * 0.8)
        assert spec.height == round(LIVE2D_DESKTOP_HEIGHT * 0.8)
        assert spec.opacity == 0.7

    def test_build_shell_spec_includes_selected_model_id(self, tmp_path) -> None:
        """Shell spec passes the selected model id to the Live2D runtime page."""
        target = tmp_path / LIVE2D_PROTOTYPE_ROUTE
        target.parent.mkdir(parents=True)
        target.write_text("<!doctype html>", encoding="utf-8")

        spec = build_live2d_desktop_shell_spec(
            tmp_path,
            model_id="custom/Xiaoyun",
        )

        assert spec.source_url.endswith(
            "/showcase-demo/live2d-prototype/index.html?desktop=1&model=custom%2FXiaoyun"
        )

    def test_shell_summary_describes_window_capabilities(self) -> None:
        """Summary makes the active desktop shell behavior visible."""
        spec = Live2DDesktopShellSpec(source_url="file:///tmp/live2d/index.html")

        assert render_live2d_shell_summary(spec) == (
            "Live2D desktop shell 520x760: "
            "transparent, frameless, top, interactive"
        )


class TestViewModelPresenceMethods:
    """Tests for ViewModel presence toggle methods."""

    pytestmark = pytest.mark.skipif(
        not HAS_PY311_ENUM,
        reason="DesktopViewModel requires Python 3.11 StrEnum support",
    )

    def test_toggle_always_on_top(self) -> None:
        """toggle_always_on_top flips always_on_top."""
        vm = DesktopViewModel()
        assert vm.always_on_top is False
        vm.toggle_always_on_top()
        assert vm.always_on_top is True
        vm.toggle_always_on_top()
        assert vm.always_on_top is False

    def test_toggle_compact_mode(self) -> None:
        """toggle_compact_mode flips compact_mode."""
        vm = DesktopViewModel()
        assert vm.compact_mode is False
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is False

    def test_enter_compact_mode_closes_status_panel(self) -> None:
        """Entering compact mode closes status panel if open."""
        vm = DesktopViewModel()
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        assert vm.product_status_visible is False

    def test_live2d_model_options_track_selected_model(self) -> None:
        """ViewModel stores selectable Live2D models and active model id."""
        vm = DesktopViewModel()

        vm.set_live2d_model_options(
            (
                ("sample/Hiyori", "Hiyori"),
                ("custom/Xiaoyun", "Xiaoyun"),
            ),
            selected_model_id="custom/Xiaoyun",
        )

        assert vm.live2d_model_options == (
            ("sample/Hiyori", "Hiyori"),
            ("custom/Xiaoyun", "Xiaoyun"),
        )
        assert vm.selected_live2d_model_id == "custom/Xiaoyun"
        assert vm.select_live2d_model("sample/Hiyori") is True
        assert vm.selected_live2d_model_id == "sample/Hiyori"
        assert vm.select_live2d_model("missing/model") is False
        assert vm.selected_live2d_model_id == "sample/Hiyori"


class TestWindowPresenceShell:
    """Tests for DesktopWindow presence shell features."""

    pytestmark = pytest.mark.skipif(
        not (HAS_PYSIDE6 and HAS_PY311_ENUM),
        reason="DesktopWindow tests require PySide6 and Python 3.11 StrEnum support",
    )

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
    def test_pin_button_present(qapp: QApplication) -> None:
        """Pin button exists."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_pin_button")
        assert window._pin_button.text() == "置顶"

    @staticmethod
    def test_compact_button_present(qapp: QApplication) -> None:
        """Compact button exists."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_compact_button")
        assert window._compact_button.text() == "小窗"

    @staticmethod
    def test_header_info_surface_is_registered_for_window_dragging(
        qapp: QApplication,
    ) -> None:
        """Header identity/status surfaces act as drag handles, but buttons do not."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        drag_handles = set(window._drag_handle_widgets)
        assert window._avatar_label in drag_handles
        assert window._name_label in drag_handles
        assert window._companion_status_label in drag_handles
        assert window._proactive_status_label in drag_handles
        assert window._product_status_button not in drag_handles
        assert window._pin_button not in drag_handles
        assert window._compact_button not in drag_handles

    @staticmethod
    def test_live2d_companion_control_buttons_trigger_callbacks(
        qapp: QApplication,
    ) -> None:
        """Desktop companion controls are visible and trigger app callbacks."""
        calls = []
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_live2d_scale_up_requested=lambda: calls.append("scale_up"),
            on_live2d_scale_down_requested=lambda: calls.append("scale_down"),
            on_live2d_opacity_down_requested=lambda: calls.append("opacity_down"),
            on_live2d_opacity_up_requested=lambda: calls.append("opacity_up"),
            on_live2d_visibility_toggled=lambda: calls.append("visibility"),
            on_live2d_position_reset_requested=lambda: calls.append("reset"),
        )
        window.show()

        window._live2d_scale_up_button.click()
        window._live2d_scale_down_button.click()
        window._live2d_opacity_down_button.click()
        window._live2d_opacity_up_button.click()
        window._live2d_toggle_button.click()
        window._live2d_reset_button.click()

        assert calls == [
            "scale_up",
            "scale_down",
            "opacity_down",
            "opacity_up",
            "visibility",
            "reset",
        ]

    @staticmethod
    def test_live2d_model_status_label_reflects_view_model(qapp: QApplication) -> None:
        """Desktop window surfaces the active Live2D model package status."""
        vm = DesktopViewModel()
        vm.set_live2d_model_catalog_summary(
            "Model: Hiyori · ready · motions 10 · textures 2"
        )
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._live2d_model_status_label.text() == (
            "Model: Hiyori · ready · motions 10 · textures 2"
        )

    @staticmethod
    def test_live2d_model_selector_lists_models_and_emits_selection(
        qapp: QApplication,
    ) -> None:
        """Desktop window exposes discovered Live2D model packages for selection."""
        calls: list[str] = []
        vm = DesktopViewModel()
        vm.set_live2d_model_options(
            (
                ("sample/Hiyori", "Hiyori"),
                ("custom/Xiaoyun", "Xiaoyun"),
            ),
            selected_model_id="sample/Hiyori",
        )
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_live2d_model_selected=lambda model_id: calls.append(model_id),
        )
        window.show()

        assert window._live2d_model_selector.count() == 2
        assert window._live2d_model_selector.itemText(0) == "Hiyori"
        assert window._live2d_model_selector.itemData(1) == "custom/Xiaoyun"
        assert window._live2d_model_selector.currentData() == "sample/Hiyori"

        window._live2d_model_selector.setCurrentIndex(1)
        qapp.processEvents()

        assert calls == ["custom/Xiaoyun"]
        assert vm.selected_live2d_model_id == "custom/Xiaoyun"

    @staticmethod
    def test_status_button_first_click_opens_panel(qapp: QApplication) -> None:
        """First click on status button opens the panel."""
        vm = DesktopViewModel()

        def on_status_requested() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(
                    items=(ProductStatusItem("对话", True, "已启用"),)
                )
            )
            window.update_from_view_model()

        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        assert not vm.product_status_visible

        window._product_status_button.pressed.emit()
        qapp.processEvents()

        assert vm.product_status_visible is True
        assert window._product_status_panel.isVisible() is True

    @staticmethod
    def test_status_button_second_click_closes_panel(qapp: QApplication) -> None:
        """Second click on status button closes the panel."""
        vm = DesktopViewModel()

        def on_status_requested() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(
                    items=(ProductStatusItem("对话", True, "已启用"),)
                )
            )
            window.update_from_view_model()

        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is False

    @staticmethod
    def test_compact_mode_preserves_chat_history(qapp: QApplication) -> None:
        """Compact mode does not clear chat messages."""
        vm = DesktopViewModel()
        vm.chat_messages.append(
            __import__("app.ui.chat_message", fromlist=["ChatMessage"]).ChatMessage(
                role="user", text="Hello"
            )
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert len(vm.chat_messages) == 1

        window._handle_compact_clicked()
        qapp.processEvents()

        assert vm.compact_mode is True
        assert len(vm.chat_messages) == 1  # preserved

    @staticmethod
    def test_pin_button_toggles_label(qapp: QApplication) -> None:
        """Pin button label toggles between 置顶 and 取消置顶."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._pin_button.text() == "置顶"
        assert vm.always_on_top is False

        window._pin_button.pressed.emit()
        qapp.processEvents()

        assert vm.always_on_top is True
        # Note: actual window flag is set but offscreen Qt may not reflect it
        window.update_from_view_model()
        assert window._pin_button.text() == "取消置顶"

    @staticmethod
    def test_compact_button_toggles_label(qapp: QApplication) -> None:
        """Compact button label toggles between 小窗 and 展开."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._compact_button.text() == "小窗"
        assert vm.compact_mode is False

        window._compact_button.pressed.emit()
        qapp.processEvents()

        assert vm.compact_mode is True
        window.update_from_view_model()
        assert window._compact_button.text() == "展开"
