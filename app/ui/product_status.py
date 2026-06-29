"""Product status view types (V11-A)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductStatusItem:
    """A single product status item."""

    label: str
    enabled: bool
    detail: str = ""


@dataclass(frozen=True)
class ProductStatusView:
    """A collection of product status items."""

    items: tuple[ProductStatusItem, ...]


def render_status_item(item: ProductStatusItem) -> str:
    """Render a single status item to a display string.

    Args:
        item: The product status item to render.

    Returns:
        A string like "✅ 对话：已启用" or "❌ 记忆上下文".
    """
    prefix = "✅" if item.enabled else "❌"
    if item.detail:
        return f"{prefix} {item.label}：{item.detail}"
    return f"{prefix} {item.label}"


def render_status_view(view: ProductStatusView) -> str:
    """Render a full status view to a multi-line display string.

    Args:
        view: The product status view to render.

    Returns:
        A newline-separated string of rendered status items.
    """
    return "\n".join(render_status_item(item) for item in view.items)
