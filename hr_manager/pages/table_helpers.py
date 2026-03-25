"""table_helpers.py — reusable column-filter and column-customize helpers.

Usage in a page class:
    from pages.table_helpers import init_col_filter, apply_col_filters, show_col_customize_menu

    class FooPage(QWidget):
        def _build(self):
            ...create self._table...
            init_col_filter(self)          # call once

        def _load_table(self, _=None):
            ...populate self._table...
            apply_col_filters(self)        # call at end (also updates _count_lbl)

        def _on_customize(self):
            show_col_customize_menu(self, self.sender(), _COLS)
"""
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QCursor


def init_col_filter(page) -> None:
    """Initialise column-filter state and wire header click."""
    page._col_filters = {}          # col_index -> value_str
    page._table.horizontalHeader().sectionClicked.connect(
        lambda col: _on_col_header_clicked(page, col)
    )


def _on_col_header_clicked(page, col: int) -> None:
    t = page._table
    if t.isColumnHidden(col):
        return
    # Collect unique values from all (non-hidden) rows
    values = sorted({
        t.item(row, col).text()
        for row in range(t.rowCount())
        if t.item(row, col) is not None
    })
    menu = QMenu(page)
    act_all = menu.addAction("全部（取消筛选）")
    act_all.setData(None)
    if values:
        menu.addSeparator()
    for v in values:
        act = menu.addAction(v)
        act.setData(v)
        act.setCheckable(True)
        act.setChecked(page._col_filters.get(col) == v)
    chosen = menu.exec(QCursor.pos())
    if chosen is None:
        return
    val = chosen.data()
    if val is None:
        page._col_filters.pop(col, None)
    else:
        page._col_filters[col] = val
    apply_col_filters(page)


def _row_matches(t, row: int, filters: dict) -> bool:
    for col, val in filters.items():
        item = t.item(row, col)
        if item is None or item.text() != val:
            return False
    return True


def apply_col_filters(page) -> None:
    """Hide rows that don't match active column filters. Updates _count_lbl."""
    t = page._table
    ncols = t.columnCount()
    # Update column header indicator (▼ mark)
    for col in range(ncols):
        h = t.horizontalHeaderItem(col)
        if h is None:
            continue
        text = h.text()
        want = col in page._col_filters
        has = text.endswith(" ▼")
        if want and not has:
            h.setText(text + " ▼")
        elif not want and has:
            h.setText(text[:-2])
    # Show/hide rows
    for row in range(t.rowCount()):
        t.setRowHidden(row, not _row_matches(t, row, page._col_filters))
    # Update count label
    if hasattr(page, "_count_lbl"):
        visible = sum(1 for row in range(t.rowCount()) if not t.isRowHidden(row))
        page._count_lbl.setText(f"共 {visible} 条")


def show_col_customize_menu(page, btn, col_names: list) -> None:
    """Show column visibility menu anchored below btn."""
    menu = QMenu(page)
    for col, name in enumerate(col_names):
        act = menu.addAction(name)
        act.setCheckable(True)
        act.setChecked(not page._table.isColumnHidden(col))
        act.setData(col)

    def _toggle(action):
        page._table.setColumnHidden(action.data(), not action.isChecked())
        # Clear filter for any now-hidden column
        if not action.isChecked() and action.data() in page._col_filters:
            del page._col_filters[action.data()]
            apply_col_filters(page)

    menu.triggered.connect(_toggle)
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
