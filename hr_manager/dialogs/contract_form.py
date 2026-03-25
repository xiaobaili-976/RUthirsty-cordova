"""ContractForm — add/edit dialog for contracts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QDateEdit, QTextEdit, QCompleter, QMessageBox,
    QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from styles import _BLUE, _LIGHT, _BORDER, _TEXT_SEC, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


def _to_qdate(iso: str) -> QDate:
    try:
        d = date.fromisoformat(iso)
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


def _calc_renewal_info(hire_date_str: str):
    """Return (renewal_count, renewal_date_iso) based on 4-year cycle."""
    try:
        hire = date.fromisoformat(hire_date_str)
        today = date.today()
        years = (today - hire).days / 365.25
        count = int(years / 4)
        renewal_year = hire.year + (count + 1) * 4
        renewal = date(renewal_year, hire.month, hire.day)
        return count, renewal.isoformat()
    except Exception:
        return 0, ""


class ContractForm(QDialog):
    def __init__(self, managers: dict, contract=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._contract = contract
        self._editing = contract is not None
        self.setWindowTitle("编辑合同" if self._editing else "新增合同")
        self.setMinimumWidth(480)
        self.setMinimumHeight(340)
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
        lay.setSpacing(12)
        lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        lay.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

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

        self._hire_date = QDateEdit()
        self._hire_date.setCalendarPopup(True)
        self._hire_date.setDate(QDate.currentDate())
        self._hire_date.dateChanged.connect(self._update_renewal_info)
        lay.addRow("入职日期", self._hire_date)

        # Auto-calculated read-only fields
        self._renewal_date_lbl = QLabel("-")
        self._renewal_date_lbl.setStyleSheet(
            f"color:{_BLUE}; font-weight:bold; padding:4px 8px; "
            f"background:#E8F0FE; border-radius:4px;"
        )
        lay.addRow("续签日期（自动）", self._renewal_date_lbl)

        self._renewal_count_lbl = QLabel("0")
        self._renewal_count_lbl.setStyleSheet(
            f"color:{_BLUE}; font-weight:bold; padding:4px 8px; "
            f"background:#E8F0FE; border-radius:4px;"
        )
        lay.addRow("合同次数（自动）", self._renewal_count_lbl)

        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(60)
        lay.addRow("备注", self._notes_edit)

        # Apply style
        for w in content.findChildren((QLineEdit, QDateEdit)):
            w.setStyleSheet(INPUT_QSS)
        self._notes_edit.setStyleSheet(INPUT_QSS)

        root.addWidget(content)
        root.addStretch(1)

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

        # Initialise labels
        self._update_renewal_info()

    def _update_renewal_info(self):
        hire_date = self._hire_date.date().toString("yyyy-MM-dd")
        count, renewal_date = _calc_renewal_info(hire_date)
        self._renewal_date_lbl.setText(renewal_date or "-")
        self._renewal_count_lbl.setText(str(count))

    def _populate(self):
        c = self._contract
        self._eid_edit.setText(c.employee_id)
        self._eid_edit.setReadOnly(True)
        if c.hire_date:
            self._hire_date.setDate(_to_qdate(c.hire_date))
        self._update_renewal_info()
        self._notes_edit.setPlainText(c.notes)

    def _parse_employee_id(self) -> str:
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

        hire_date = self._hire_date.date().toString("yyyy-MM-dd")
        _, renewal_date = _calc_renewal_info(hire_date)

        from db.models import Contract
        c = Contract(
            contract_id=self._contract.contract_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            contract_type="固定期限",
            hire_date=hire_date,
            start_date=hire_date,
            end_date="",
            renewal_date=renewal_date,
            probation_end="",
            status="active",
            notes=self._notes_edit.toPlainText().strip(),
            created_at="",
        )
        ok = cont_mgr.update_contract(c) if self._editing else cont_mgr.add_contract(c)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
