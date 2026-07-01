"""Desktop window implementation."""

from collections.abc import Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.contracts.states import AppState
from app.core.config import get_config
from app.ui import window_style
from app.ui.avatar_expression_view import build_avatar_expression_view
from app.ui.chat_message import ChatMessage
from app.ui.conversation_view import (
    get_input_placeholder,
    render_empty_conversation_text,
)
from app.ui.desktop_presence import (
    COMPACT_MODE_HEIGHT,
    COMPACT_MODE_WIDTH,
    render_compact_button_text,
    render_pin_button_text,
)
from app.ui.live2d_desktop_window import calculate_dragged_position
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
        return render_empty_conversation_text()

    lines: list[str] = []
    for msg in messages:
        if msg.role == "user":
            lines.append("你：")
            lines.append(msg.text)
        else:
            lines.append("小云：")
            lines.append(msg.text)
        lines.append("")  # blank line between messages
        lines.append("")  # extra spacing for readability (Phase 2-B)

    # Remove trailing blank lines
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
        on_add_manual_memory_requested: Callable[[str], None] | None = None,
        on_product_status_requested: Callable[[], None] | None = None,
        on_hide_requested: Callable[[], None] | None = None,
        on_close_requested: Callable[[], bool] | None = None,
        on_live2d_scale_up_requested: Callable[[], None] | None = None,
        on_live2d_scale_down_requested: Callable[[], None] | None = None,
        on_live2d_opacity_down_requested: Callable[[], None] | None = None,
        on_live2d_opacity_up_requested: Callable[[], None] | None = None,
        on_live2d_visibility_toggled: Callable[[], None] | None = None,
        on_live2d_position_reset_requested: Callable[[], None] | None = None,
        on_live2d_model_selected: Callable[[str], None] | None = None,
        on_live2d_models_refresh_requested: Callable[[], None] | None = None,
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
        self._on_add_manual_memory_requested = on_add_manual_memory_requested
        self._on_product_status_requested = on_product_status_requested
        self._on_hide_requested = on_hide_requested
        self._on_close_requested = on_close_requested
        self._on_live2d_scale_up_requested = on_live2d_scale_up_requested
        self._on_live2d_scale_down_requested = on_live2d_scale_down_requested
        self._on_live2d_opacity_down_requested = on_live2d_opacity_down_requested
        self._on_live2d_opacity_up_requested = on_live2d_opacity_up_requested
        self._on_live2d_visibility_toggled = on_live2d_visibility_toggled
        self._on_live2d_position_reset_requested = on_live2d_position_reset_requested
        self._on_live2d_model_selected = on_live2d_model_selected
        self._on_live2d_models_refresh_requested = on_live2d_models_refresh_requested
        self._memory_management_enabled = memory_management_enabled
        self._drag_origin = None
        self._window_origin = None

        config = get_config()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(config.window_width, config.window_height)
        # Phase 2-D: Store normal window size for compact mode restoration
        self._normal_window_width = config.window_width
        self._normal_window_height = config.window_height

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Companion header — subtle card background (Phase 2-C)
        header_widget = QWidget()
        self._drag_handle_widgets: list[QWidget] = [header_widget]
        header_widget.setStyleSheet(window_style.HEADER_CARD_STYLE)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 10, 12, 10)

        self._avatar_label = QLabel(self._view_model.effective_avatar_text)
        self._avatar_label.setToolTip(self._view_model.effective_avatar_label)
        self._avatar_label.setStyleSheet(self._view_model.effective_avatar_style)
        header_layout.addWidget(self._avatar_label)
        self._drag_handle_widgets.append(self._avatar_label)

        # Avatar expression label (Phase 2-H)
        self._avatar_expression_label = QLabel()
        self._avatar_expression_label.setStyleSheet(
            window_style.AVATAR_EXPRESSION_LABEL_STYLE
        )
        header_layout.addWidget(self._avatar_expression_label)
        self._drag_handle_widgets.append(self._avatar_expression_label)

        info_widget = QWidget()
        self._drag_handle_widgets.append(info_widget)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self._name_label = QLabel(self._view_model.companion_name)
        self._name_label.setStyleSheet(window_style.NAME_LABEL_STYLE)
        info_layout.addWidget(self._name_label)
        self._drag_handle_widgets.append(self._name_label)

        self._subtitle_label = QLabel(self._view_model.companion_subtitle)
        self._subtitle_label.setStyleSheet(window_style.SUBTITLE_LABEL_STYLE)
        info_layout.addWidget(self._subtitle_label)
        self._drag_handle_widgets.append(self._subtitle_label)

        # Phase 2-A: Natural companion status text
        self._companion_status_label = QLabel(self._view_model.companion_status_text)
        self._companion_status_label.setStyleSheet(window_style.STATUS_LABEL_STYLE)
        info_layout.addWidget(self._companion_status_label)
        self._drag_handle_widgets.append(self._companion_status_label)

        # Phase 3-D: Proactive status hint (e.g., "小云会安静一会儿。")
        self._proactive_status_label = QLabel(self._view_model.proactive_status_text)
        self._proactive_status_label.setStyleSheet(window_style.PROACTIVE_STATUS_LABEL_STYLE)
        info_layout.addWidget(self._proactive_status_label)
        self._drag_handle_widgets.append(self._proactive_status_label)

        # Phase 2-A: Version and release stage
        version_text = f"{self._view_model.companion_version_text} · {self._view_model.companion_release_stage_text}"
        self._version_label = QLabel(version_text)
        self._version_label.setStyleSheet(window_style.VERSION_LABEL_STYLE)
        info_layout.addWidget(self._version_label)
        self._drag_handle_widgets.append(self._version_label)

        header_layout.addWidget(info_widget, stretch=1)

        # V11-A: Product status button — subdued access point (Phase 2-C)
        self._product_status_button = QPushButton("状态")
        self._product_status_button.setToolTip("查看小云的能力状态")
        self._product_status_button.setStyleSheet(window_style.STATUS_BUTTON_STYLE)
        self._product_status_button.pressed.connect(
            self._handle_product_status_clicked
        )
        header_layout.addWidget(self._product_status_button)

        # Phase 2-D: Desktop presence shell — pin and compact buttons
        self._pin_button = QPushButton(render_pin_button_text(self._view_model.always_on_top))
        self._pin_button.setStyleSheet(window_style.STATUS_BUTTON_STYLE)
        self._pin_button.pressed.connect(self._handle_pin_clicked)
        header_layout.addWidget(self._pin_button)

        self._compact_button = QPushButton(render_compact_button_text(self._view_model.compact_mode))
        self._compact_button.setStyleSheet(window_style.STATUS_BUTTON_STYLE)
        self._compact_button.pressed.connect(self._handle_compact_clicked)
        header_layout.addWidget(self._compact_button)

        layout.addWidget(header_widget)
        for drag_handle in self._drag_handle_widgets:
            drag_handle.installEventFilter(self)

        live2d_control_row = QWidget()
        live2d_control_layout = QHBoxLayout(live2d_control_row)
        live2d_control_layout.setContentsMargins(0, 0, 0, 0)
        self._live2d_scale_up_button = QPushButton("人物+")
        self._live2d_scale_up_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_scale_up_button.clicked.connect(self._on_live2d_scale_up_clicked)
        live2d_control_layout.addWidget(self._live2d_scale_up_button)
        self._live2d_scale_down_button = QPushButton("人物-")
        self._live2d_scale_down_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_scale_down_button.clicked.connect(self._on_live2d_scale_down_clicked)
        live2d_control_layout.addWidget(self._live2d_scale_down_button)
        self._live2d_opacity_down_button = QPushButton("淡一点")
        self._live2d_opacity_down_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_opacity_down_button.clicked.connect(self._on_live2d_opacity_down_clicked)
        live2d_control_layout.addWidget(self._live2d_opacity_down_button)
        self._live2d_opacity_up_button = QPushButton("实一点")
        self._live2d_opacity_up_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_opacity_up_button.clicked.connect(self._on_live2d_opacity_up_clicked)
        live2d_control_layout.addWidget(self._live2d_opacity_up_button)
        self._live2d_toggle_button = QPushButton("人物")
        self._live2d_toggle_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_toggle_button.clicked.connect(self._on_live2d_toggle_clicked)
        live2d_control_layout.addWidget(self._live2d_toggle_button)
        self._live2d_reset_button = QPushButton("重置人物")
        self._live2d_reset_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_reset_button.clicked.connect(self._on_live2d_reset_clicked)
        live2d_control_layout.addWidget(self._live2d_reset_button)
        live2d_control_layout.addStretch()
        layout.addWidget(live2d_control_row)
        self._live2d_model_status_label = QLabel(
            self._view_model.live2d_model_catalog_summary
        )
        self._live2d_model_status_label.setWordWrap(True)
        self._live2d_model_status_label.setStyleSheet(window_style.STATUS_LABEL_STYLE)
        layout.addWidget(self._live2d_model_status_label)
        self._live2d_model_selector = QComboBox()
        self._live2d_model_selector.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._live2d_model_selector.currentIndexChanged.connect(
            self._on_live2d_model_selected_from_combo
        )
        layout.addWidget(self._live2d_model_selector)
        self._sync_live2d_model_selector()
        self._live2d_model_refresh_button = QPushButton("刷新模型")
        self._live2d_model_refresh_button.setStyleSheet(
            window_style.SECONDARY_BUTTON_STYLE
        )
        self._live2d_model_refresh_button.clicked.connect(
            self._on_live2d_models_refresh_clicked
        )
        layout.addWidget(self._live2d_model_refresh_button)
        self._live2d_model_details_label = QLabel(
            self._view_model.live2d_model_catalog_details
        )
        self._live2d_model_details_label.setWordWrap(True)
        self._live2d_model_details_label.setStyleSheet(window_style.STATUS_LABEL_STYLE)
        layout.addWidget(self._live2d_model_details_label)

        # Phase 3-B: Onboarding card — shown at first run
        self._onboarding_card = QWidget()
        self._onboarding_card.setStyleSheet(window_style.ONBOARDING_CARD_STYLE)
        self._onboarding_card_layout = QVBoxLayout(self._onboarding_card)
        self._onboarding_card_layout.setContentsMargins(10, 8, 10, 8)
        self._onboarding_title = QLabel()
        self._onboarding_title.setStyleSheet(window_style.ONBOARDING_TITLE_STYLE)
        self._onboarding_card_layout.addWidget(self._onboarding_title)
        self._onboarding_subtitle = QLabel()
        self._onboarding_subtitle.setStyleSheet(window_style.ONBOARDING_SUBTITLE_STYLE)
        self._onboarding_card_layout.addWidget(self._onboarding_subtitle)
        self._onboarding_bullets = QLabel()
        self._onboarding_bullets.setStyleSheet(window_style.ONBOARDING_BULLET_STYLE)
        self._onboarding_bullets.setWordWrap(True)
        self._onboarding_card_layout.addWidget(self._onboarding_bullets)
        onboarding_button_row = QWidget()
        onboarding_button_layout = QHBoxLayout(onboarding_button_row)
        onboarding_button_layout.setContentsMargins(0, 4, 0, 0)
        self._onboarding_dismiss_button = QPushButton("知道了")
        self._onboarding_dismiss_button.setStyleSheet(window_style.PRIMARY_BUTTON_STYLE)
        self._onboarding_dismiss_button.clicked.connect(self._on_onboarding_dismiss)
        onboarding_button_layout.addWidget(self._onboarding_dismiss_button)
        self._onboarding_settings_button = QPushButton("打开设置")
        self._onboarding_settings_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._onboarding_settings_button.clicked.connect(self._on_onboarding_open_settings)
        onboarding_button_layout.addWidget(self._onboarding_settings_button)
        onboarding_button_layout.addStretch()
        self._onboarding_card_layout.addWidget(onboarding_button_row)
        layout.addWidget(self._onboarding_card)

        # V11-A: Product status panel — card style (Phase 2-C)
        self._product_status_panel = QWidget()
        self._product_status_panel.setStyleSheet(
            "background-color: #f0f4f8; border-radius: 6px; padding: 4px;"
        )
        self._product_status_panel_layout = QVBoxLayout(self._product_status_panel)
        self._product_status_panel_layout.setContentsMargins(10, 8, 10, 8)
        self._product_status_text = QLabel()
        self._product_status_text.setWordWrap(True)
        self._product_status_text.setStyleSheet(window_style.PRODUCT_STATUS_TEXT_STYLE)
        self._product_status_panel_layout.addWidget(self._product_status_text)
        # V11-C: Startup diagnostics details in product status panel
        self._startup_diagnostics_text = QLabel()
        self._startup_diagnostics_text.setWordWrap(True)
        self._startup_diagnostics_text.setStyleSheet(window_style.STARTUP_DIAGNOSTICS_TEXT_STYLE)
        self._product_status_panel_layout.addWidget(self._startup_diagnostics_text)
        self._product_status_panel.setVisible(False)
        layout.addWidget(self._product_status_panel)

        # Phase 2-E: Settings panel — card style, mutually exclusive with status panel
        # Uses QScrollArea so all sections are readable even when content is long
        self._settings_panel = QWidget()
        self._settings_panel.setStyleSheet(
            "background-color: #f0f7f0; border-radius: 6px; padding: 4px;"
        )
        self._settings_panel_layout = QVBoxLayout(self._settings_panel)
        self._settings_panel_layout.setContentsMargins(10, 8, 10, 8)
        # Phase 3-E: Copy config button row
        self._settings_copy_button = QPushButton("复制配置示例")
        self._settings_copy_button.setStyleSheet(window_style.SETTINGS_COPY_BUTTON_STYLE)
        self._settings_copy_button.clicked.connect(self._on_copy_config_example)
        self._settings_panel_layout.addWidget(self._settings_copy_button)
        self._settings_scroll = QScrollArea()
        self._settings_scroll.setWidgetResizable(True)
        self._settings_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._settings_scroll.setStyleSheet("background: transparent; border: none;")
        self._settings_text = QLabel()
        self._settings_text.setWordWrap(True)
        self._settings_text.setStyleSheet(window_style.PRODUCT_STATUS_TEXT_STYLE)
        self._settings_scroll.setWidget(self._settings_text)
        self._settings_panel_layout.addWidget(self._settings_scroll)
        self._settings_panel.setVisible(False)
        layout.addWidget(self._settings_panel)

        # Chat history display
        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setStyleSheet(window_style.CHAT_HISTORY_STYLE)
        self._chat_history.setPlainText(render_chat_messages(self._view_model.chat_messages))
        layout.addWidget(self._chat_history, stretch=1)

        # Error display
        self._error_label = QLabel(self._view_model.error_text)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(window_style.ERROR_LABEL_STYLE)
        self._error_label.setVisible(bool(self._view_model.error_text))
        layout.addWidget(self._error_label)

        # Memory suggestion widget (V8-I) — card style (Phase 2-C/3-C)
        self._memory_suggestion_widget = QWidget()
        self._memory_suggestion_widget.setStyleSheet(
            "background-color: #f0f7ff; border-radius: 6px; padding: 4px;"
        )
        self._memory_suggestion_layout = QVBoxLayout(self._memory_suggestion_widget)
        self._memory_suggestion_layout.setContentsMargins(10, 8, 10, 8)

        self._memory_suggestion_title = QLabel("要我记住这件事吗？")
        self._memory_suggestion_title.setStyleSheet(window_style.MEMORY_SUGGESTION_TITLE_STYLE)
        self._memory_suggestion_layout.addWidget(self._memory_suggestion_title)

        self._memory_suggestion_text = QLabel("")
        self._memory_suggestion_text.setWordWrap(True)
        self._memory_suggestion_text.setStyleSheet(window_style.MEMORY_SUGGESTION_TEXT_STYLE)
        self._memory_suggestion_layout.addWidget(self._memory_suggestion_text)

        self._memory_suggestion_privacy = QLabel("")
        self._memory_suggestion_privacy.setWordWrap(True)
        self._memory_suggestion_privacy.setStyleSheet(window_style.MEMORY_SUGGESTION_PRIVACY_STYLE)
        self._memory_suggestion_layout.addWidget(self._memory_suggestion_privacy)

        memory_button_row = QWidget()
        memory_button_layout = QHBoxLayout(memory_button_row)
        memory_button_layout.setContentsMargins(0, 0, 0, 0)

        self._memory_confirm_button = QPushButton("记住")
        self._memory_confirm_button.setStyleSheet(window_style.PRIMARY_BUTTON_STYLE)
        self._memory_confirm_button.clicked.connect(self._on_memory_confirm_clicked)
        memory_button_layout.addWidget(self._memory_confirm_button)

        self._memory_reject_button = QPushButton("不记")
        self._memory_reject_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._memory_reject_button.clicked.connect(self._on_memory_reject_clicked)
        memory_button_layout.addWidget(self._memory_reject_button)

        self._memory_suggestion_layout.addWidget(memory_button_row)
        self._memory_suggestion_widget.setVisible(False)
        layout.addWidget(self._memory_suggestion_widget)

        # Memory panel widget (V8-J) — card style (Phase 2-C/3-C)
        self._memory_panel_widget = QWidget()
        self._memory_panel_widget.setStyleSheet(
            "background-color: #f0f7ff; border-radius: 6px; padding: 4px;"
        )
        self._memory_panel_layout = QVBoxLayout(self._memory_panel_widget)
        self._memory_panel_layout.setContentsMargins(10, 8, 10, 8)

        self._memory_panel_title = QLabel("小云记住的事")
        self._memory_panel_title.setStyleSheet(window_style.MEMORY_PANEL_TITLE_STYLE)
        self._memory_panel_layout.addWidget(self._memory_panel_title)

        self._memory_panel_status = QLabel("")
        self._memory_panel_status.setWordWrap(True)
        self._memory_panel_status.setStyleSheet(window_style.MEMORY_PANEL_PRIVACY_STYLE)
        self._memory_panel_status.setVisible(False)
        self._memory_panel_layout.addWidget(self._memory_panel_status)

        self._memory_panel_privacy = QLabel("")
        self._memory_panel_privacy.setWordWrap(True)
        self._memory_panel_privacy.setStyleSheet(window_style.MEMORY_PANEL_PRIVACY_STYLE)
        self._memory_panel_layout.addWidget(self._memory_panel_privacy)

        # Phase 3-C: Manual memory add input row — placed before records for usability
        self._memory_manual_input = QLineEdit()
        self._memory_manual_input.setPlaceholderText("想让小云记住什么...")
        self._memory_manual_input.setStyleSheet("padding: 4px; font-size: 13px;")
        self._memory_manual_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._memory_manual_input.setEnabled(True)
        self._memory_manual_input.setReadOnly(False)
        self._memory_manual_input.returnPressed.connect(self._on_memory_add_manual_clicked)
        self._memory_panel_layout.addWidget(self._memory_manual_input)

        memory_add_button_row = QWidget()
        memory_add_button_layout = QHBoxLayout(memory_add_button_row)
        memory_add_button_layout.setContentsMargins(0, 0, 0, 0)
        self._memory_add_button = QPushButton("添加记忆")
        self._memory_add_button.setStyleSheet(window_style.PRIMARY_BUTTON_STYLE)
        self._memory_add_button.clicked.connect(self._on_memory_add_manual_clicked)
        memory_add_button_layout.addWidget(self._memory_add_button)
        memory_add_button_layout.addStretch()
        self._memory_panel_layout.addWidget(memory_add_button_row)

        self._memory_panel_text = QLabel("")
        self._memory_panel_text.setWordWrap(True)
        self._memory_panel_text.setStyleSheet(window_style.MEMORY_PANEL_TEXT_STYLE)
        self._memory_panel_layout.addWidget(self._memory_panel_text)

        self._memory_delete_record_buttons: list[QPushButton] = []
        for index in range(5):
            button = QPushButton(f"删除第 {index + 1} 条记忆")
            button.setStyleSheet(window_style.DESTRUCTIVE_BUTTON_STYLE)
            button.clicked.connect(
                lambda _checked=False, record_index=index: self._on_memory_delete_clicked(
                    record_index
                )
            )
            button.setVisible(False)
            self._memory_delete_record_buttons.append(button)
            self._memory_panel_layout.addWidget(button)
        self._memory_delete_first_button = self._memory_delete_record_buttons[0]

        self._memory_panel_widget.setVisible(False)

        layout.addWidget(self._memory_panel_widget)

        # Input field (Phase 2-B)
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText(get_input_placeholder())
        self._input_field.returnPressed.connect(self._on_send_clicked)
        layout.addWidget(self._input_field)

        # Phase 2-D: Auxiliary button row — hidden in compact mode
        self._aux_button_row = QWidget()
        aux_button_layout = QHBoxLayout(self._aux_button_row)
        aux_button_layout.setContentsMargins(0, 0, 0, 0)

        self._new_conversation_button = QPushButton("新对话")
        self._new_conversation_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._new_conversation_button.clicked.connect(self._on_new_conversation_clicked)
        aux_button_layout.addWidget(self._new_conversation_button)

        self._voice_input_button = QPushButton("语音输入")
        self._voice_input_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._voice_input_button.clicked.connect(self._on_voice_input_clicked)
        aux_button_layout.addWidget(self._voice_input_button)

        self._memory_panel_button = QPushButton("记忆")
        self._memory_panel_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._memory_panel_button.clicked.connect(self._on_memory_panel_clicked)
        self._memory_panel_button.setVisible(memory_management_enabled)
        aux_button_layout.addWidget(self._memory_panel_button)

        self._stop_speaking_button = QPushButton("停止说话")
        self._stop_speaking_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._stop_speaking_button.clicked.connect(self._on_tts_stop_clicked)
        self._stop_speaking_button.setEnabled(False)
        aux_button_layout.addWidget(self._stop_speaking_button)

        # Phase 2-E: Settings button
        self._settings_button = QPushButton("设置")
        self._settings_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._settings_button.clicked.connect(self._handle_settings_clicked)
        aux_button_layout.addWidget(self._settings_button)

        # Phase 2-F: Hide button
        self._hide_button = QPushButton("隐藏")
        self._hide_button.setStyleSheet(window_style.SECONDARY_BUTTON_STYLE)
        self._hide_button.clicked.connect(self._on_hide_clicked)
        self._hide_button.setVisible(on_hide_requested is not None)
        self._hide_button.setEnabled(self._view_model.tray_available)
        aux_button_layout.addWidget(self._hide_button)

        aux_button_layout.addStretch()
        layout.addWidget(self._aux_button_row)

        # Phase 2-D: Send button row — always visible even in compact mode
        self._send_button_row = QWidget()
        send_button_layout = QHBoxLayout(self._send_button_row)
        send_button_layout.setContentsMargins(0, 0, 0, 0)
        send_button_layout.addStretch()

        self._send_button = QPushButton("发送")
        self._send_button.setStyleSheet(window_style.PRIMARY_BUTTON_STYLE)
        self._send_button.clicked.connect(self._on_send_clicked)
        send_button_layout.addWidget(self._send_button)
        layout.addWidget(self._send_button_row)

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
        if self._view_model.memory_panel_visible:
            self._memory_manual_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _on_memory_delete_clicked(self, index: int) -> None:
        """Handle delete memory record button click."""
        if index < 0 or index >= len(self._view_model.memory_records):
            return
        record = self._view_model.memory_records[index]
        if self._on_memory_delete_requested:
            self._on_memory_delete_requested(record.record_id)

    def _on_memory_add_manual_clicked(self) -> None:
        """Handle manual memory add button click (Phase 3-C)."""
        text = self._memory_manual_input.text().strip()
        if not text:
            return
        if self._on_add_manual_memory_requested is None:
            return
        self._on_add_manual_memory_requested(text)
        self._memory_manual_input.clear()
        # Refresh memory list if panel is open
        if self._view_model.memory_panel_visible and self._on_memory_list_requested:
            self._on_memory_list_requested()
        self.update_from_view_model()

    def _handle_settings_clicked(self) -> None:
        """Handle settings button click (Phase 2-E / Phase 3-E).

        Mutual exclusivity: opening settings closes product status and memory panel.
        """
        # Phase 3-E: close memory panel when opening settings
        if not self._view_model.settings_visible:
            self._view_model.memory_panel_visible = False
        self._view_model.toggle_settings_visible()
        self.update_from_view_model()

    def _on_copy_config_example(self) -> None:
        """Handle copy config example button click (Phase 3-E).

        Copies the env example text to system clipboard.
        Does not write to .env or any file.
        Silently succeeds — no feedback UI in this version.
        """
        from app.ui.settings_controls_view import build_env_example
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            try:
                clipboard.setText(build_env_example())
            except Exception:
                # Clipboard may be unavailable in some environments (e.g., offscreen)
                pass

    def _on_hide_clicked(self) -> None:
        """Handle hide button click (Phase 2-F)."""
        if self._on_hide_requested:
            self._on_hide_requested()

    def _on_live2d_scale_up_clicked(self) -> None:
        if self._on_live2d_scale_up_requested:
            self._on_live2d_scale_up_requested()

    def _on_live2d_scale_down_clicked(self) -> None:
        if self._on_live2d_scale_down_requested:
            self._on_live2d_scale_down_requested()

    def _on_live2d_opacity_down_clicked(self) -> None:
        if self._on_live2d_opacity_down_requested:
            self._on_live2d_opacity_down_requested()

    def _on_live2d_opacity_up_clicked(self) -> None:
        if self._on_live2d_opacity_up_requested:
            self._on_live2d_opacity_up_requested()

    def _on_live2d_toggle_clicked(self) -> None:
        if self._on_live2d_visibility_toggled:
            self._on_live2d_visibility_toggled()

    def _on_live2d_reset_clicked(self) -> None:
        if self._on_live2d_position_reset_requested:
            self._on_live2d_position_reset_requested()

    def _on_live2d_model_selected_from_combo(self, _index: int) -> None:
        model_id = self._live2d_model_selector.currentData()
        if not isinstance(model_id, str) or not model_id:
            return
        if not self._view_model.select_live2d_model(model_id):
            return
        if self._on_live2d_model_selected:
            self._on_live2d_model_selected(model_id)

    def _on_live2d_models_refresh_clicked(self) -> None:
        if self._on_live2d_models_refresh_requested:
            self._on_live2d_models_refresh_requested()

    def _sync_live2d_model_selector(self) -> None:
        selector = self._live2d_model_selector
        selector.blockSignals(True)
        selector.clear()
        for model_id, label in self._view_model.live2d_model_options:
            selector.addItem(label, model_id)
        selected_id = self._view_model.selected_live2d_model_id
        if selected_id:
            selected_index = selector.findData(selected_id)
            if selected_index >= 0:
                selector.setCurrentIndex(selected_index)
        selector.setVisible(bool(self._view_model.live2d_model_options))
        selector.blockSignals(False)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        """Allow dragging the main window from non-button header surfaces."""

        if watched not in self._drag_handle_widgets:
            return super().eventFilter(watched, event)

        event_type = event.type()
        if (
            event_type == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._drag_origin = _event_global_position(event)
            self._window_origin = self.pos()
            event.accept()
            return True

        if (
            event_type == QEvent.Type.MouseMove
            and self._drag_origin is not None
            and self._window_origin is not None
        ):
            current = _event_global_position(event)
            next_position = calculate_dragged_position(
                self._window_origin.x(),
                self._window_origin.y(),
                self._drag_origin.x(),
                self._drag_origin.y(),
                current.x(),
                current.y(),
            )
            self.move(next_position.x, next_position.y)
            event.accept()
            return True

        if (
            event_type == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._drag_origin = None
            self._window_origin = None
            event.accept()
            return True

        return super().eventFilter(watched, event)

    def _on_onboarding_dismiss(self) -> None:
        """Handle '知道了' button click (Phase 3-B)."""
        self._view_model.dismiss_onboarding()
        self.update_from_view_model()

    def _on_onboarding_open_settings(self) -> None:
        """Handle '打开设置' button click (Phase 3-B)."""
        self._view_model.open_settings_from_onboarding()
        self.update_from_view_model()

    def _handle_product_status_clicked(self) -> None:
        """Handle product status button click (Phase 2-D).

        If in compact mode, exit compact mode first per spec requirement.
        """
        if self._view_model.compact_mode:
            self._handle_compact_clicked()
        if self._on_product_status_requested is not None:
            self._on_product_status_requested()

    def _handle_pin_clicked(self) -> None:
        """Handle pin button click: toggle always-on-top flag."""
        self._view_model.toggle_always_on_top()
        self._pin_button.setText(render_pin_button_text(self._view_model.always_on_top))
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self._view_model.always_on_top
        )
        self.show()

    def _handle_compact_clicked(self) -> None:
        """Handle compact button click: toggle compact mode."""
        self._view_model.toggle_compact_mode()
        self._compact_button.setText(
            render_compact_button_text(self._view_model.compact_mode)
        )
        if self._view_model.compact_mode:
            # Enter compact mode: save size, shrink, hide aux buttons
            self._normal_window_width = self.width()
            self._normal_window_height = self.height()
            self.resize(COMPACT_MODE_WIDTH, COMPACT_MODE_HEIGHT)
            self._aux_button_row.setVisible(False)
            # Ensure status panel is hidden in compact mode
            if self._view_model.product_status_visible:
                self._view_model.product_status_visible = False
                self._product_status_panel.setVisible(False)
        else:
            # Exit compact mode: restore size, show aux buttons
            self.resize(self._normal_window_width, self._normal_window_height)
            self._aux_button_row.setVisible(True)
        # Sync all UI state including onboarding card visibility
        self.update_from_view_model()

    def update_from_view_model(self) -> None:
        """Update UI from view model state."""
        self._name_label.setText(self._view_model.companion_name)
        self._subtitle_label.setText(self._view_model.companion_subtitle)
        self._avatar_label.setText(self._view_model.effective_avatar_text)
        self._avatar_label.setToolTip(self._view_model.effective_avatar_label)
        self._avatar_label.setStyleSheet(self._view_model.effective_avatar_style)
        # Phase 2-H: Update avatar expression label
        expr = build_avatar_expression_view(self._view_model.avatar_action)
        self._avatar_expression_label.setText(expr.label)
        # Phase 2-A: Update companion status text
        self._companion_status_label.setText(self._view_model.companion_status_text)
        # Phase 3-D: Update proactive status hint
        self._proactive_status_label.setText(self._view_model.proactive_status_text)
        version_text = f"{self._view_model.companion_version_text} · {self._view_model.companion_release_stage_text}"
        self._version_label.setText(version_text)
        # Phase 2-D: Sync presence shell button texts
        self._pin_button.setText(render_pin_button_text(self._view_model.always_on_top))
        self._compact_button.setText(render_compact_button_text(self._view_model.compact_mode))
        self._live2d_model_status_label.setText(
            self._view_model.live2d_model_catalog_summary
        )
        self._live2d_model_details_label.setText(
            self._view_model.live2d_model_catalog_details
        )
        self._sync_live2d_model_selector()
        # Phase 2-D: Sync compact mode layout
        self._aux_button_row.setVisible(not self._view_model.compact_mode)

        # Phase 3-B: Update onboarding card visibility and content
        self._onboarding_card.setVisible(self._view_model.onboarding_visible)
        if self._view_model.onboarding_text:
            # Parse and display the onboarding text
            onboarding_text = self._view_model.onboarding_text
            onboarding_lines = onboarding_text.split("\n", 2)
            if len(onboarding_lines) >= 1:
                self._onboarding_title.setText(onboarding_lines[0])
            if len(onboarding_lines) >= 2:
                self._onboarding_subtitle.setText(onboarding_lines[1])
            if len(onboarding_lines) >= 3:
                self._onboarding_bullets.setText(onboarding_lines[2])

        self._chat_history.setPlainText(
            render_chat_messages(self._view_model.chat_messages)
        )
        self._chat_history.moveCursor(QTextCursor.MoveOperation.End)
        self._error_label.setText(self._view_model.error_text)
        self._error_label.setVisible(bool(self._view_model.error_text))

        # Update memory suggestion widget (V8-I / Phase 3-C)
        suggestion = self._view_model.memory_suggestion
        if suggestion is None:
            self._memory_suggestion_widget.setVisible(False)
        else:
            self._memory_suggestion_widget.setVisible(True)
            # Phase 3-C: Use UX copy for body text
            from app.ui.memory_ux_view import build_memory_suggestion_copy
            suggestion_copy = build_memory_suggestion_copy()
            self._memory_suggestion_text.setText(
                f"「{render_memory_suggestion_text(suggestion.text, max_chars=80)}」\n\n{suggestion_copy.body}"
            )
            self._memory_suggestion_privacy.setText(suggestion_copy.privacy_hint)

        # Update memory panel widget (V8-J / Phase 3-C)
        if not self._view_model.memory_panel_visible:
            self._memory_panel_widget.setVisible(False)
        else:
            self._memory_panel_widget.setVisible(True)
            from app.ui.memory_ux_view import build_memory_panel_copy
            panel_copy = build_memory_panel_copy()
            records = self._view_model.memory_records
            if not records:
                self._memory_panel_text.setText(panel_copy.empty_title)
            else:
                lines: list[str] = []
                for i, record in enumerate(records[:5], 1):
                    truncated = render_memory_record_text(record.text, max_chars=80)
                    lines.append(f"{i}. {truncated}")
                self._memory_panel_text.setText("\n".join(lines))
            self._memory_panel_privacy.setText(panel_copy.privacy_body)
            # Sync per-record delete buttons visibility
            for i, btn in enumerate(self._memory_delete_record_buttons):
                btn.setVisible(i < len(records))
            self._memory_delete_first_button.setEnabled(bool(records))

        # Sync memory status feedback (always, even when panel is hidden)
        self._memory_panel_status.setText(self._view_model.memory_status_text)
        self._memory_panel_status.setVisible(
            self._view_model.memory_panel_visible and bool(self._view_model.memory_status_text)
        )

        # Sync hide button enabled state
        self._hide_button.setEnabled(self._view_model.tray_available)
        if self._view_model.tray_available:
            self._hide_button.setToolTip("隐藏到系统托盘")
        else:
            self._hide_button.setToolTip("托盘不可用，无法隐藏")

        # Update product status panel (V11-A)
        self._product_status_panel.setVisible(self._view_model.product_status_visible)
        self._product_status_text.setText(self._view_model.product_status_text)
        # V11-C: Startup diagnostics details
        self._startup_diagnostics_text.setText(self._view_model.startup_diagnostics_text)

        # Phase 2-E: Update settings panel
        self._settings_panel.setVisible(self._view_model.settings_visible)
        self._settings_text.setText(self._view_model.settings_text)

        is_listening = self._view_model.state == AppState.LISTENING
        is_thinking = self._view_model.state == AppState.THINKING
        is_speaking = self._view_model.state == AppState.SPEAKING
        busy = is_listening or is_thinking or is_speaking
        self._send_button.setEnabled(not busy)
        self._input_field.setEnabled(not busy)
        self._new_conversation_button.setEnabled(not busy)
        self._voice_input_button.setEnabled(not busy)
        self._stop_speaking_button.setEnabled(is_speaking)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Handle window close event (Phase 3-A).

        Delegates to on_close_requested callback if set.
        - Returns True from callback: accept close, application exits.
        - Returns False from callback: ignore close, window already hidden to tray.
        """
        if self._on_close_requested is None:
            event.accept()
            return

        should_accept = self._on_close_requested()
        if should_accept:
            event.accept()
        else:
            event.ignore()


def _event_global_position(event: object) -> object:
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()
