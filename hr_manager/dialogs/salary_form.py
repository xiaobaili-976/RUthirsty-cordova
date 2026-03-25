"""SalaryForm — add/edit dialog for salary records."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit, QCompleter,
    QMessageBox, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QDate

from styles import _BLUE, _LIGHT, _BORDER, _TEXT_SEC, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{_BLUE}; font-size:12px; font-weight:bold; "
        f"border-bottom:1px solid {_BORDER}; padding-bottom:3px; margin-top:6px;"
    )
    return lbl


_MONTHS = ["01", "02", "03", "04", "05", "06",
           "07", "08", "09", "10", "11", "12"]


class SalaryForm(QDialog):
    def __init__(self, managers: dict, salary=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._salary = salary
        self._editing = salary is not None
        self.setWindowTitle("编辑薪酬记录" if self._editing else "新增薪酬记录")
        self.setMinimumWidth(560)
        self.setMinimumHeight(560)
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
        ttl = QLabel("编辑薪酬记录" if self._editing else "新增薪酬记录")
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

        def _make_form():
            fl = QFormLayout()
            fl.setSpacing(10)
            fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            fl.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
            return fl

        form = _make_form()

        # Employee ID
        self._eid_edit = QLineEdit()
        self._eid_edit.setPlaceholderText("输入工号或姓名…")
        emp_mgr = self._mgr.get("employee")
        if emp_mgr:
            emps = emp_mgr.list_employees()
            suggestions = [f"{e.employee_id} {e.name}" for e in emps]
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._eid_edit.setCompleter(completer)
        form.addRow("员工工号 *", self._eid_edit)
        lay.addLayout(form)

        lay.addWidget(_section_label("薪资构成"))
        salary_form = _make_form()

        self._base_spin = QDoubleSpinBox()
        self._base_spin.setRange(0, 9_999_999)
        self._base_spin.setDecimals(2)
        self._base_spin.setSingleStep(100)
        self._base_spin.valueChanged.connect(self._update_totals)
        salary_form.addRow("基本工资", self._base_spin)

        self._perf_spin = QDoubleSpinBox()
        self._perf_spin.setRange(0, 9_999_999)
        self._perf_spin.setDecimals(2)
        self._perf_spin.setSingleStep(100)
        self._perf_spin.valueChanged.connect(self._update_totals)
        salary_form.addRow("绩效工资", self._perf_spin)

        total_row = QHBoxLayout()
        self._total_lbl = QLabel("0.00")
        self._total_lbl.setStyleSheet(
            f"color:{_BLUE}; font-size:16px; font-weight:bold; padding:4px 8px;"
            f"background:#E8F0FE; border-radius:4px;"
        )
        total_row.addWidget(self._total_lbl)
        total_row.addStretch(1)
        salary_form.addRow("总工资（自动）", total_row)

        lay.addLayout(salary_form)
        lay.addWidget(_section_label("薪酬带范围"))
        band_form = _make_form()

        self._band_min = QDoubleSpinBox()
        self._band_min.setRange(0, 9_999_999)
        self._band_min.setDecimals(0)
        band_form.addRow("Band 最低", self._band_min)

        self._band_mid = QDoubleSpinBox()
        self._band_mid.setRange(0, 9_999_999)
        self._band_mid.setDecimals(0)
        self._band_mid.valueChanged.connect(self._update_totals)
        band_form.addRow("Band 中位", self._band_mid)

        self._band_max = QDoubleSpinBox()
        self._band_max.setRange(0, 9_999_999)
        self._band_max.setDecimals(0)
        band_form.addRow("Band 最高", self._band_max)

        cr_row = QHBoxLayout()
        self._cr_lbl = QLabel("-")
        self._cr_lbl.setStyleSheet(
            f"color:{_BLUE}; font-weight:bold; padding:4px 8px; "
            f"background:#E8F0FE; border-radius:4px;"
        )
        cr_row.addWidget(self._cr_lbl)
        cr_row.addStretch(1)
        band_form.addRow("CR（自动）", cr_row)

        lay.addLayout(band_form)
        lay.addWidget(_section_label("调薪计划"))
        raise_form = _make_form()

        self._raise_src = QLineEdit()
        raise_form.addRow("调薪来源", self._raise_src)

        # Year + month planned date
        ym_row = QHBoxLayout()
        self._planned_year = QSpinBox()
        self._planned_year.setRange(2020, 2050)
        self._planned_year.setValue(date.today().year + 1)
        ym_row.addWidget(self._planned_year)
        ym_row.addWidget(QLabel("年"))
        self._planned_month = QComboBox()
        self._planned_month.addItems(_MONTHS)
        self._planned_month.setCurrentIndex(0)
        ym_row.addWidget(self._planned_month)
        ym_row.addWidget(QLabel("月"))
        ym_row.addStretch(1)
        raise_form.addRow("规划调薪日期", ym_row)

        self._planned_amt = QDoubleSpinBox()
        self._planned_amt.setRange(-9_999_999, 9_999_999)
        self._planned_amt.setDecimals(0)
        raise_form.addRow("规划调薪金额", self._planned_amt)

        self._bonus_spin = QDoubleSpinBox()
        self._bonus_spin.setRange(0, 9_999_999)
        self._bonus_spin.setDecimals(2)
        raise_form.addRow("上年度奖金", self._bonus_spin)

        lay.addLayout(raise_form)

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

    def _update_totals(self):
        total = self._base_spin.value() + self._perf_spin.value()
        self._total_lbl.setText(f"{total:,.2f}")
        band_mid = self._band_mid.value()
        if band_mid > 0:
            cr = total / band_mid
            self._cr_lbl.setText(f"{cr:.0%}")
        else:
            self._cr_lbl.setText("-")

    def _populate(self):
        s = self._salary
        self._eid_edit.setText(s.employee_id)
        self._eid_edit.setReadOnly(True)
        self._base_spin.setValue(s.base_salary)
        self._perf_spin.setValue(s.performance_pay)
        self._band_min.setValue(float(s.band_min) if s.band_min else 0)
        self._band_mid.setValue(float(s.band_mid) if s.band_mid else 0)
        self._band_max.setValue(float(s.band_max) if s.band_max else 0)
        self._update_totals()
        self._raise_src.setText(s.raise_source)
        # Parse planned_raise_date "YYYY-MM-DD" into year + month
        if s.planned_raise_date and len(s.planned_raise_date) >= 7:
            try:
                parts = s.planned_raise_date.split("-")
                self._planned_year.setValue(int(parts[0]))
                self._planned_month.setCurrentIndex(int(parts[1]) - 1)
            except Exception:
                pass
        self._planned_amt.setValue(float(s.planned_raise_amount) if s.planned_raise_amount else 0)
        self._bonus_spin.setValue(float(s.bonus_last) if s.bonus_last else 0)

    def _parse_employee_id(self) -> str:
        text = self._eid_edit.text().strip()
        return text.split()[0] if text else ""

    def _on_save(self):
        sal_mgr = self._mgr.get("salary")
        if not sal_mgr:
            return
        eid = self._parse_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请填写员工工号")
            return

        total = self._base_spin.value() + self._perf_spin.value()
        band_mid = self._band_mid.value()
        cr = total / band_mid if band_mid > 0 else 0.0
        planned_date = (
            f"{self._planned_year.value():04d}-"
            f"{self._planned_month.currentText()}-01"
        )

        from db.models import Salary
        s = Salary(
            salary_id=self._salary.salary_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            effective_date=date.today().isoformat(),
            base_salary=self._base_spin.value(),
            performance_pay=self._perf_spin.value(),
            total_salary=total,
            cr=cr,
            pay_band="",
            band_min=self._band_min.value(),
            band_mid=band_mid,
            band_max=self._band_max.value(),
            bonus_last=self._bonus_spin.value(),
            raise_source=self._raise_src.text().strip(),
            raise_reason="",
            planned_raise_date=planned_date,
            planned_raise_amount=self._planned_amt.value(),
            approved_by="",
            created_at="",
        )
        ok = sal_mgr.update_record(s) if self._editing else sal_mgr.add_record(s)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
