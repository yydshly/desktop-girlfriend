"""Desktop window implementation."""

from collections.abc import Callable

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.contracts.states import AppState
from app.core.config import get_config
from app.ui.chat_message import ChatMessage
from app.ui.view_model import DesktopViewModel


def should_submit_user_text(text: str) -> bool:
    """Return True if the text input is non-blank and should be submitted."""
    return bool(text.strip())


def render_chat_messages(messages: list[ChatMessage]) -> str:
    """Render a list of chat messages into display text.

    Args:
        messages: List of ChatMessage objects.

    Returns:
        Plain text suitable for QTextEdit.setPlainText().
    """
    if not messages:
        return "还没有对话，和小云说句话吧。"

    lines: list[str] = []
    for msg in messages:
        if msg.role == "user":
            lines.append("你：")
            lines.append(msg.text)
        else:
            lines.append("小云：")
            lines.append(msg.text)
        lines.append("")  # blank line between messages

    # Remove trailing blank line
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


class DesktopWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        view_model: DesktopViewModel,
        on_user_text_submitted: Callable[[str], None],
        on_conversation_cleared: Callable[[], None],
        on_tts_stop_requested: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._view_model = view_model
        self._on_user_text_submitted = on_user_text_submitted
        self._on_conversation_cleared = on_conversation_cleared
        self._on_tts_stop_requested = on_tts_stop_requested

        config = get_config()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(config.window_width, config.window_height)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Companion header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        self._avatar_label = QLabel(self._view_model.companion_avatar_text)
        self._avatar_label.setStyleSheet(
            "font-size: 28px; min-width: 48px; max-width: 48px; "
            "min-height: 48px; max-height: 48px; "
            "background-color: #eef3ff; qproperty-alignment: AlignCenter;"
        )
        header_layout.addWidget(self._avatar_label)

        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self._name_label = QLabel(self._view_model.companion_name)
        self._name_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        info_layout.addWidget(self._name_label)

        self._subtitle_label = QLabel(self._view_model.companion_subtitle)
        self._subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(self._subtitle_label)

        self._state_label = QLabel(self._view_model.display_text)
        self._state_label.setStyleSheet("font-size: 13px; color: #444;")
        info_layout.addWidget(self._state_label)

        header_layout.addWidget(info_widget, stretch=1)
        layout.addWidget(header_widget)

        # Chat history display
        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        self._chat_history.setPlainText(render_chat_messages(self._view_model.chat_messages))
        layout.addWidget(self._chat_history, stretch=1)

        # Error display
        self._error_label = QLabel(self._view_model.error_text)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #b00020; padding: 8px;")
        self._error_label.setVisible(bool(self._view_model.error_text))
        layout.addWidget(self._error_label)

        # Input field
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入文字后点击发送...")
        layout.addWidget(self._input_field)

        # Button row
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self._new_conversation_button = QPushButton("新对话")
        self._new_conversation_button.clicked.connect(self._on_new_conversation_clicked)
        button_layout.addWidget(self._new_conversation_button)

        self._stop_speaking_button = QPushButton("停止说话")
        self._stop_speaking_button.clicked.connect(self._on_tts_stop_clicked)
        self._stop_speaking_button.setEnabled(False)
        button_layout.addWidget(self._stop_speaking_button)

        self._send_button = QPushButton("发送")
        self._send_button.clicked.connect(self._on_send_clicked)
        button_layout.addWidget(self._send_button)

        layout.addWidget(button_row)

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        text = self._input_field.text()
        if not should_submit_user_text(text):
            return
        self._on_user_text_submitted(text)
        self._input_field.clear()

    def _on_new_conversation_clicked(self) -> None:
        """Handle new conversation button click."""
        self._on_conversation_cleared()

    def _on_tts_stop_clicked(self) -> None:
        """Handle stop speaking button click."""
        if self._on_tts_stop_requested:
            self._on_tts_stop_requested()

    def update_from_view_model(self) -> None:
        """Update UI from view model state."""
        self._name_label.setText(self._view_model.companion_name)
        self._subtitle_label.setText(self._view_model.companion_subtitle)
        self._avatar_label.setText(self._view_model.companion_avatar_text)
        self._state_label.setText(self._view_model.display_text)
        self._chat_history.setPlainText(
            render_chat_messages(self._view_model.chat_messages)
        )
        self._chat_history.moveCursor(QTextCursor.MoveOperation.End)
        self._error_label.setText(self._view_model.error_text)
        self._error_label.setVisible(bool(self._view_model.error_text))
        is_thinking = self._view_model.state == AppState.THINKING
        is_speaking = self._view_model.state == AppState.SPEAKING
        busy = is_thinking or is_speaking
        self._send_button.setEnabled(not busy)
        self._input_field.setEnabled(not busy)
        self._new_conversation_button.setEnabled(not busy)
        self._stop_speaking_button.setEnabled(is_speaking)
