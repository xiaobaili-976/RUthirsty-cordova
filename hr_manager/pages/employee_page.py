"""EmployeePage — employee list with add/edit/delete and search."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from styles import _BLUE, _LIGHT, _BORDER, _RED, TABLE_QSS, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER, EMP_TYPE_BORDER


_COLS = ["工号", "姓名", "性别", "年龄", "员工类型", "部门", "小组", "职位", "职级", "状态"]


class EmployeePage(QWidget):
    employee_selected = pyqtSignal(str)

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
        title = QLabel("基础信息管理")
        title.setStyleSheet("color:#003087; font-size:18px; font-weight:bold;")
        top.addWidget(title)
        top.addStretch(1)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索姓名/工号/职位…")
        self._search.setFixedWidth(200)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._on_search)
        top.addWidget(self._search)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["全部状态", "在职", "试用期", "已离职"])
        self._status_filter.setFixedHeight(32)
        self._status_filter.currentIndexChanged.connect(self._load_table)
        top.addWidget(self._status_filter)

        add_btn = QPushButton("+ 新增人员")
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

        # Bottom action bar
        bot = QHBoxLayout()
        self._count_lbl = QLabel("共 0 条")
        self._count_lbl.setStyleSheet("color:#888; font-size:12px;")
        bot.addWidget(self._count_lbl)
        bot.addStretch(1)

        view_btn = QPushButton("查看详情")
        view_btn.setStyleSheet(BTN_SECONDARY)
        view_btn.setFixedHeight(30)
        view_btn.clicked.connect(self._on_view)
        bot.addWidget(view_btn)

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

    def _get_status_filter(self) -> str | None:
        idx = self._status_filter.currentIndex()
        return {0: None, 1: "active", 2: "probation", 3: "resigned"}.get(idx)

    def _load_table(self, _=None):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        query = self._search.text().strip()
        status = self._get_status_filter()
        if query:
            emps = emp_mgr.search(query)
            if status:
                emps = [e for e in emps if e.status == status]
        else:
            emps = emp_mgr.list_employees(status=status)

        depts  = {r["dept_id"]: r["dept_name"] for r in emp_mgr.list_departments()}
        groups = {r["group_id"]: r["group_name"] for r in emp_mgr.list_groups()}

        self._table.setRowCount(len(emps))
        for row, e in enumerate(emps):
            vals = [
                e.employee_id, e.name, e.gender,
                str(e.age) if e.age else "",
                e.employee_type or "",
                depts.get(e.dept_id, ""),
                groups.get(e.group_id, ""),
                e.job_title, e.job_level, e.display_status,
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, e.employee_id)
                if e.status == "resigned":
                    item.setForeground(QColor("#aaa"))
                elif e.status == "probation":
                    item.setForeground(QColor("#E67E22"))
                # Color employee_type column
                elif col == 4 and val:
                    item.setForeground(QColor(EMP_TYPE_BORDER.get(val, "#AAB4C8")))
                self._table.setItem(row, col, item)

        self._count_lbl.setText(f"共 {len(emps)} 条")

    def _on_search(self, _):
        self._load_table()

    def _selected_employee_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_view(self):
        eid = self._selected_employee_id()
        if eid:
            self.employee_selected.emit(eid)

    def _on_double_click(self, index):
        eid = self._table.item(index.row(), 0)
        if eid:
            self.employee_selected.emit(eid.data(Qt.ItemDataRole.UserRole))

    def _on_add(self):
        from dialogs.employee_form import EmployeeForm
        dlg = EmployeeForm(self._mgr, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_edit(self):
        eid = self._selected_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        from dialogs.employee_form import EmployeeForm
        emp = self._mgr["employee"].get_employee(eid)
        dlg = EmployeeForm(self._mgr, employee=emp, parent=self)
        if dlg.exec():
            self._load_table()

    def _on_delete(self):
        eid = self._selected_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        if QMessageBox.question(
            self, "确认删除", f"确定删除工号 {eid} 的人员及其所有相关数据？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._mgr["employee"].delete_employee(eid)
            self._load_table()
