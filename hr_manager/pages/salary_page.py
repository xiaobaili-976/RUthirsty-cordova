"""SalaryPage — salary management with pay band progress bar in cells."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _GREEN, _YELLOW,
    TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)

_COLS = ["工号", "姓名", "生效日期", "基本工资", "绩效工资", "总工资", "薪酬带", "CR", "规划调薪日期"]


def _fmt_money(v) -> str:
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return str(v) if v else "-"


def _band_pct(total, band_min, band_max) -> int:
    """Return salary position in band as integer 0-100."""
    try:
        lo, hi = float(band_min), float(band_max)
        tot = float(total)
        if hi <= lo:
            return 0
        return max(0, min(100, int((tot - lo) / (hi - lo) * 100)))
    except Exception:
        return 0


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
        self._table.setRowHeight(0, 36)
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

    def refresh(self):
        self._load_table()

    def _all_salary_records(self):
        """Retrieve one latest salary record per employee."""
        emp_mgr = self._mgr.get("employee")
        sal_mgr = self._mgr.get("salary")
        if not emp_mgr or not sal_mgr:
            return []
        employees = emp_mgr.list_employees()
        records = []
        for e in employees:
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
            pct = _band_pct(s.total_salary, s.band_min, s.band_max)
            vals = [
                s.employee_id,
                s.employee_name,
                s.effective_date,
                _fmt_money(s.base_salary),
                _fmt_money(s.performance_pay),
                _fmt_money(s.total_salary),
                s.pay_band,
                f"{s.cr:.0%}" if s.cr else "-",
                s.planned_raise_date or "-",
            ]
            self._table.setRowHeight(row, 36)
            for col, val in enumerate(vals):
                if col == 6:
                    # Pay band column: show progress bar widget
                    bar = QProgressBar()
                    bar.setRange(0, 100)
                    bar.setValue(pct)
                    bar.setFormat(f"{s.pay_band}  {pct}%")
                    bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Color by position
                    if pct < 80:
                        bar_color = _GREEN
                    elif pct < 100:
                        bar_color = _YELLOW
                    else:
                        bar_color = _RED
                    bar.setStyleSheet(f"""
                        QProgressBar {{
                            border: 1px solid {_BORDER};
                            border-radius: 4px;
                            background: #f0f0f0;
                            font-size: 11px;
                        }}
                        QProgressBar::chunk {{
                            background: {bar_color};
                            border-radius: 3px;
                        }}
                    """)
                    self._table.setCellWidget(row, col, bar)
                else:
                    item = QTableWidgetItem(val or "")
                    item.setData(Qt.ItemDataRole.UserRole, s.salary_id)
                    self._table.setItem(row, col, item)

        self._count_lbl.setText(f"共 {len(records)} 条")

    def _selected_salary_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        # Try col 0 first; col 6 has widget
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
        salary = None
        if sal_mgr and eid:
            salary = sal_mgr.get_current(eid)
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
