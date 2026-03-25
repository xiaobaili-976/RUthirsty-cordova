"""PositionForm — add/edit dialog for position/job-level records."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QCompleter, QMessageBox, QWidget
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


class PositionForm(QDialog):
    def __init__(self, managers: dict, position=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._position = position
        self._editing = position is not None
        self.setWindowTitle("编辑职级记录" if self._editing else "新增职级记录")
        self.setMinimumWidth(500)
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
        ttl = QLabel("编辑职级记录" if self._editing else "新增职级记录")
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

        self._eff_date = QDateEdit()
        self._eff_date.setCalendarPopup(True)
        self._eff_date.setDate(QDate.currentDate())
        lay.addRow("生效日期", self._eff_date)

        self._level_edit = QLineEdit()
        self._level_edit.setPlaceholderText("如: P6")
        lay.addRow("职级", self._level_edit)

        self._grade_edit = QLineEdit()
        self._grade_edit.setPlaceholderText("如: 高级工程师")
        lay.addRow("职等", self._grade_edit)

        self._adj_cb = QComboBox()
        self._adj_cb.addItems(["晋升", "降级", "平调", "入职"])
        lay.addRow("调整类型", self._adj_cb)

        self._reason_edit = QLineEdit()
        lay.addRow("调整原因", self._reason_edit)

        self._approved_by = QLineEdit()
        lay.addRow("审批人", self._approved_by)

        # Planned section
        sep = QLabel("── 规划信息 ──")
        sep.setStyleSheet(f"color:{_BLUE}; font-size:11px; margin-top:4px;")
        lay.addRow(sep)

        self._planned_date = QDateEdit()
        self._planned_date.setCalendarPopup(True)
        self._planned_date.setDate(QDate.currentDate().addYears(1))
        lay.addRow("规划调整日期", self._planned_date)

        self._planned_type = QLineEdit()
        self._planned_type.setPlaceholderText("如: 晋升")
        lay.addRow("规划调整类型", self._planned_type)

        self._planned_src = QLineEdit()
        self._planned_src.setPlaceholderText("调整来源/依据")
        lay.addRow("规划来源", self._planned_src)

        # Apply style
        for w in content.findChildren((QLineEdit, QComboBox, QDateEdit)):
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
        p = self._position
        self._eid_edit.setText(p.employee_id)
        self._eid_edit.setReadOnly(True)
        if p.effective_date:
            self._eff_date.setDate(_to_qdate(p.effective_date))
        self._level_edit.setText(p.level)
        self._grade_edit.setText(p.grade)
        idx = self._adj_cb.findText(p.adjustment_type)
        if idx >= 0:
            self._adj_cb.setCurrentIndex(idx)
        self._reason_edit.setText(p.reason)
        self._approved_by.setText(p.approved_by)
        if p.planned_date:
            self._planned_date.setDate(_to_qdate(p.planned_date))
        self._planned_type.setText(p.planned_type)
        self._planned_src.setText(p.planned_source)

    def _parse_employee_id(self) -> str:
        text = self._eid_edit.text().strip()
        return text.split()[0] if text else ""

    def _on_save(self):
        pos_mgr = self._mgr.get("position")
        if not pos_mgr:
            return
        eid = self._parse_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请填写员工工号")
            return

        from db.models import Position
        p = Position(
            position_id=self._position.position_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            effective_date=self._eff_date.date().toString("yyyy-MM-dd"),
            level=self._level_edit.text().strip(),
            grade=self._grade_edit.text().strip(),
            adjustment_type=self._adj_cb.currentText(),
            reason=self._reason_edit.text().strip(),
            approved_by=self._approved_by.text().strip(),
            planned_date=self._planned_date.date().toString("yyyy-MM-dd"),
            planned_type=self._planned_type.text().strip(),
            planned_source=self._planned_src.text().strip(),
            created_at="",
        )
        ok = pos_mgr.update_record(p) if self._editing else pos_mgr.add_record(p)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
