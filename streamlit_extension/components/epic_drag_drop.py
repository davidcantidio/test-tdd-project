"""
🎛️ Epic Drag & Drop Component using streamlit-elements

Provides a real drag-drop grid for epic reordering, with a safe
fallback in callers when the dependency is unavailable.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

# Import inside functions where possible in callers to allow optional dependency
from streamlit_elements import elements, dashboard, mui  # type: ignore


def layout_to_order(updated_layout: List[Dict[str, Any]]) -> List[int]:
    """Convert React Grid Layout payload to ordered epic IDs.

    Sorts by (y, then x) to obtain a stable vertical order.
    Accepts items with 'i' fields like 'epic_123'.
    Ignores unknown/malformed items.
    """
    if not isinstance(updated_layout, list):
        return []

    def _to_id(item: Dict[str, Any]) -> int | None:
        i = item.get("i")
        if isinstance(i, str) and i.startswith("epic_"):
            try:
                return int(i.split("_", 1)[1])
            except ValueError:
                return None
        return None

    def _safe_int(value, default=0):
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    sorted_items = sorted(
        [it for it in updated_layout if isinstance(it, dict) and "i" in it],
        key=lambda it: (_safe_int(it.get("y")), _safe_int(it.get("x"))),
    )
    ordered_ids: List[int] = []
    for it in sorted_items:
        eid = _to_id(it)
        if eid is not None:
            ordered_ids.append(eid)
    return ordered_ids


def render_epic_drag_drop(
    epics: List[Any], on_layout_change: Callable[[List[Dict[str, Any]]], None]
) -> None:
    """Render epic cards with drag-drop using streamlit-elements.

    Args:
        epics: ViewModelEpic-like objects with id, title, epic_key, description, status
        on_layout_change: callback receiving updated layout (list of dicts)
    """
    # Build initial layout (single column, vertical stacking)
    layout: List[Any] = []
    for i, epic in enumerate(epics):
        layout.append(
            dashboard.Item(
                f"epic_{epic.id}",
                0,
                i * 3,  # y position keeps spacing between rows
                12,
                2,
                isDraggable=True,
                isResizable=False,
            )
        )

    with elements("epic_review_drag_grid"):
        with dashboard.Grid(layout, onLayoutChange=on_layout_change, cols=12, rowHeight=30, draggableHandle=".drag-handle"):
            for epic in epics:
                with mui.Paper(key=f"epic_{epic.id}", elevation=2, sx={"p": 2, "mb": 1}):
                    # Simple card header with drag handle and title
                    mui.Stack(direction="row", spacing=1, alignItems="center")(
                        mui.Icon("drag_indicator", className="drag-handle"),
                        mui.Typography(epic.title, variant="subtitle1"),
                        mui.Chip(label=epic.status, size="small", variant="outlined"),
                    )
                    # Optional: show a short description
                    if getattr(epic, "description", ""):
                        mui.Typography(str(epic.description)[:180], variant="body2", sx={"mt": 1})
