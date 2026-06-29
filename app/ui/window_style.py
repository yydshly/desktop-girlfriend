"""Window style constants for desktop UI polish (Phase 2-C)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Header / companion card area
# ---------------------------------------------------------------------------

# Subtle card background for the top header area
HEADER_CARD_STYLE = "background-color: #f5f7ff; border-radius: 8px; padding: 4px;"

# Avatar expression label — small, below emoji
AVATAR_EXPRESSION_LABEL_STYLE = (
    "font-size: 11px; color: #888; qproperty-alignment: AlignCenter;"
)

# Companion name — prominent and bold
NAME_LABEL_STYLE = "font-size: 20px; font-weight: 700; color: #2c3e50;"

# Companion subtitle — lighter, secondary info
SUBTITLE_LABEL_STYLE = "font-size: 12px; color: #7f8c8d;"

# Natural-language companion status text
STATUS_LABEL_STYLE = "font-size: 14px; color: #555; padding-top: 2px;"

# Version and release stage — subtle
VERSION_LABEL_STYLE = "font-size: 11px; color: #aaa;"

# Status button in header — subdued access point
STATUS_BUTTON_STYLE = (
    "font-size: 12px; padding: 4px 10px; "
    "background-color: #e8ecf0; color: #666; "
    "border: none; border-radius: 4px;"
)

# ---------------------------------------------------------------------------
# Product status panel
# ---------------------------------------------------------------------------

# Status panel text — readable, product-info style
PRODUCT_STATUS_TEXT_STYLE = "color: #333; font-size: 13px; line-height: 1.6;"

# Startup diagnostics detail text — smaller, secondary
STARTUP_DIAGNOSTICS_TEXT_STYLE = (
    "font-size: 12px; color: #888; padding-top: 4px; line-height: 1.5;"
)

# ---------------------------------------------------------------------------
# Chat area
# ---------------------------------------------------------------------------

CHAT_HISTORY_STYLE = "padding: 12px; background-color: #fcfcfc; border-radius: 6px;"

# ---------------------------------------------------------------------------
# Error display
# ---------------------------------------------------------------------------

ERROR_LABEL_STYLE = "color: #c0392b; padding: 8px; font-size: 13px;"

# ---------------------------------------------------------------------------
# Memory suggestion widget
# ---------------------------------------------------------------------------

MEMORY_SUGGESTION_TITLE_STYLE = "font-size: 14px; font-weight: 600; color: #2c3e50;"
MEMORY_SUGGESTION_TEXT_STYLE = "padding: 4px 0; color: #333; font-size: 13px;"
MEMORY_SUGGESTION_PRIVACY_STYLE = "padding: 4px 0; color: #888; font-size: 12px;"

# ---------------------------------------------------------------------------
# Memory panel widget
# ---------------------------------------------------------------------------

MEMORY_PANEL_TITLE_STYLE = "font-size: 14px; font-weight: 600; color: #2c3e50;"
MEMORY_PANEL_TEXT_STYLE = "padding: 4px 0; color: #333; font-size: 13px;"
MEMORY_PANEL_PRIVACY_STYLE = "padding: 4px 0; color: #888; font-size: 12px;"

# ---------------------------------------------------------------------------
# Buttons — primary / secondary distinction (Phase 2-C)
# ---------------------------------------------------------------------------

# Primary action button — send button stands out
PRIMARY_BUTTON_STYLE = (
    "font-size: 14px; padding: 6px 16px; "
    "background-color: #4a90d9; color: white; "
    "border: none; border-radius: 6px; font-weight: 600;"
)

# Secondary / auxiliary buttons — subdued but visible
SECONDARY_BUTTON_STYLE = (
    "font-size: 13px; padding: 5px 12px; "
    "background-color: #eef2f5; color: #555; "
    "border: none; border-radius: 5px;"
)

# Delete / destructive secondary button
DESTRUCTIVE_BUTTON_STYLE = (
    "font-size: 13px; padding: 5px 12px; "
    "background-color: #fdecea; color: #c0392b; "
    "border: none; border-radius: 5px;"
)

# ---------------------------------------------------------------------------
# Onboarding card (Phase 3-B)
# ---------------------------------------------------------------------------

# Onboarding card — light card, subtle border, compact
ONBOARDING_CARD_STYLE = (
    "background-color: #f0f7ff; border-radius: 8px; padding: 12px; "
    "border: 1px solid #c8d9f0;"
)

# Onboarding title — bold, welcoming
ONBOARDING_TITLE_STYLE = "font-size: 16px; font-weight: 700; color: #2c3e50;"

# Onboarding subtitle — secondary text
ONBOARDING_SUBTITLE_STYLE = "font-size: 13px; color: #555; padding: 4px 0;"

# Onboarding bullet text — readable list
ONBOARDING_BULLET_STYLE = "font-size: 12px; color: #444; line-height: 1.7;"

