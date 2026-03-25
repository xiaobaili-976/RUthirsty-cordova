"""ContractPage — contract management with renewal countdown and color alerts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _RED_LIGHT, _YELLOW, _GREEN,
    TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)

_COLS = ["工号", "姓名", "合同类型", "入职日期", "工作时长(月)", "合同结束", "续签日期", "续签倒计时", "状态"]

_STATUS_DISPLAY = {
    "active": "在职",
    "expired": "已到期",
    "terminated": "已终止",
}

_STATUS_MAP = {
    0: None,
    1: "active",
    2: "expired",
    3: "terminated",
}


def _months_between(d1: str, d2: str) -> str:
    """Return months between two ISO date strings, or ''."""
    try:
        a = date.fromisoformat(d1)
        b = date.fromisoformat(d2)
        months = (b.year - a.year) * 12 + (b.month - a.month)
        return str(months)
    except Exception:
        return ""


def _days_to(target_date: str) -> int | None:
    """Days from today to target_date. Returns None if blank/invalid."""
    try:
        td = date.fromisoformat(target_date)
        return (td - date.today()).days
    except Exception:
        return None


class ContractPage(QWidget):
    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self.setStyleSheet("background:#F5F7FA;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Title + toolbar
        top = QHBoxLayout()
        title = QLabel("合同管理")
        title.setStyleSheet(f"color:{_BLUE}; font-size:18px; font-weight:bold;")
        top.addWidget(title)
        top.addStretch(1)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索姓名/工号…")
        self._search.setFixedWidth(180)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._load_table)
        top.addWidget(self._search)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["全部状态", "在职", "已到期", "已终止"])
        self._status_filter.setFixedHeight(32)
        self._status_filter.currentIndexChanged.connect(self._load_table)
        top.addWidget(self._status_filter)

        add_btn = QPushButton("+ 新增合同")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._on_add)
        top.addWidget(add_btn)
        lay.addLayout(top)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch(1)
        for color, text in [(_RED_LIGHT, "≤7天到期"), ("#FEF3CD", "≤30天到期")]:
            dot = QLabel("  ")
            dot.setStyleSheet(f"background:{color}; border: 1px solid #ccc; border-radius:3px;")
            dot.setFixedSize(18, 14)
            legend.addWidget(dot)
            legend.addWidget(QLabel(text))
            legend.addSpacing(12)
        lay.addLayout(legend)

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

    def refresh(self):
        self._load_table()

    def _load_table(self, _=None):
        cont_mgr = self._mgr.get("contract")
        if not cont_mgr:
            return
        contracts = cont_mgr.get_all_contracts()

        query = self._search.text().strip().lower()
        status_key = _STATUS_MAP.get(self._status_filter.currentIndex())

        if query:
            contracts = [c for c in contracts
                         if query in c.employee_id.lower() or query in c.employee_name.lower()]
        if status_key:
            contracts = [c for c in contracts if c.status == status_key]

        self._table.setRowCount(len(contracts))
        for row, c in enumerate(contracts):
            days = _days_to(c.renewal_date) if c.renewal_date else None
            duration = _months_between(c.hire_date, date.today().isoformat())
            countdown_text = f"{days} 天" if days is not None else "-"
            status_text = _STATUS_DISPLAY.get(c.status, c.status)

            vals = [
                c.employee_id,
                c.employee_name,
                c.contract_type,
                c.hire_date,
                duration,
                c.end_date,
                c.renewal_date,
                countdown_text,
                status_text,
            ]
            # Row color
            if days is not None and days <= 7:
                bg = QColor(_RED_LIGHT)
            elif days is not None and days <= 30:
                bg = QColor("#FEF3CD")
            else:
                bg = None

            for col, val in enumerate(vals):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.ItemDataRole.UserRole, c.contract_id)
                if bg:
                    item.setBackground(bg)
                self._table.setItem(row, col, item)

        self._count_lbl.setText(f"共 {len(contracts)} 条")

    def _selected_contract_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_double_click(self, index):
        self._on_edit()

    def _on_add(self):
        from dialogs.contract_form import ContractForm
        dlg = ContractForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        cid = self._selected_contract_id()
        if cid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        cont_mgr = self._mgr.get("contract")
        # Find contract by id
        all_contracts = cont_mgr.get_all_contracts() if cont_mgr else []
        contract = next((c for c in all_contracts if c.contract_id == cid), None)
        if not contract:
            return
        from dialogs.contract_form import ContractForm
        dlg = ContractForm(self._mgr, contract=contract, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_delete(self):
        cid = self._selected_contract_id()
        if cid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", "确定删除该合同记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            cont_mgr = self._mgr.get("contract")
            if cont_mgr:
                cont_mgr.delete_contract(cid)
                self._load_table()
