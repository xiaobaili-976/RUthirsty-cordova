"""EsopPage — ESOP / long-term incentive management."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _GREEN, _YELLOW,
    TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)
from pages.table_helpers import init_col_filter, apply_col_filters, show_col_customize_menu

_COLS = ["工号", "姓名", "授予年份", "授予份额", "上年度授予份额", "饱和度", "年度指导线", "人才识别"]


def _saturation_color(pct: float) -> str:
    if pct >= 80:
        return _GREEN
    elif pct >= 60:
        return _YELLOW
    return _RED


class EsopPage(QWidget):
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
        title = QLabel("ESOP 长期激励")
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
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
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

        init_col_filter(self)

    def refresh(self):
        self._load_table()

    def _all_esop_records(self):
        emp_mgr = self._mgr.get("employee")
        esop_mgr = self._mgr.get("esop")
        if not emp_mgr or not esop_mgr:
            return []
        records = []
        for e in emp_mgr.list_employees():
            latest = esop_mgr.get_current(e.employee_id)
            if latest:
                records.append(latest)
        return records

    def _load_table(self, _=None):
        records = self._all_esop_records()
        query = self._search.text().strip().lower()
        if query:
            records = [r for r in records
                       if query in r.employee_id.lower() or query in r.employee_name.lower()]

        self._table.setRowCount(len(records))
        for row, s in enumerate(records):
            try:
                sat_pct = float(getattr(s, "saturation", 0) or 0) * 100
            except Exception:
                sat_pct = 0.0
            color = _saturation_color(sat_pct)
            sat_text = f"{sat_pct:.1f}%"
            # Extract year from grant_date (YYYY-01-01 → YYYY)
            grant_year = (s.grant_date or "")[:4]
            # shares_vested is repurposed as 上年度授予份额
            prev_granted = f"{s.shares_vested:,.0f}" if s.shares_vested else "-"

            vals = [
                s.employee_id,
                s.employee_name,
                grant_year,
                f"{s.shares_granted:,.0f}",
                prev_granted,
                sat_text,
                f"{s.annual_guideline:,.0f}" if s.annual_guideline else "-",
                s.talent_result or "-",
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.ItemDataRole.UserRole, s.esop_id)
                if col == 5:  # saturation column
                    item.setForeground(QColor(color))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                self._table.setItem(row, col, item)

        apply_col_filters(self)

    def _on_customize(self):
        show_col_customize_menu(self, self.sender(), _COLS)

    def _selected_esop_id(self):
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
        from dialogs.esop_form import EsopForm
        dlg = EsopForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        sid = self._selected_esop_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        eid = self._selected_employee_id()
        esop_mgr = self._mgr.get("esop")
        esop = esop_mgr.get_current(eid) if esop_mgr and eid else None
        if not esop:
            return
        from dialogs.esop_form import EsopForm
        dlg = EsopForm(self._mgr, esop=esop, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_delete(self):
        sid = self._selected_esop_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", "确定删除该ESOP记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            esop_mgr = self._mgr.get("esop")
            if esop_mgr:
                esop_mgr.delete_record(sid)
                self._load_table()
