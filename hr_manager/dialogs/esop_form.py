"""EsopForm — add/edit dialog for ESOP records."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit, QCompleter,
    QMessageBox, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QDate

from styles import _BLUE, _LIGHT, _BORDER, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


def _to_qdate(iso: str) -> QDate:
    from datetime import date
    try:
        d = date.fromisoformat(iso)
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{_BLUE}; font-size:12px; font-weight:bold; "
        f"border-bottom:1px solid {_BORDER}; padding-bottom:3px; margin-top:6px;"
    )
    return lbl


class EsopForm(QDialog):
    def __init__(self, managers: dict, esop=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._esop = esop
        self._editing = esop is not None
        self.setWindowTitle("编辑ESOP记录" if self._editing else "新增ESOP记录")
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
        lay.setSpacing(6)

        # Base form
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

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

        self._grant_date = QDateEdit()
        self._grant_date.setCalendarPopup(True)
        self._grant_date.setDate(QDate.currentDate())
        form.addRow("授予日期", self._grant_date)

        lay.addLayout(form)
        lay.addWidget(_section_label("份额信息"))

        shares_form = QFormLayout()
        shares_form.setSpacing(8)
        shares_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._granted_spin = QDoubleSpinBox()
        self._granted_spin.setRange(0, 999_999_999)
        self._granted_spin.setDecimals(0)
        self._granted_spin.setSingleStep(1000)
        self._granted_spin.valueChanged.connect(self._update_unvested)
        shares_form.addRow("授予份额", self._granted_spin)

        self._vested_spin = QDoubleSpinBox()
        self._vested_spin.setRange(0, 999_999_999)
        self._vested_spin.setDecimals(0)
        self._vested_spin.setSingleStep(1000)
        self._vested_spin.valueChanged.connect(self._update_unvested)
        shares_form.addRow("已归属", self._vested_spin)

        unvested_row = QHBoxLayout()
        self._unvested_lbl = QLabel("0")
        self._unvested_lbl.setStyleSheet(
            f"color:{_BLUE}; font-weight:bold; padding:3px 8px; "
            f"background:#E8F0FE; border-radius:4px;"
        )
        unvested_row.addWidget(self._unvested_lbl)
        unvested_row.addStretch(1)
        shares_form.addRow("未归属（自动）", unvested_row)

        lay.addLayout(shares_form)
        lay.addWidget(_section_label("指导线 & 人才"))

        guide_form = QFormLayout()
        guide_form.setSpacing(8)
        guide_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._annual_guide = QDoubleSpinBox()
        self._annual_guide.setRange(0, 999_999_999)
        self._annual_guide.setDecimals(0)
        guide_form.addRow("年度指导线", self._annual_guide)

        self._upper_spin = QDoubleSpinBox()
        self._upper_spin.setRange(0, 999_999_999)
        self._upper_spin.setDecimals(0)
        guide_form.addRow("授予上限", self._upper_spin)

        self._lower_spin = QDoubleSpinBox()
        self._lower_spin.setRange(0, 999_999_999)
        self._lower_spin.setDecimals(0)
        guide_form.addRow("授予下限", self._lower_spin)

        self._talent_edit = QLineEdit()
        self._talent_edit.setPlaceholderText("如: A级/B+级")
        guide_form.addRow("人才识别结果", self._talent_edit)

        self._plan_edit = QLineEdit()
        self._plan_edit.setPlaceholderText("如: 2023 期权计划")
        guide_form.addRow("计划名称", self._plan_edit)

        lay.addLayout(guide_form)
        lay.addWidget(_section_label("备注"))

        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(60)
        lay.addWidget(self._notes_edit)

        # Apply style
        for w in content.findChildren((QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox)):
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

    def _update_unvested(self):
        unvested = max(0.0, self._granted_spin.value() - self._vested_spin.value())
        self._unvested_lbl.setText(f"{unvested:,.0f}")

    def _populate(self):
        s = self._esop
        self._eid_edit.setText(s.employee_id)
        self._eid_edit.setReadOnly(True)
        if s.grant_date:
            self._grant_date.setDate(_to_qdate(s.grant_date))
        self._granted_spin.setValue(float(s.shares_granted) if s.shares_granted else 0)
        self._vested_spin.setValue(float(s.shares_vested) if s.shares_vested else 0)
        self._update_unvested()
        self._annual_guide.setValue(float(s.annual_guideline) if s.annual_guideline else 0)
        self._upper_spin.setValue(float(s.grant_upper) if s.grant_upper else 0)
        self._lower_spin.setValue(float(s.grant_lower) if s.grant_lower else 0)
        self._talent_edit.setText(s.talent_result)
        self._plan_edit.setText(s.plan_name)
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
        vested = self._vested_spin.value()
        unvested = max(0.0, granted - vested)

        from db.models import Esop
        s = Esop(
            esop_id=self._esop.esop_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            grant_date=self._grant_date.date().toString("yyyy-MM-dd"),
            shares_granted=granted,
            shares_vested=vested,
            shares_unvested=unvested,
            annual_guideline=self._annual_guide.value(),
            grant_upper=self._upper_spin.value(),
            grant_lower=self._lower_spin.value(),
            talent_result=self._talent_edit.text().strip(),
            vest_schedule="[]",
            plan_name=self._plan_edit.text().strip(),
            notes=self._notes_edit.toPlainText().strip(),
            created_at="",
        )
        ok = esop_mgr.update_record(s) if self._editing else esop_mgr.add_record(s)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
