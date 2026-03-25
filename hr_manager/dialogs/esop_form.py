"""EsopForm — add/edit dialog for ESOP records."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit, QCompleter,
    QMessageBox, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt

from styles import _BLUE, _LIGHT, _BORDER, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


class EsopForm(QDialog):
    def __init__(self, managers: dict, esop=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._esop = esop
        self._editing = esop is not None
        self.setWindowTitle("编辑ESOP记录" if self._editing else "新增ESOP记录")
        self.setMinimumWidth(500)
        self.setMinimumHeight(480)
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
        ttl = QLabel("编辑ESOP记录" if self._editing else "新增ESOP记录")
        ttl.setStyleSheet("color:white; font-size:14px; font-weight:bold;")
        hdr_lay.addWidget(ttl)
        root.addWidget(hdr)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        content.setStyleSheet("background:white;")
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Employee ID
        self._eid_edit = QLineEdit()
        self._eid_edit.setPlaceholderText("输入工号或姓名搜索…")
        emp_mgr = self._mgr.get("employee")
        if emp_mgr:
            emps = emp_mgr.list_employees()
            suggestions = [f"{e.employee_id} {e.name}" for e in emps]
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._eid_edit.setCompleter(completer)
        form.addRow("员工工号 *", self._eid_edit)

        # Grant year (year-only spinner)
        self._grant_year = QSpinBox()
        self._grant_year.setRange(2000, 2050)
        self._grant_year.setValue(date.today().year)
        form.addRow("授予年份", self._grant_year)

        # Shares
        self._granted_spin = QDoubleSpinBox()
        self._granted_spin.setRange(0, 999_999_999)
        self._granted_spin.setDecimals(0)
        self._granted_spin.setSingleStep(1000)
        form.addRow("授予份额", self._granted_spin)

        # 上年度授予份额 (stored in shares_vested)
        self._prev_granted_spin = QDoubleSpinBox()
        self._prev_granted_spin.setRange(0, 999_999_999)
        self._prev_granted_spin.setDecimals(0)
        self._prev_granted_spin.setSingleStep(1000)
        form.addRow("上年度授予份额", self._prev_granted_spin)

        # Guideline fields
        self._annual_guide = QDoubleSpinBox()
        self._annual_guide.setRange(0, 999_999_999)
        self._annual_guide.setDecimals(0)
        form.addRow("年度指导线", self._annual_guide)

        self._upper_spin = QDoubleSpinBox()
        self._upper_spin.setRange(0, 999_999_999)
        self._upper_spin.setDecimals(0)
        form.addRow("授予上限", self._upper_spin)

        self._lower_spin = QDoubleSpinBox()
        self._lower_spin.setRange(0, 999_999_999)
        self._lower_spin.setDecimals(0)
        form.addRow("授予下限", self._lower_spin)

        self._talent_edit = QLineEdit()
        self._talent_edit.setPlaceholderText("如: A级/B+级")
        form.addRow("人才识别结果", self._talent_edit)

        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(60)
        form.addRow("备注", self._notes_edit)

        lay.addLayout(form)

        # Apply style
        for w in content.findChildren((QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox)):
            w.setStyleSheet(INPUT_QSS)

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
        s = self._esop
        self._eid_edit.setText(s.employee_id)
        self._eid_edit.setReadOnly(True)
        if s.grant_date and len(s.grant_date) >= 4:
            try:
                self._grant_year.setValue(int(s.grant_date[:4]))
            except Exception:
                pass
        self._granted_spin.setValue(float(s.shares_granted) if s.shares_granted else 0)
        self._prev_granted_spin.setValue(float(s.shares_vested) if s.shares_vested else 0)
        self._annual_guide.setValue(float(s.annual_guideline) if s.annual_guideline else 0)
        self._upper_spin.setValue(float(s.grant_upper) if s.grant_upper else 0)
        self._lower_spin.setValue(float(s.grant_lower) if s.grant_lower else 0)
        self._talent_edit.setText(s.talent_result)
        self._notes_edit.setPlainText(s.notes)

    def _parse_employee_id(self) -> str:
        text = self._eid_edit.text().strip()
        return text.split()[0] if text else ""

    def _on_save(self):
        esop_mgr = self._mgr.get("esop")
        if not esop_mgr:
            return
        eid = self._parse_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请填写员工工号")
            return

        granted = self._granted_spin.value()
        prev_granted = self._prev_granted_spin.value()
        grant_date = f"{self._grant_year.value():04d}-01-01"

        from db.models import Esop
        s = Esop(
            esop_id=self._esop.esop_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            grant_date=grant_date,
            shares_granted=granted,
            shares_vested=prev_granted,      # repurposed as 上年度授予份额
            shares_unvested=0,
            annual_guideline=self._annual_guide.value(),
            grant_upper=self._upper_spin.value(),
            grant_lower=self._lower_spin.value(),
            talent_result=self._talent_edit.text().strip(),
            vest_schedule="[]",
            plan_name="",
            notes=self._notes_edit.toPlainText().strip(),
            created_at="",
        )
        ok = esop_mgr.update_record(s) if self._editing else esop_mgr.add_record(s)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
