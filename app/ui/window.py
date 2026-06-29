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
from app.ui.memory_record_view import render_memory_record_text
from app.ui.memory_suggestion import render_memory_suggestion_text
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
        on_voice_input_requested: Callable[[], None] | None = None,
        on_memory_confirm_requested: Callable[[str], None] | None = None,
        on_memory_reject_requested: Callable[[str], None] | None = None,
        on_memory_list_requested: Callable[[], None] | None = None,
        on_memory_delete_requested: Callable[[str], None] | None = None,
        on_product_status_requested: Callable[[], None] | None = None,
        memory_management_enabled: bool = False,
    ) -> None:
        super().__init__()
        self._view_model = view_model
        self._on_user_text_submitted = on_user_text_submitted
        self._on_conversation_cleared = on_conversation_cleared
        self._on_tts_stop_requested = on_tts_stop_requested
        self._on_voice_input_requested = on_voice_input_requested
        self._on_memory_confirm_requested = on_memory_confirm_requested
        self._on_memory_reject_requested = on_memory_reject_requested
        self._on_memory_list_requested = on_memory_list_requested
        self._on_memory_delete_requested = on_memory_delete_requested
        self._on_product_status_requested = on_product_status_requested
        self._memory_management_enabled = memory_management_enabled

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

        self._avatar_label = QLabel(self._view_model.effective_avatar_text)
        self._avatar_label.setToolTip(self._view_model.effective_avatar_label)
        self._avatar_label.setStyleSheet(self._view_model.effective_avatar_style)
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

        # V10-B: Avatar action status label
        self._avatar_action_label = QLabel(self._view_model.effective_avatar_label)
        self._avatar_action_label.setStyleSheet("font-size: 12px; color: #777;")
        info_layout.addWidget(self._avatar_action_label)

        header_layout.addWidget(info_widget, stretch=1)

        # V11-A: Product status button
        self._product_status_button = QPushButton("状态")
        self._product_status_button.setToolTip("查看小云的能力状态")
        self._product_status_button.pressed.connect(
            self._handle_product_status_clicked
        )
        header_layout.addWidget(self._product_status_button)

        layout.addWidget(header_widget)

        # V11-A: Product status panel (between header and chat history)
        self._product_status_panel = QWidget()
        self._product_status_panel_layout = QVBoxLayout(self._product_status_panel)
        self._product_status_panel_layout.setContentsMargins(8, 8, 8, 8)
        self._product_status_text = QLabel()
        self._product_status_text.setWordWrap(True)
        self._product_status_text.setStyleSheet("color: #333; font-size: 13px;")
        self._product_status_panel_layout.addWidget(self._product_status_text)
        # V11-C: Startup diagnostics details in product status panel
        self._startup_diagnostics_text = QLabel()
        self._startup_diagnostics_text.setWordWrap(True)
        self._startup_diagnostics_text.setStyleSheet("font-size: 12px; color: #777; padding-top: 4px;")
        self._product_status_panel_layout.addWidget(self._startup_diagnostics_text)
        self._product_status_panel.setVisible(False)
        layout.addWidget(self._product_status_panel)

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

        # Memory suggestion widget (V8-I)
        self._memory_suggestion_widget = QWidget()
        self._memory_suggestion_layout = QVBoxLayout(self._memory_suggestion_widget)
        self._memory_suggestion_layout.setContentsMargins(8, 8, 8, 8)

        self._memory_suggestion_title = QLabel("要我记住这件事吗？")
        self._memory_suggestion_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._memory_suggestion_layout.addWidget(self._memory_suggestion_title)

        self._memory_suggestion_text = QLabel("")
        self._memory_suggestion_text.setWordWrap(True)
        self._memory_suggestion_text.setStyleSheet("padding: 4px 0; color: #333;")
        self._memory_suggestion_layout.addWidget(self._memory_suggestion_text)

        memory_button_row = QWidget()
        memory_button_layout = QHBoxLayout(memory_button_row)
        memory_button_layout.setContentsMargins(0, 0, 0, 0)

        self._memory_confirm_button = QPushButton("记住")
        self._memory_confirm_button.clicked.connect(self._on_memory_confirm_clicked)
        memory_button_layout.addWidget(self._memory_confirm_button)

        self._memory_reject_button = QPushButton("不记")
        self._memory_reject_button.clicked.connect(self._on_memory_reject_clicked)
        memory_button_layout.addWidget(self._memory_reject_button)

        self._memory_suggestion_layout.addWidget(memory_button_row)
        self._memory_suggestion_widget.setVisible(False)
        layout.addWidget(self._memory_suggestion_widget)

        # Memory panel widget (V8-J)
        self._memory_panel_widget = QWidget()
        self._memory_panel_layout = QVBoxLayout(self._memory_panel_widget)
        self._memory_panel_layout.setContentsMargins(8, 8, 8, 8)

        self._memory_panel_title = QLabel("已保存的记忆")
        self._memory_panel_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._memory_panel_layout.addWidget(self._memory_panel_title)

        self._memory_panel_text = QLabel("")
        self._memory_panel_text.setWordWrap(True)
        self._memory_panel_text.setStyleSheet("padding: 4px 0; color: #333;")
        self._memory_panel_layout.addWidget(self._memory_panel_text)

        self._memory_delete_first_button = QPushButton("删除第一条")
        self._memory_delete_first_button.clicked.connect(self._on_memory_delete_first_clicked)
        self._memory_panel_layout.addWidget(self._memory_delete_first_button)

        self._memory_panel_widget.setVisible(False)
        layout.addWidget(self._memory_panel_widget)

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

        self._voice_input_button = QPushButton("语音输入")
        self._voice_input_button.clicked.connect(self._on_voice_input_clicked)
        button_layout.addWidget(self._voice_input_button)

        self._memory_panel_button = QPushButton("记忆")
        self._memory_panel_button.clicked.connect(self._on_memory_panel_clicked)
        self._memory_panel_button.setVisible(memory_management_enabled)
        button_layout.addWidget(self._memory_panel_button)

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

    def _on_voice_input_clicked(self) -> None:
        """Handle voice input button click."""
        if self._on_voice_input_requested:
            self._on_voice_input_requested()

    def _on_memory_confirm_clicked(self) -> None:
        """Handle memory confirm button click."""
        suggestion = self._view_model.memory_suggestion
        if suggestion is None:
            return
        if self._on_memory_confirm_requested:
            self._on_memory_confirm_requested(suggestion.pending_id)

    def _on_memory_reject_clicked(self) -> None:
        """Handle memory reject button click."""
        suggestion = self._view_model.memory_suggestion
        if suggestion is None:
            return
        if self._on_memory_reject_requested:
            self._on_memory_reject_requested(suggestion.pending_id)

    def _on_memory_panel_clicked(self) -> None:
        """Handle memory panel button click."""
        self._view_model.toggle_memory_panel()
        if self._view_model.memory_panel_visible and self._on_memory_list_requested:
            self._on_memory_list_requested()
        self.update_from_view_model()

    def _on_memory_delete_first_clicked(self) -> None:
        """Handle delete first memory record button click."""
        if not self._view_model.memory_records:
            return
        first = self._view_model.memory_records[0]
        if self._on_memory_delete_requested:
            self._on_memory_delete_requested(first.record_id)

    def _handle_product_status_clicked(self) -> None:
        """Handle product status button click."""
        if self._on_product_status_requested is not None:
            self._on_product_status_requested()

    def update_from_view_model(self) -> None:
        """Update UI from view model state."""
        self._name_label.setText(self._view_model.companion_name)
        self._subtitle_label.setText(self._view_model.companion_subtitle)
        self._avatar_label.setText(self._view_model.effective_avatar_text)
        self._avatar_label.setToolTip(self._view_model.effective_avatar_label)
        self._avatar_label.setStyleSheet(self._view_model.effective_avatar_style)
        self._avatar_action_label.setText(self._view_model.effective_avatar_label)
        self._state_label.setText(self._view_model.effective_display_text)
        self._chat_history.setPlainText(
            render_chat_messages(self._view_model.chat_messages)
        )
        self._chat_history.moveCursor(QTextCursor.MoveOperation.End)
        self._error_label.setText(self._view_model.error_text)
        self._error_label.setVisible(bool(self._view_model.error_text))

        # Update memory suggestion widget (V8-I)
        suggestion = self._view_model.memory_suggestion
        if suggestion is None:
            self._memory_suggestion_widget.setVisible(False)
        else:
            self._memory_suggestion_widget.setVisible(True)
            self._memory_suggestion_text.setText(
                f"「{render_memory_suggestion_text(suggestion.text, max_chars=80)}」"
            )

        # Update memory panel widget (V8-J)
        if not self._view_model.memory_panel_visible:
            self._memory_panel_widget.setVisible(False)
        else:
            self._memory_panel_widget.setVisible(True)
            records = self._view_model.memory_records
            if not records:
                self._memory_panel_text.setText("还没有保存的记忆")
            else:
                lines: list[str] = []
                for i, record in enumerate(records[:5], 1):
                    truncated = render_memory_record_text(record.text, max_chars=80)
                    lines.append(f"{i}. {truncated}")
                self._memory_panel_text.setText("\n".join(lines))
            self._memory_delete_first_button.setEnabled(bool(records))

        # Update product status panel (V11-A)
        self._product_status_panel.setVisible(self._view_model.product_status_visible)
        self._product_status_text.setText(self._view_model.product_status_text)
        # V11-C: Startup diagnostics details
        self._startup_diagnostics_text.setText(self._view_model.startup_diagnostics_text)

        is_listening = self._view_model.state == AppState.LISTENING
        is_thinking = self._view_model.state == AppState.THINKING
        is_speaking = self._view_model.state == AppState.SPEAKING
        busy = is_listening or is_thinking or is_speaking
        self._send_button.setEnabled(not busy)
        self._input_field.setEnabled(not busy)
        self._new_conversation_button.setEnabled(not busy)
        self._voice_input_button.setEnabled(not busy)
        self._stop_speaking_button.setEnabled(is_speaking)
