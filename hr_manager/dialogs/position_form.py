"""PositionForm — add/edit dialog for position/job-level records."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCompleter, QDateEdit, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QDate

from styles import _BLUE, _LIGHT, _BORDER, _TEXT_SEC, BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS


class PositionForm(QDialog):
    def __init__(self, managers: dict, position=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._position = position
        self._editing = position is not None
        self.setWindowTitle("编辑职级记录" if self._editing else "新增职级记录")
        self.setMinimumWidth(500)
        self.setMinimumHeight(420)
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
        lay.setSpacing(12)
        lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        lay.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._eid_edit = QLineEdit()
        self._eid_edit.setPlaceholderText("输入工号或姓名搜索…")
        emp_mgr = self._mgr.get("employee")
        if emp_mgr:
            emps = emp_mgr.list_employees()
            suggestions = [f"{e.employee_id} {e.name}" for e in emps]
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._eid_edit.setCompleter(completer)
        self._eid_edit.textChanged.connect(self._on_eid_changed)
        lay.addRow("员工工号 *", self._eid_edit)

        self._level_edit = QLineEdit()
        self._level_edit.setPlaceholderText("如: P6")
        lay.addRow("职级", self._level_edit)

        self._grade_edit = QLineEdit()
        self._grade_edit.setPlaceholderText("如: 高级工程师")
        lay.addRow("职等", self._grade_edit)

        self._adj_cb = QComboBox()
        self._adj_cb.addItems(["调级", "调等"])
        lay.addRow("调整类型", self._adj_cb)

        # Last adjustment lookup (auto-populated from DB, user-adjustable)
        self._last_adj_date = QDateEdit()
        self._last_adj_date.setCalendarPopup(True)
        self._last_adj_date.setDate(QDate.currentDate())
        self._last_adj_date.dateChanged.connect(self._update_interval)
        lay.addRow("最近一次调整日期", self._last_adj_date)

        self._interval_lbl = QLabel("-")
        self._interval_lbl.setStyleSheet(
            f"color:{_TEXT_SEC}; padding:4px 8px; background:#f7f8fa; "
            f"border:1px solid {_BORDER}; border-radius:4px;"
        )
        lay.addRow("距离上次调整间隔", self._interval_lbl)

        self._situation_edit = QLineEdit()
        self._situation_edit.setPlaceholderText("描述本次调整情况…")
        lay.addRow("调整情况", self._situation_edit)

        # Apply style
        for w in content.findChildren((QLineEdit, QComboBox)):
            w.setStyleSheet(INPUT_QSS)

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

    def _on_eid_changed(self, text: str):
        eid = text.split()[0] if text.strip() else ""
        self._lookup_last_adjustment(eid)

    def _lookup_last_adjustment(self, eid: str):
        pos_mgr = self._mgr.get("position")
        if not pos_mgr or not eid:
            self._last_adj_date.blockSignals(True)
            self._last_adj_date.setDate(QDate.currentDate())
            self._last_adj_date.blockSignals(False)
            self._interval_lbl.setText("-")
            return
        history = pos_mgr.get_history(eid)
        # Exclude the current record when editing
        if self._editing and self._position:
            history = [p for p in history if p.position_id != self._position.position_id]
        if not history:
            self._last_adj_date.blockSignals(True)
            self._last_adj_date.setDate(QDate.currentDate())
            self._last_adj_date.blockSignals(False)
            self._interval_lbl.setText("-")
            return
        history.sort(key=lambda p: p.effective_date or "", reverse=True)
        latest = history[0]
        last_date = latest.effective_date or ""
        try:
            d = date.fromisoformat(last_date)
            self._last_adj_date.setDate(QDate(d.year, d.month, d.day))
        except Exception:
            self._last_adj_date.setDate(QDate.currentDate())
        self._update_interval()

    def _update_interval(self):
        qd = self._last_adj_date.date()
        try:
            last = date(qd.year(), qd.month(), qd.day())
            today = date.today()
            months = (today.year - last.year) * 12 + (today.month - last.month)
            self._interval_lbl.setText(f"{months} 个月")
        except Exception:
            self._interval_lbl.setText("-")

    def _populate(self):
        p = self._position
        self._eid_edit.setText(p.employee_id)
        self._eid_edit.setReadOnly(True)
        self._level_edit.setText(p.level)
        self._grade_edit.setText(p.grade)
        idx = self._adj_cb.findText(p.adjustment_type)
        if idx >= 0:
            self._adj_cb.setCurrentIndex(idx)
        self._situation_edit.setText(p.reason or "")
        self._lookup_last_adjustment(p.employee_id)

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
            effective_date=date.today().isoformat(),
            level=self._level_edit.text().strip(),
            grade=self._grade_edit.text().strip(),
            adjustment_type=self._adj_cb.currentText(),
            reason=self._situation_edit.text().strip(),
            approved_by="",
            planned_date="",
            planned_type="",
            planned_source="",
            created_at="",
        )
        ok = pos_mgr.update_record(p) if self._editing else pos_mgr.add_record(p)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
