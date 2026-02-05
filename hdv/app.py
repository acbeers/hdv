"""Textual app for hierarchical CSV viewing."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.widgets import DataTable, Footer, Header, Static

from .data import aggregate_level, load_and_classify


class HDVDataTable(DataTable):
    """DataTable that maps Right to expand and Left to back (instead of cursor movement)."""

    BINDINGS = [
        b for b in DataTable.BINDINGS if b.key not in ("left", "right")
    ] + [
        Binding("left", "back", "Back", show=False),
        Binding("right", "expand", "Expand", show=False),
    ]


class HDVApp(App[None]):
    """Hierarchical Data Viewer - interactive CSV drill-down."""

    TITLE = "HDV"
    SUB_TITLE = "Hierarchical Data Viewer"
    CSS_PATH = "app.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "sort_toggle", "Sort", show=True),
        Binding("left", "back", "Back", show=True),
        Binding("right", "expand", "Expand", show=True),
    ]

    def __init__(
        self,
        source: str | Path | IO[str],
        source_name: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.source = source
        self.source_name = source_name or (
            str(source) if not hasattr(source, "read") else "<stdin>"
        )
        self.df = None
        self.dimension_columns: list[str] = []
        self.numeric_columns: list[str] = []
        self.path: list[str] = []  # current drill-down path (value per level)
        self.sort_by_numeric: bool = False  # False = by dimension label, True = by numeric column

    def on_mount(self) -> None:
        try:
            self.df, self.dimension_columns, self.numeric_columns = load_and_classify(
                self.source
            )
        except Exception as e:
            self.notify(f"Failed to load CSV: {e}", severity="error")
            return
        if not self.dimension_columns:
            self.notify("No non-numeric columns found for hierarchy.", severity="warning")
        self._refresh_table()
        self.query_one(HDVDataTable).focus()

    def _refresh_table(self) -> None:
        table = self.query_one(HDVDataTable)
        table.clear(columns=True)
        self._current_rows = []
        level = len(self.path)
        if level >= len(self.dimension_columns):
            return
        dim_col = self.dimension_columns[level]
        agg_columns = self.numeric_columns if self.numeric_columns else ["count"]
        columns = [dim_col] + agg_columns
        table.add_columns(*columns)
        rows = aggregate_level(
            self.df, self.dimension_columns, self.numeric_columns, self.path
        )
        # Sort: by dimension label or by first numeric column
        if self.sort_by_numeric and agg_columns:
            key_col = agg_columns[0]
            rows = sorted(rows, key=lambda r: r[1].get(key_col, 0), reverse=True)
        else:
            rows = sorted(rows, key=lambda r: (r[0] or ""))
        self._current_rows = rows  # ordered as displayed (for selection)
        for i, (label, sums) in enumerate(rows):
            num_vals = []
            for c in agg_columns:
                v = sums.get(c, 0)
                num_vals.append(f"{v:.0f}" if isinstance(v, (int, float)) and v == int(v) else str(v))
            table.add_row(label, *num_vals, key=str(i))
        if rows:
            try:
                table.move_cursor(row=0, column=0)
            except Exception:
                pass
        # Update breadcrumb
        bc = self.query_one("#breadcrumb", Static)
        if self.path:
            bc.update(" / ".join(self.path))
        else:
            bc.update("(top level)")

    def _get_selected_dim_value(self) -> str | None:
        table = self.query_one(HDVDataTable)
        if not table.rows:
            return None
        cursor_row = table.cursor_row
        if cursor_row is None or cursor_row < 0:
            return None
        rows = getattr(self, "_current_rows", [])
        if cursor_row >= len(rows):
            return None
        return rows[cursor_row][0]

    def action_sort_toggle(self) -> None:
        """Switch between sorting by dimension column and by numeric column."""
        self.sort_by_numeric = not self.sort_by_numeric
        self._refresh_table()

    def action_back(self) -> None:
        if not self.path:
            return
        self.path.pop()
        self._refresh_table()

    def action_expand(self) -> None:
        level = len(self.path)
        # Can't expand when already at the last dimension (no further levels)
        if level >= len(self.dimension_columns) - 1:
            return
        val = self._get_selected_dim_value()
        if val is None:
            return
        self.path.append(val)
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("(top level)", id="breadcrumb"),
            ScrollableContainer(HDVDataTable(id="table"), id="table-container"),
        )
        yield Footer()
