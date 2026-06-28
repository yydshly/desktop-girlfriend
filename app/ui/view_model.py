"""UI view model."""

from app.contracts.events import STATE_CHANGED, BaseEvent
from app.contracts.states import AppState

# Mapping from AppState to display text
_STATE_DISPLAY_TEXT: dict[AppState, str] = {
    AppState.IDLE: "状态：待机",
    AppState.LISTENING: "状态：聆听中",
    AppState.THINKING: "状态：思考中",
    AppState.SPEAKING: "状态：说话中",
    AppState.ERROR: "状态：错误",
}


class DesktopViewModel:
    """View model for desktop UI data binding."""

    def __init__(self) -> None:
        self.state: AppState = AppState.IDLE
        self.display_text: str = _STATE_DISPLAY_TEXT[AppState.IDLE]

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
