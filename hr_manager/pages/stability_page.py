"""StabilityPage — stability barometer with risk badge, filter, and actions."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _RED_LIGHT, _GREEN,
    _YELLOW, TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER,
    RISK_COLOR, RISK_BG
)
from pages.table_helpers import init_col_filter, apply_col_filters, show_col_customize_menu

_COLS = ["工号", "姓名", "评估日期", "家庭分", "职业分", "工作分", "综合评分", "风险等级", "风险标签"]

_RISK_LABEL = {
    "green":  "稳定",
    "yellow": "需关注",
    "red":    "高风险",
}
_RISK_FILTER = {
    0: None,
    1: "red",
    2: "yellow",
    3: "green",
}


class StabilityPage(QWidget):
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
        title = QLabel("稳定性晴雨表")
        title.setStyleSheet(f"color:{_BLUE}; font-size:18px; font-weight:bold;")
        top.addWidget(title)
        top.addStretch(1)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索姓名/工号…")
        self._search.setFixedWidth(180)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._load_table)
        top.addWidget(self._search)

        self._risk_filter = QComboBox()
        self._risk_filter.addItems(["全部风险", "高风险", "需关注", "稳定"])
        self._risk_filter.setFixedHeight(32)
        self._risk_filter.currentIndexChanged.connect(self._load_table)
        top.addWidget(self._risk_filter)

        customize_btn = QPushButton("表头定制")
        customize_btn.setStyleSheet(BTN_SECONDARY)
        customize_btn.setFixedHeight(32)
        customize_btn.clicked.connect(self._on_customize)
        top.addWidget(customize_btn)

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

        init_col_filter(self)

        # Bottom bar
        bot = QHBoxLayout()
        self._count_lbl = QLabel("共 0 条")
        self._count_lbl.setStyleSheet("color:#888; font-size:12px;")
        bot.addWidget(self._count_lbl)
        bot.addStretch(1)

        add_btn = QPushButton("+ 新增评估")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.setFixedHeight(30)
        add_btn.clicked.connect(self._on_add)
        bot.addWidget(add_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(BTN_SECONDARY)
        edit_btn.setFixedHeight(30)
        edit_btn.clicked.connect(self._on_edit)
        bot.addWidget(edit_btn)

        comm_btn = QPushButton("查看沟通记录")
        comm_btn.setStyleSheet(BTN_SECONDARY)
        comm_btn.setFixedHeight(30)
        comm_btn.clicked.connect(self._on_view_comm)
        bot.addWidget(comm_btn)

        del_btn = QPushButton("删除")
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.setFixedHeight(30)
        del_btn.clicked.connect(self._on_delete)
        bot.addWidget(del_btn)
        lay.addLayout(bot)

    def refresh(self):
        self._load_table()

    def _all_stability_records(self):
        emp_mgr = self._mgr.get("employee")
        stab_mgr = self._mgr.get("stability")
        if not emp_mgr or not stab_mgr:
            return []
        employees = emp_mgr.list_employees()
        records = []
        for e in employees:
            latest = stab_mgr.get_latest(e.employee_id)
            if latest:
                records.append(latest)
        return records

    def _load_table(self, _=None):
        records = self._all_stability_records()
        query = self._search.text().strip().lower()
        risk_key = _RISK_FILTER.get(self._risk_filter.currentIndex())

        if query:
            records = [r for r in records
                       if query in r.employee_id.lower() or query in r.employee_name.lower()]
        if risk_key:
            records = [r for r in records if r.risk_level == risk_key]

        self._table.setRowCount(len(records))
        for row, s in enumerate(records):
            risk_lbl = _RISK_LABEL.get(s.risk_level, s.risk_level)
            risk_color = RISK_COLOR.get(s.risk_level, "#333")
            risk_bg = RISK_BG.get(s.risk_level, "#fff")

            vals = [
                s.employee_id,
                s.employee_name,
                s.assessment_date,
                f"{s.family_score:.1f}",
                f"{s.career_score:.1f}",
                f"{s.work_score:.1f}",
                f"{s.overall_score:.1f}",
                risk_lbl,
                s.risk_tags or "-",
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.ItemDataRole.UserRole, s.stability_id)
                if col == 7:  # risk level badge column
                    item.setForeground(QColor(risk_color))
                    item.setBackground(QColor(risk_bg))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)

        self._count_lbl.setText(f"共 {len(records)} 条")
        apply_col_filters(self)

    def _on_customize(self):
        show_col_customize_menu(self, self.sender(), _COLS)

    def _selected_stability_id(self) -> int | None:
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
        from dialogs.stability_form import StabilityForm
        dlg = StabilityForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        sid = self._selected_stability_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        eid = self._selected_employee_id()
        stab_mgr = self._mgr.get("stability")
        stab = None
        if stab_mgr and eid:
            stab = stab_mgr.get_latest(eid)
        if not stab:
            return
        from dialogs.stability_form import StabilityForm
        dlg = StabilityForm(self._mgr, assessment=stab, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_view_comm(self):
        sid = self._selected_stability_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        eid = self._selected_employee_id()
        stab_mgr = self._mgr.get("stability")
        stab = None
        if stab_mgr and eid:
            stab = stab_mgr.get_latest(eid)
        if not stab:
            return
        from dialogs.stability_form import StabilityForm
        dlg = StabilityForm(self._mgr, assessment=stab, open_comm_tab=True, parent=self)
        dlg.exec()

    def _on_delete(self):
        sid = self._selected_stability_id()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", "确定删除该稳定性评估记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            # stability_manager has no delete_assessment — use raw db if available
            stab_mgr = self._mgr.get("stability")
            if stab_mgr and hasattr(stab_mgr, "_db"):
                stab_mgr._db.execute(
                    "DELETE FROM stability WHERE stability_id=?", (sid,)
                )
            self._load_table()
