"""UI view model."""

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
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
from app.ui.chat_message import ChatMessage
from app.ui.memory_record_view import MemoryRecordView
from app.ui.memory_suggestion import MemorySuggestionView

# Mapping from AppState to display text
_STATE_DISPLAY_TEXT: dict[AppState, str] = {
    AppState.IDLE: "当前状态：待机",
    AppState.LISTENING: "当前状态：聆听中",
    AppState.THINKING: "当前状态：正在想你说的话",
    AppState.SPEAKING: "当前状态：正在回应你",
    AppState.ERROR: "当前状态：出了一点小问题",
}

_DEFAULT_ASSISTANT_TEXT = ""

# Companion profile
COMPANION_NAME = "小云"
COMPANION_SUBTITLE = "你的桌面 AI 伙伴"
COMPANION_AVATAR_TEXT = "☁️"


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

    def toggle_memory_panel(self) -> None:
        """Toggle the memory panel visibility."""
        self.memory_panel_visible = not self.memory_panel_visible

    @property
    def effective_display_text(self) -> str:
        """Return the display text, using voice_status_text if set."""
        if self.voice_status_text:
            return self.voice_status_text
        return self.display_text
