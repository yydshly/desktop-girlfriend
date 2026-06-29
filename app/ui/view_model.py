"""UI view model."""

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.ui.chat_message import ChatMessage

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

    @property
    def effective_display_text(self) -> str:
        """Return the display text, using voice_status_text if set."""
        if self.voice_status_text:
            return self.voice_status_text
        return self.display_text
