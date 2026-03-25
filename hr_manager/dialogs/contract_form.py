"""ContractForm — add/edit dialog for contracts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QCompleter, QMessageBox,
    QWidget
)
from PyQt6.QtCore import Qt, QDate, QStringListModel
from PyQt6.QtGui import QFont

from styles import _BLUE, _LIGHT, _BORDER, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


def _to_qdate(iso: str) -> QDate:
    try:
        d = date.fromisoformat(iso)
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


class ContractForm(QDialog):
    def __init__(self, managers: dict, contract=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._contract = contract
        self._editing = contract is not None
        self.setWindowTitle("编辑合同" if self._editing else "新增合同")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"background:{_LIGHT};")
        self._build()
        if self._editing:
            self._populate()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr.setFixedHeight(46)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 0, 20, 0)
        ttl = QLabel("编辑合同" if self._editing else "新增合同")
        ttl.setStyleSheet("color:white; font-size:14px; font-weight:bold;")
        hdr_lay.addWidget(ttl)
        root.addWidget(hdr)

        # Content
        content = QWidget()
        content.setStyleSheet("background:white;")
        lay = QFormLayout(content)
        lay.setContentsMargins(24, 16, 24, 12)
        lay.setSpacing(10)
        lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Employee ID with completer
        self._eid_edit = QLineEdit()
        self._eid_edit.setPlaceholderText("输入工号或姓名搜索…")
        emp_mgr = self._mgr.get("employee")
        if emp_mgr:
            emps = emp_mgr.list_employees()
            suggestions = [f"{e.employee_id} {e.name}" for e in emps]
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._eid_edit.setCompleter(completer)
        lay.addRow("员工工号 *", self._eid_edit)

        self._type_cb = QComboBox()
        self._type_cb.addItems(["固定期限", "无固定期限", "实习"])
        lay.addRow("合同类型", self._type_cb)

        self._hire_date = QDateEdit()
        self._hire_date.setCalendarPopup(True)
        self._hire_date.setDate(QDate.currentDate())
        lay.addRow("入职日期", self._hire_date)

        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        lay.addRow("合同开始日期", self._start_date)

        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate().addYears(1))
        lay.addRow("合同结束日期", self._end_date)

        self._renewal_date = QDateEdit()
        self._renewal_date.setCalendarPopup(True)
        self._renewal_date.setDate(QDate.currentDate().addYears(1))
        lay.addRow("续签日期", self._renewal_date)

        self._prob_end = QDateEdit()
        self._prob_end.setCalendarPopup(True)
        self._prob_end.setDate(QDate.currentDate().addMonths(3))
        lay.addRow("试用期结束", self._prob_end)

        self._status_cb = QComboBox()
        self._status_cb.addItems(["active", "expired", "terminated"])
        lay.addRow("状态", self._status_cb)

        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(60)
        lay.addRow("备注", self._notes_edit)

        # Apply style
        for w in content.findChildren((QLineEdit, QTextEdit, QComboBox, QDateEdit)):
            w.setStyleSheet(INPUT_QSS)

        root.addWidget(content)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 8, 24, 16)
        btn_row.addStretch(1)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    def _populate(self):
        c = self._contract
        self._eid_edit.setText(c.employee_id)
        self._eid_edit.setReadOnly(True)
        idx = self._type_cb.findText(c.contract_type)
        if idx >= 0:
            self._type_cb.setCurrentIndex(idx)
        if c.hire_date:
            self._hire_date.setDate(_to_qdate(c.hire_date))
        if c.start_date:
            self._start_date.setDate(_to_qdate(c.start_date))
        if c.end_date:
            self._end_date.setDate(_to_qdate(c.end_date))
        if c.renewal_date:
            self._renewal_date.setDate(_to_qdate(c.renewal_date))
        if c.probation_end:
            self._prob_end.setDate(_to_qdate(c.probation_end))
        idx = self._status_cb.findText(c.status)
        if idx >= 0:
            self._status_cb.setCurrentIndex(idx)
        self._notes_edit.setPlainText(c.notes)

    def _parse_employee_id(self) -> str:
        """Extract pure employee_id from completer text like '001 张三'."""
        text = self._eid_edit.text().strip()
        return text.split()[0] if text else ""

    def _on_save(self):
        cont_mgr = self._mgr.get("contract")
        if not cont_mgr:
            return
        eid = self._parse_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请填写员工工号")
            return

        from db.models import Contract
        c = Contract(
            contract_id=self._contract.contract_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            contract_type=self._type_cb.currentText(),
            hire_date=self._hire_date.date().toString("yyyy-MM-dd"),
            start_date=self._start_date.date().toString("yyyy-MM-dd"),
            end_date=self._end_date.date().toString("yyyy-MM-dd"),
            renewal_date=self._renewal_date.date().toString("yyyy-MM-dd"),
            probation_end=self._prob_end.date().toString("yyyy-MM-dd"),
            status=self._status_cb.currentText(),
            notes=self._notes_edit.toPlainText().strip(),
            created_at="",
        )
        ok = cont_mgr.update_contract(c) if self._editing else cont_mgr.add_contract(c)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
