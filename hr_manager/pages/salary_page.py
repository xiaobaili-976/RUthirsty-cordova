"""SalaryPage — salary management."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _GREEN, _YELLOW,
    TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)
from pages.table_helpers import init_col_filter, apply_col_filters, show_col_customize_menu

_COLS = ["工号", "姓名", "基本工资", "绩效工资", "总工资", "CR", "规划调薪"]


def _fmt_money(v) -> str:
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return str(v) if v else "-"


class SalaryPage(QWidget):
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
        title = QLabel("薪酬管理")
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

    def _all_salary_records(self):
        emp_mgr = self._mgr.get("employee")
        sal_mgr = self._mgr.get("salary")
        if not emp_mgr or not sal_mgr:
            return []
        records = []
        for e in emp_mgr.list_employees():
            s = sal_mgr.get_current(e.employee_id)
            if s:
                records.append(s)
        return records

    def _load_table(self, _=None):
        records = self._all_salary_records()
        query = self._search.text().strip().lower()
        if query:
            records = [r for r in records
                       if query in r.employee_id.lower() or query in r.employee_name.lower()]

        self._table.setRowCount(len(records))
        for row, s in enumerate(records):
            cr_text = f"{s.cr:.0%}" if s.cr else "-"
            vals = [
                s.employee_id,
                s.employee_name,
                _fmt_money(s.base_salary),
                _fmt_money(s.performance_pay),
                _fmt_money(s.total_salary),
                cr_text,
                s.planned_raise_date or "-",
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.ItemDataRole.UserRole, s.salary_id)
                self._table.setItem(row, col, item)

        apply_col_filters(self)

    def _on_customize(self):
        show_col_customize_menu(self, self.sender(), _COLS)

    def _selected_salary_id(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        for col in range(len(_COLS)):
            item = self._table.item(row, col)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _selected_employee_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.text() if item else None

    def _on_double_click(self, index):
        self._on_edit()

    def _on_add(self):
        from dialogs.salary_form import SalaryForm
        dlg = SalaryForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        sid = self._selected_salary_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        eid = self._selected_employee_id()
        sal_mgr = self._mgr.get("salary")
        salary = sal_mgr.get_current(eid) if sal_mgr and eid else None
        if not salary:
            return
        from dialogs.salary_form import SalaryForm
        dlg = SalaryForm(self._mgr, salary=salary, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_delete(self):
        sid = self._selected_salary_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", "确定删除该薪酬记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            sal_mgr = self._mgr.get("salary")
            if sal_mgr:
                sal_mgr.delete_record(sid)
                self._load_table()
