"""UI view model."""

from app.contracts.states import AppState


class DesktopViewModel:
    """View model for desktop UI data binding."""

    def __init__(self) -> None:
        self.state: AppState = AppState.IDLE
        self.display_text: str = "Desktop Girlfriend - V1 Scaffold"
