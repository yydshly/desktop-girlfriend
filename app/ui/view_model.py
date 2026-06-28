"""UI view model."""

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.ui.chat_message import ChatMessage

# Mapping from AppState to display text
_STATE_DISPLAY_TEXT: dict[AppState, str] = {
    AppState.IDLE: "状态：待机",
    AppState.LISTENING: "状态：聆听中",
    AppState.THINKING: "状态：思考中",
    AppState.SPEAKING: "状态：说话中",
    AppState.ERROR: "状态：错误",
}

_DEFAULT_ASSISTANT_TEXT = ""


class DesktopViewModel:
    """View model for desktop UI data binding."""

    def __init__(self) -> None:
        self.state: AppState = AppState.IDLE
        self.display_text: str = _STATE_DISPLAY_TEXT[AppState.IDLE]
        self.assistant_text: str = _DEFAULT_ASSISTANT_TEXT
        self.error_text: str = ""
        self.chat_messages: list[ChatMessage] = []

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
