"""table_helpers.py — Excel-style column filter header + column visibility.

Usage in a page class:
    from pages.table_helpers import install_filter_header, show_col_customize_menu

    class FooPage(QWidget):
        def _build(self):
            self._table = QTableWidget()
            self._filter_hdr = install_filter_header(self._table, self)
            self._table.setColumnCount(len(_COLS))
            self._table.setHorizontalHeaderLabels(_COLS)
            self._filter_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            ...

        def _load_table(self, _=None):
            # populate rows ...
            self._filter_hdr.apply_filters(self)   # re-sort + re-filter + update count

        def _on_customize(self):
            show_col_customize_menu(self, self.sender(), _COLS)
"""
from PyQt6.QtWidgets import (
    QHeaderView, QDialog, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QCheckBox, QScrollArea, QWidget, QMenu
)
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QPolygonF


_BTN_AREA = 22   # px from section right edge that triggers the filter popup


# ── Filter popup ──────────────────────────────────────────────────────────────

class FilterPopup(QDialog):
    """Popup with sort buttons + checkbox value list (Excel-style)."""

    def __init__(self, col, all_values, current_sel, sort_cb, filter_cb, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self._all_set = set(all_values)
        self._sort_cb = sort_cb
        self._filter_cb = filter_cb
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedWidth(230)
        self.setStyleSheet(
            "QDialog { background:white; border:1px solid #DDE3EE; border-radius:6px; }"
            "QPushButton { padding:4px 10px; border-radius:4px; font-size:12px; }"
            "QCheckBox { font-size:12px; padding:2px 4px; }"
        )
        self._build(list(all_values), current_sel)

    def _build(self, values, current_sel):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        # Sort row
        sort_row = QHBoxLayout()
        asc_btn = QPushButton("↑ 升序")
        asc_btn.setStyleSheet(
            "QPushButton{background:#F0F4FF;color:#003087;border:1px solid #DDE3EE;}"
        )
        asc_btn.clicked.connect(lambda: (self._sort_cb(True), self.accept()))
        desc_btn = QPushButton("↓ 降序")
        desc_btn.setStyleSheet(
            "QPushButton{background:#F0F4FF;color:#003087;border:1px solid #DDE3EE;}"
        )
        desc_btn.clicked.connect(lambda: (self._sort_cb(False), self.accept()))
        sort_row.addWidget(asc_btn)
        sort_row.addWidget(desc_btn)
        lay.addLayout(sort_row)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#DDE3EE;")
        lay.addWidget(sep)

        # "全选" checkbox
        self._all_cb = QCheckBox("（全选）")
        all_checked = current_sel == self._all_set or current_sel is None
        self._all_cb.setTristate(False)
        self._all_cb.setChecked(all_checked)
        self._all_cb.stateChanged.connect(self._toggle_all)
        lay.addWidget(self._all_cb)

        # Scrollable value list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        scroll.setMaximumHeight(min(220, 28 * len(values) + 8))
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(2, 2, 2, 2)
        inner_lay.setSpacing(1)

        self._cbs: list[tuple[str, QCheckBox]] = []
        for v in values:
            cb = QCheckBox(v if v else "（空白）")
            checked = (current_sel is None) or (v in current_sel)
            cb.setChecked(checked)
            cb.stateChanged.connect(self._on_value_changed)
            inner_lay.addWidget(cb)
            self._cbs.append((v, cb))
        inner_lay.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#DDE3EE;")
        lay.addWidget(sep2)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(
            "QPushButton{background:#003087;color:white;border:none;font-weight:bold;}"
            "QPushButton:hover{background:#0050B3;}"
        )
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(
            "QPushButton{background:white;color:#333;border:1px solid #DDE3EE;}"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)
        self.adjustSize()

    def _toggle_all(self, state):
        checked = (state == 2)
        for _, cb in self._cbs:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def _on_value_changed(self):
        n_checked = sum(1 for _, cb in self._cbs if cb.isChecked())
        n_total = len(self._cbs)
        self._all_cb.blockSignals(True)
        if n_checked == n_total:
            self._all_cb.setCheckState(Qt.CheckState.Checked)
        elif n_checked == 0:
            self._all_cb.setCheckState(Qt.CheckState.Unchecked)
        else:
            self._all_cb.setTristate(True)
            self._all_cb.setCheckState(Qt.CheckState.PartiallyChecked)
        self._all_cb.blockSignals(False)

    def _on_ok(self):
        selected = {v for v, cb in self._cbs if cb.isChecked()}
        self._filter_cb(selected)
        self.accept()


# ── Filter header ─────────────────────────────────────────────────────────────

class FilterHeader(QHeaderView):
    """Drop-in replacement for QTableWidget's horizontal header.

    Features:
    • ▼ button drawn in each section (blue when filter active)
    • Click ▼ → FilterPopup (sort + multi-select checkboxes)
    • Click section title → toggle sort
    • apply_filters(page) re-applies active sort + filters after table reload
    """

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._col_filters: dict[int, set] = {}   # col → set of allowed strings
        self._sort_col = -1
        self._sort_asc = True
        self._page = None
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setSortIndicatorShown(False)

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()

        is_active = logicalIndex in self._col_filters
        tri_color = QColor("#003087") if is_active else QColor("#AAAAAA")

        aw, ah = 7.0, 4.0
        ax = float(rect.right()) - aw - 5.0
        ay = float(rect.center().y()) - ah / 2.0 + 1.0

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(tri_color))
        poly = QPolygonF([
            QPointF(ax,          ay),
            QPointF(ax + aw,     ay),
            QPointF(ax + aw / 2, ay + ah),
        ])
        painter.drawPolygon(poly)
        painter.restore()

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        col = self.logicalIndexAt(event.pos())
        if col < 0 or self.isSectionHidden(col):
            event.accept()
            return

        sec_pos = self.sectionViewportPosition(col)
        sec_w   = self.sectionSize(col)
        in_btn  = event.pos().x() >= (sec_pos + sec_w - _BTN_AREA)

        if in_btn:
            self._show_filter_popup(col)
        else:
            # Toggle sort
            if self._sort_col == col:
                self._sort_asc = not self._sort_asc
            else:
                self._sort_col = col
                self._sort_asc = True
            self._do_sort()
        event.accept()

    # ── Filter popup ──────────────────────────────────────────────────────────

    def _show_filter_popup(self, col):
        table = self.parent()
        if not table:
            return

        all_vals = sorted({
            (table.item(r, col).text() if table.item(r, col) else "")
            for r in range(table.rowCount())
        })
        all_set = set(all_vals)
        current = self._col_filters.get(col)   # None = all selected

        def _sort_cb(ascending: bool):
            self._sort_col = col
            self._sort_asc = ascending
            self._do_sort()

        def _filter_cb(selected: set):
            if selected >= all_set:              # all selected → clear filter
                self._col_filters.pop(col, None)
            else:
                self._col_filters[col] = selected
            self._apply_internal(table)
            self.viewport().update()

        popup = FilterPopup(col, all_vals, current, _sort_cb, _filter_cb, parent=None)
        sec_pos    = self.sectionViewportPosition(col)
        global_pos = self.mapToGlobal(QPoint(sec_pos, self.height()))
        popup.move(global_pos)
        popup.exec()

    # ── Sort ──────────────────────────────────────────────────────────────────

    def _do_sort(self):
        table = self.parent()
        if not table or self._sort_col < 0:
            return
        order = (Qt.SortOrder.AscendingOrder
                 if self._sort_asc else Qt.SortOrder.DescendingOrder)
        table.sortItems(self._sort_col, order)
        self.setSortIndicatorShown(True)
        self.setSortIndicator(self._sort_col, order)

    # ── Filter application ────────────────────────────────────────────────────

    def _apply_internal(self, table):
        for row in range(table.rowCount()):
            visible = True
            for c, allowed in self._col_filters.items():
                item = table.item(row, c)
                v = item.text() if item else ""
                if v not in allowed:
                    visible = False
                    break
            table.setRowHidden(row, not visible)
        self._update_count(table)

    def _update_count(self, table):
        if self._page and hasattr(self._page, "_count_lbl"):
            n = sum(1 for r in range(table.rowCount()) if not table.isRowHidden(r))
            self._page._count_lbl.setText(f"共 {n} 条")

    def apply_filters(self, page=None):
        """Re-apply sort + col-filters. Call at end of _load_table()."""
        if page is not None:
            self._page = page
        table = self.parent()
        if not table:
            return
        self._do_sort()
        self._apply_internal(table)

    def clear_col_filter(self, col: int):
        self._col_filters.pop(col, None)
        table = self.parent()
        if table:
            self._apply_internal(table)
        self.viewport().update()


# ── Public API ────────────────────────────────────────────────────────────────

def install_filter_header(table, page=None) -> FilterHeader:
    """Install a FilterHeader on table (replaces default header). Returns it."""
    hdr = FilterHeader(Qt.Orientation.Horizontal, table)
    hdr._page = page
    table.setHorizontalHeader(hdr)
    return hdr


def show_col_customize_menu(page, btn, col_names: list) -> None:
    """Show column visibility menu anchored below btn."""
    hdr: FilterHeader | None = getattr(page, "_filter_hdr", None)
    menu = QMenu(page)
    for col, name in enumerate(col_names):
        act = menu.addAction(name)
        act.setCheckable(True)
        act.setChecked(not page._table.isColumnHidden(col))
        act.setData(col)

    def _toggle(action):
        hidden = not action.isChecked()
        page._table.setColumnHidden(action.data(), hidden)
        if hidden and hdr:
            hdr.clear_col_filter(action.data())

    menu.triggered.connect(_toggle)
    menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
