"""PositionPage — position / job-level management."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _GREEN, _TEXT_SEC,
    TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)
from pages.table_helpers import install_filter_header, show_col_customize_menu

_COLS = ["工号", "姓名", "职级", "职等", "调整类型", "调整间隔(月)", "调整情况"]

_ADJ_COLORS = {
    "调级": _GREEN,
    "调等": _BLUE,
}


def _months_interval(prev_date: str, cur_date: str) -> str:
    try:
        a = date.fromisoformat(prev_date)
        b = date.fromisoformat(cur_date)
        return str((b.year - a.year) * 12 + (b.month - a.month))
    except Exception:
        return "-"


class PositionPage(QWidget):
    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self.setStyleSheet("background:#F5F7FA;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Toolbar
        top = QHBoxLayout()
        title = QLabel("人岗管理")
        title.setStyleSheet(f"color:{_BLUE}; font-size:18px; font-weight:bold;")
        top.addWidget(title)
        top.addStretch(1)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索姓名/工号…")
        self._search.setFixedWidth(180)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._load_table)
        top.addWidget(self._search)

        customize_btn = QPushButton("表头定制")
        customize_btn.setStyleSheet(BTN_SECONDARY)
        customize_btn.setFixedHeight(32)
        customize_btn.clicked.connect(self._on_customize)
        top.addWidget(customize_btn)

        add_btn = QPushButton("+ 新增记录")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._on_add)
        top.addWidget(add_btn)
        lay.addLayout(top)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        self._table.setStyleSheet(TABLE_QSS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().hide()
        self._filter_hdr = install_filter_header(self._table, self)
        self._filter_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._filter_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.doubleClicked.connect(self._on_double_click)
        lay.addWidget(self._table, 1)

        # Bottom bar
        bot = QHBoxLayout()
        self._count_lbl = QLabel("共 0 条")
        self._count_lbl.setStyleSheet("color:#888; font-size:12px;")
        bot.addWidget(self._count_lbl)
        bot.addStretch(1)

        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(BTN_SECONDARY)
        edit_btn.setFixedHeight(30)
        edit_btn.clicked.connect(self._on_edit)
        bot.addWidget(edit_btn)

        del_btn = QPushButton("删除")
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.setFixedHeight(30)
        del_btn.clicked.connect(self._on_delete)
        bot.addWidget(del_btn)
        lay.addLayout(bot)

    def refresh(self):
        self._load_table()

    def _all_position_records(self):
        emp_mgr = self._mgr.get("employee")
        pos_mgr = self._mgr.get("position")
        if not emp_mgr or not pos_mgr:
            return []
        records = []
        for e in emp_mgr.list_employees():
            records.extend(pos_mgr.get_history(e.employee_id))
        return records

    def _load_table(self, _=None):
        records = self._all_position_records()
        query = self._search.text().strip().lower()
        if query:
            records = [r for r in records
                       if query in r.employee_id.lower() or query in r.employee_name.lower()]

        # Sort by employee then date descending
        records.sort(key=lambda r: (r.employee_id, r.effective_date or ""), reverse=True)

        # Compute intervals per employee
        prev_dates = {}
        intervals = {}
        for r in sorted(records, key=lambda r: (r.employee_id, r.effective_date or "")):
            pid = r.employee_id
            if pid in prev_dates:
                intervals[r.position_id] = _months_interval(prev_dates[pid], r.effective_date or "")
            else:
                intervals[r.position_id] = "-"
            prev_dates[pid] = r.effective_date or ""

        self._table.setRowCount(len(records))
        for row, p in enumerate(records):
            adj_color = _ADJ_COLORS.get(p.adjustment_type, "#333")
            vals = [
                p.employee_id,
                p.employee_name,
                p.level,
                p.grade,
                p.adjustment_type,
                intervals.get(p.position_id, "-"),
                p.reason or "",
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.ItemDataRole.UserRole, p.position_id)
                if col == 4:  # adjustment_type column
                    item.setForeground(QColor(adj_color))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                self._table.setItem(row, col, item)

        self._filter_hdr.apply_filters(self)

    def _on_customize(self):
        show_col_customize_menu(self, self.sender(), _COLS)

    def _selected_position_id(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_employee_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.text() if item else None

    def _on_double_click(self, index):
        self._on_edit()

    def _on_add(self):
        from dialogs.position_form import PositionForm
        dlg = PositionForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        pid = self._selected_position_id()
        if pid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        eid = self._selected_employee_id()
        pos_mgr = self._mgr.get("position")
        position = None
        if pos_mgr and eid:
            history = pos_mgr.get_history(eid)
            position = next((p for p in history if p.position_id == pid), None)
        if not position:
            return
        from dialogs.position_form import PositionForm
        dlg = PositionForm(self._mgr, position=position, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_delete(self):
        pid = self._selected_position_id()
        if pid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", "确定删除该职级记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            pos_mgr = self._mgr.get("position")
            if pos_mgr:
                pos_mgr.delete_record(pid)
                self._load_table()
