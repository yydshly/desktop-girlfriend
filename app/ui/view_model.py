"""UI view model."""

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
    MEMORY_ADDED,
    MEMORY_CONFIRMED,
    MEMORY_DELETED,
    MEMORY_ERROR,
    MEMORY_LISTED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.core.version import get_app_version
from app.ui.avatar_action import (
    AvatarAction,
    avatar_label_for_action,
    avatar_style_for_action,
    avatar_text_for_action,
)
from app.ui.chat_message import ChatMessage
from app.ui.companion_presence import render_companion_status_text
from app.ui.memory_record_view import MemoryRecordView
from app.ui.memory_suggestion import MemorySuggestionView
from app.ui.product_status import ProductStatusView, render_status_view

# Mapping from AppState to display text
_STATE_DISPLAY_TEXT: dict[AppState, str] = {
    AppState.IDLE: "当前状态：待机",
    AppState.LISTENING: "当前状态：聆听中",
    AppState.THINKING: "当前状态：正在想你说的话",
    AppState.SPEAKING: "当前状态：正在回应你",
    AppState.ERROR: "当前状态：出了一点小问题",
}

_DEFAULT_ASSISTANT_TEXT = ""

# Companion profile — version reads from VERSION file
_companion_version_info = get_app_version()
COMPANION_NAME = "小云"
COMPANION_SUBTITLE = "你的桌面 AI 伙伴"
COMPANION_AVATAR_TEXT = "☁️"
COMPANION_VERSION = _companion_version_info.version
COMPANION_RELEASE_STAGE = _companion_version_info.release_stage


class DesktopViewModel:
    """View model for desktop UI data binding."""

    def __init__(self) -> None:
        self.state: AppState = AppState.IDLE
        self.display_text: str = _STATE_DISPLAY_TEXT[AppState.IDLE]
        self.assistant_text: str = _DEFAULT_ASSISTANT_TEXT
        self.error_text: str = ""
        self.chat_messages: list[ChatMessage] = []
        self.companion_name: str = COMPANION_NAME
        self.companion_subtitle: str = COMPANION_SUBTITLE
        self.companion_avatar_text: str = COMPANION_AVATAR_TEXT
        self.voice_status_text: str = ""
        self.memory_suggestion: MemorySuggestionView | None = None
        self.memory_status_text: str = ""
        self.memory_records: list[MemoryRecordView] = []
        self.memory_panel_visible: bool = False
        # Avatar action state (V10-A)
        self.avatar_action: AvatarAction = AvatarAction.IDLE
        self.avatar_action_label: str = avatar_label_for_action(AvatarAction.IDLE)
        # Companion presence fields (Phase 2-A)
        self.companion_status_text: str = render_companion_status_text(AvatarAction.IDLE)
        self.companion_version_text: str = COMPANION_VERSION
        self.companion_release_stage_text: str = COMPANION_RELEASE_STAGE
        # Product status state (V11-A)
        self.product_status_visible: bool = False
        self.product_status_view: ProductStatusView = ProductStatusView(items=())
        self.product_status_text: str = ""
        # Startup diagnostics state (V11-C)
        self.startup_diagnostics_text: str = ""
        # Desktop presence state (Phase 2-D)
        self.always_on_top: bool = False
        self.compact_mode: bool = False
        self.live2d_model_catalog_summary: str = (
            "Model: scanning local Live2D packages"
        )
        self.live2d_model_catalog_details: str = ""
        self.live2d_model_options: tuple[tuple[str, str], ...] = ()
        self.selected_live2d_model_id: str = ""
        # Settings panel state (Phase 2-E)
        self.settings_visible: bool = False
        self.settings_text: str = ""
        # System tray state (Phase 2-F)
        self.tray_available: bool = False
        self.hidden_to_tray: bool = False
        # Phase 3-A: Force quit state (for tray "退出" menu)
        self.force_quit_requested: bool = False
        # Phase 3-B: Onboarding state (session-level, not persisted)
        self.onboarding_visible: bool = True
        self.onboarding_text: str = ""
        # Phase 3-D: Proactive status hint (e.g., "小云会安静一会儿。")
        self.proactive_status_text: str = ""
        # Memory panel UX: track if panel has ever been closed (for status clearing)
        self._memory_panel_ever_closed: bool = False

    def handle_state_changed(self, event: BaseEvent) -> None:
        """Handle state.changed event and update display text.

        Args:
            event: The state.changed event.
        """
        if event.event_type != STATE_CHANGED:
            return

        current_state_value = event.payload.get("current_state")

        if type(current_state_value) is not str:
            self.state = AppState.ERROR
        else:
            try:
                self.state = AppState(current_state_value)
            except ValueError:
                self.state = AppState.ERROR

        self.voice_status_text = ""
        self.display_text = _STATE_DISPLAY_TEXT.get(self.state, "状态：未知")

        if self.state == AppState.THINKING:
            self.error_text = ""

        # Update avatar action based on new state (V10-A)
        if self.state == AppState.IDLE:
            self.avatar_action = AvatarAction.IDLE
        elif self.state == AppState.LISTENING:
            self.avatar_action = AvatarAction.LISTENING
        elif self.state == AppState.THINKING:
            self.avatar_action = AvatarAction.THINKING
        elif self.state == AppState.SPEAKING:
            self.avatar_action = AvatarAction.SPEAKING
        elif self.state == AppState.ERROR:
            self.avatar_action = AvatarAction.ERROR
        else:
            self.avatar_action = AvatarAction.IDLE
        self.avatar_action_label = avatar_label_for_action(self.avatar_action)
        self.companion_status_text = render_companion_status_text(self.avatar_action)

    def handle_assistant_text_received(self, event: BaseEvent) -> None:
        """Handle assistant.text_received event and update assistant text.

        Args:
            event: The assistant.text_received event.
        """
        if event.event_type != ASSISTANT_TEXT_RECEIVED:
            return

        text = event.payload.get("text")
        if type(text) is str:
            self.assistant_text = text
            if text.strip():
                self.chat_messages.append(ChatMessage(role="assistant", text=text))

    def handle_user_text_submitted(self, event: BaseEvent) -> None:
        """Handle user.text_submitted event and append user message.

        Args:
            event: The user.text_submitted event.
        """
        if event.event_type != USER_TEXT_SUBMITTED:
            return

        text = event.payload.get("text")
        if type(text) is str and text.strip():
            self.chat_messages.append(ChatMessage(role="user", text=text.strip()))
            # Phase 3-D: detect proactive suppress phrases and set hint
            self._maybe_set_proactive_suppress_hint(text)

    # Phase 3-D: suppress phrases for proactive control UX
    _PROACTIVE_SUPPRESS_PHRASES: tuple[str, ...] = (
        "别打扰",
        "不要主动",
        "别主动",
        "安静一会",
        "安静一下",
        "先别说",
        "别说话",
        "不用提醒",
        "先不用",
    )

    def _maybe_set_proactive_suppress_hint(self, text: str) -> None:
        """Check text for suppress phrases and set proactive status hint.

        Args:
            text: The user's message text.
        """
        for phrase in self._PROACTIVE_SUPPRESS_PHRASES:
            if phrase in text:
                self.proactive_status_text = "小云会安静一会儿。"
                return

    def handle_system_error(self, event: BaseEvent) -> None:
        """Handle system.error event and update error text.

        Args:
            event: The system.error event.
        """
        if event.event_type != SYSTEM_ERROR:
            return

        message = event.payload.get("message")
        if type(message) is str and message.strip():
            self.error_text = message.strip()
        else:
            self.error_text = "发生未知错误。"

        self.avatar_action = AvatarAction.ERROR
        self.avatar_action_label = avatar_label_for_action(AvatarAction.ERROR)
        self.companion_status_text = render_companion_status_text(AvatarAction.ERROR)

    def handle_conversation_cleared(self, event: BaseEvent) -> None:
        """Handle conversation.cleared event and reset UI state.

        Args:
            event: The conversation.cleared event.
        """
        if event.event_type != CONVERSATION_CLEARED:
            return

        self.chat_messages.clear()
        self.assistant_text = ""
        self.error_text = ""
        self.voice_status_text = ""
        self.memory_suggestion = None
        self.memory_status_text = ""
        self.memory_panel_visible = False
        self.state = AppState.IDLE
        self.display_text = _STATE_DISPLAY_TEXT[AppState.IDLE]
        self.avatar_action = AvatarAction.IDLE
        self.avatar_action_label = avatar_label_for_action(AvatarAction.IDLE)
        self.companion_status_text = render_companion_status_text(AvatarAction.IDLE)

    def handle_voice_progress_event(self, event: BaseEvent) -> None:
        """Handle voice progress events and update fine-grained status text.

        Args:
            event: A voice progress event (recording/recognition started/finished).
        """
        event_type = event.event_type
        if event_type == VOICE_RECORDING_STARTED:
            self.voice_status_text = "当前状态：正在录音，请说话"
        elif event_type == VOICE_RECORDING_FINISHED:
            self.voice_status_text = "当前状态：正在整理语音"
        elif event_type == ASR_RECOGNITION_STARTED:
            self.voice_status_text = "当前状态：正在识别语音"
        elif event_type == ASR_TEXT_RECOGNIZED:
            self.voice_status_text = "当前状态：正在想你说的话"

    def handle_memory_suggestions_detected(self, event: BaseEvent) -> None:
        """Handle memory.suggestions_detected event and store first suggestion.

        Args:
            event: The memory.suggestions_detected event.
        """
        if event.event_type != MEMORY_SUGGESTIONS_DETECTED:
            return

        suggestions = event.payload.get("suggestions")
        if not isinstance(suggestions, list) or len(suggestions) == 0:
            self.memory_suggestion = None
            self.memory_status_text = ""
            return

        first = suggestions[0]
        if not isinstance(first, dict):
            return

        pending_id = first.get("pending_id")
        kind = first.get("kind")
        importance = first.get("importance")
        text = first.get("text")

        if (
            not isinstance(pending_id, str)
            or not isinstance(kind, str)
            or not isinstance(importance, str)
            or not isinstance(text, str)
        ):
            return

        self.memory_suggestion = MemorySuggestionView(
            pending_id=pending_id,
            kind=kind,
            importance=importance,
            text=text,
        )
        self.memory_status_text = "小云发现一条可能值得记住的信息"

    def handle_memory_confirmed(self, event: BaseEvent) -> None:
        """Handle memory.confirmed event and clear suggestion.

        Args:
            event: The memory.confirmed event.
        """
        if event.event_type != MEMORY_CONFIRMED:
            return

        self.memory_suggestion = None
        self.memory_status_text = "已记住"

    def handle_memory_added(self, event: BaseEvent) -> None:
        """Handle memory.added event and update memory status text."""
        if event.event_type != MEMORY_ADDED:
            return
        self.memory_status_text = "已添加记忆"

    def handle_memory_rejected(self, event: BaseEvent) -> None:
        """Handle memory.rejected event and clear suggestion.

        Args:
            event: The memory.rejected event.
        """
        if event.event_type != MEMORY_REJECTED:
            return

        self.memory_suggestion = None
        self.memory_status_text = "已忽略"

    def handle_memory_error(self, event: BaseEvent) -> None:
        """Handle memory.error event and set status text.

        Args:
            event: The memory.error event.
        """
        if event.event_type != MEMORY_ERROR:
            return

        message = event.payload.get("message")
        if isinstance(message, str) and message.strip():
            self.memory_status_text = message.strip()
        else:
            self.memory_status_text = "记忆处理失败"

    def handle_memory_listed(self, event: BaseEvent) -> None:
        """Handle memory.listed event and store memory records.

        Args:
            event: The memory.listed event.
        """
        if event.event_type != MEMORY_LISTED:
            return

        records = event.payload.get("records")
        if not isinstance(records, list):
            self.memory_records = []
            self.memory_panel_visible = True
            if self.memory_status_text != "已添加记忆":
                self.memory_status_text = "已加载记忆"
            return

        self.memory_records = []
        for r in records:
            if not isinstance(r, dict):
                continue
            record_id = r.get("record_id")
            kind = r.get("kind")
            importance = r.get("importance")
            text = r.get("text")
            created_at = r.get("created_at")
            updated_at = r.get("updated_at")

            if (
                isinstance(record_id, str)
                and isinstance(kind, str)
                and isinstance(importance, str)
                and isinstance(text, str)
                and isinstance(created_at, str)
                and isinstance(updated_at, str)
            ):
                self.memory_records.append(
                    MemoryRecordView(
                        record_id=record_id,
                        kind=kind,
                        importance=importance,
                        text=text,
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )

        self.memory_panel_visible = True
        if self.memory_status_text != "已添加记忆":
            self.memory_status_text = "已加载记忆"

    def handle_memory_deleted(self, event: BaseEvent) -> None:
        """Handle memory.deleted event and remove the deleted record.

        Args:
            event: The memory.deleted event.
        """
        if event.event_type != MEMORY_DELETED:
            return

        record_id = event.payload.get("record_id")
        if isinstance(record_id, str):
            self.memory_records = [
                r for r in self.memory_records if r.record_id != record_id
            ]
        self.memory_status_text = "已删除记忆"

    def handle_proactive_nudge_ready(self, event: BaseEvent) -> None:
        """Handle proactive.nudge_ready event and append as assistant message.

        Args:
            event: The proactive.nudge_ready event.
        """
        if event.event_type != PROACTIVE_NUDGE_READY:
            return

        text = event.payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return

        self.chat_messages.append(ChatMessage(role="assistant", text=text))

        self.avatar_action = AvatarAction.PROACTIVE
        self.avatar_action_label = avatar_label_for_action(AvatarAction.PROACTIVE)
        self.companion_status_text = render_companion_status_text(AvatarAction.PROACTIVE)

    def handle_proactive_avatar_hint(self, event: BaseEvent) -> None:
        """Handle proactive visual hint without appending chat message.

        Used when proactive_tts_enabled=True to update avatar to PROACTIVE
        without duplicating the chat message (TTS pipeline appends via
        ASSISTANT_TEXT_RECEIVED subscription).

        Args:
            event: The proactive.nudge_ready event.
        """
        if event.event_type != PROACTIVE_NUDGE_READY:
            return

        self.avatar_action = AvatarAction.PROACTIVE
        self.avatar_action_label = avatar_label_for_action(AvatarAction.PROACTIVE)
        self.companion_status_text = render_companion_status_text(AvatarAction.PROACTIVE)

    def toggle_memory_panel(self) -> None:
        """Toggle the memory panel visibility."""
        self.memory_panel_visible = not self.memory_panel_visible
        if self.memory_panel_visible:
            # Only clear stale feedback on re-open (not first open from manual add)
            if self._memory_panel_ever_closed and self.memory_status_text == "已添加记忆":
                self.memory_status_text = ""
            self.product_status_visible = False
            self.settings_visible = False
        else:
            self._memory_panel_ever_closed = True

    def toggle_product_status_visible(self) -> None:
        """Toggle the product status panel visibility."""
        self.product_status_visible = not self.product_status_visible
        # Mutual exclusivity: opening product status closes settings
        if self.product_status_visible:
            self.settings_visible = False

    def toggle_always_on_top(self) -> None:
        """Toggle the always-on-top window flag (Phase 2-D)."""
        self.always_on_top = not self.always_on_top

    def toggle_compact_mode(self) -> None:
        """Toggle compact mode (Phase 2-D)."""
        self.compact_mode = not self.compact_mode
        # When entering compact mode, close panels and onboarding
        if self.compact_mode:
            self.product_status_visible = False
            self.settings_visible = False
            self.onboarding_visible = False

    def toggle_settings_visible(self) -> None:
        """Toggle the settings panel visibility (Phase 2-E)."""
        self.settings_visible = not self.settings_visible
        # Mutual exclusivity: opening settings closes product status
        if self.settings_visible:
            self.product_status_visible = False

    def set_settings_text(self, text: str) -> None:
        """Set the settings panel display text.

        Args:
            text: The rendered settings text.
        """
        self.settings_text = text

    def set_tray_available(self, available: bool) -> None:
        """Set whether the system tray is available.

        Args:
            available: Whether the system tray is available on this platform.
        """
        self.tray_available = available

    def set_hidden_to_tray(self, hidden: bool) -> None:
        """Set whether the window is hidden to tray.

        Args:
            hidden: Whether the window is currently hidden to tray.
        """
        self.hidden_to_tray = hidden

    def request_force_quit(self) -> None:
        """Request forced quit when user selects '退出' from tray menu."""
        self.force_quit_requested = True

    def clear_force_quit_request(self) -> None:
        """Clear the force-quit request flag."""
        self.force_quit_requested = False

    def set_onboarding_text(self, text: str) -> None:
        """Set the onboarding card display text.

        Args:
            text: The rendered onboarding text.
        """
        self.onboarding_text = text

    def set_proactive_status_text(self, text: str) -> None:
        """Set the proactive status hint text (Phase 3-D).

        Args:
            text: The proactive status hint, e.g. "小云会安静一会儿。"
        """
        self.proactive_status_text = text

    def clear_proactive_status_text(self) -> None:
        """Clear the proactive status hint text (Phase 3-D)."""
        self.proactive_status_text = ""

    def dismiss_onboarding(self) -> None:
        """Dismiss the onboarding card (Phase 3-B)."""
        self.onboarding_visible = False

    def open_settings_from_onboarding(self) -> None:
        """Open settings from onboarding card (Phase 3-B).

        Dismisses the onboarding card and opens the settings panel,
        ensuring mutual exclusivity with the product status panel.
        """
        self.onboarding_visible = False
        self.settings_visible = True
        self.product_status_visible = False

    def set_product_status_view(self, view: ProductStatusView) -> None:
        """Set the product status view and update rendered text.

        Args:
            view: The product status view to display.
        """
        self.product_status_view = view
        self.product_status_text = render_status_view(view)

    def set_startup_diagnostics_text(self, text: str) -> None:
        """Set the startup diagnostics detail text.

        Args:
            text: The rendered startup diagnostics details.
        """
        self.startup_diagnostics_text = text

    def set_live2d_model_catalog_summary(self, text: str) -> None:
        """Set the compact Live2D model package status text."""
        self.live2d_model_catalog_summary = text.strip() or (
            "Model: no Live2D model status available"
        )

    def set_live2d_model_catalog_details(self, text: str) -> None:
        """Set detailed Live2D model package diagnostics text."""
        self.live2d_model_catalog_details = text.strip()

    def set_live2d_model_options(
        self,
        options: tuple[tuple[str, str], ...],
        *,
        selected_model_id: str | None = None,
    ) -> None:
        """Set selectable Live2D model options as `(model_id, label)` pairs."""
        self.live2d_model_options = tuple(
            (model_id, label)
            for model_id, label in options
            if model_id.strip() and label.strip()
        )
        valid_ids = {model_id for model_id, _label in self.live2d_model_options}
        if selected_model_id in valid_ids:
            self.selected_live2d_model_id = selected_model_id or ""
            return
        if self.selected_live2d_model_id not in valid_ids:
            self.selected_live2d_model_id = (
                self.live2d_model_options[0][0] if self.live2d_model_options else ""
            )

    def select_live2d_model(self, model_id: str) -> bool:
        """Select a discovered Live2D model by id."""
        valid_ids = {option_id for option_id, _label in self.live2d_model_options}
        if model_id not in valid_ids:
            return False
        self.selected_live2d_model_id = model_id
        return True

    @property
    def effective_avatar_text(self) -> str:
        """Return the avatar emoji text for the current avatar action."""
        return avatar_text_for_action(self.avatar_action)

    @property
    def effective_avatar_label(self) -> str:
        """Return the avatar label text for the current avatar action."""
        return self.avatar_action_label

    @property
    def effective_avatar_style(self) -> str:
        """Return the stylesheet for the current avatar action."""
        return avatar_style_for_action(self.avatar_action)

    @property
    def effective_display_text(self) -> str:
        """Return the display text, using voice_status_text if set."""
        if self.voice_status_text:
            return self.voice_status_text
        return self.display_text
