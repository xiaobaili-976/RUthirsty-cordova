"""DashboardPage — home control panel with key metrics and alerts."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from styles import _BLUE, _LIGHT, _BORDER, _RED, _GREEN, _YELLOW, _BG, BTN_PRIMARY


class _MetricCard(QFrame):
    def __init__(self, title: str, value: str = "0", color: str = "#003087"):
        super().__init__()
        self.setStyleSheet(
            f"background:white; border:1px solid #DDE3EE; border-radius:10px;"
        )
        self.setMinimumSize(160, 100)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)

        self._val_lbl = QLabel(value)
        self._val_lbl.setStyleSheet(
            f"color:{color}; font-size:32px; font-weight:bold; border:none;"
        )
        lay.addWidget(self._val_lbl)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color:#888; font-size:12px; border:none;")
        lay.addWidget(t_lbl)

    def set_value(self, v: str):
        self._val_lbl.setText(v)


class DashboardPage(QWidget):
    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self.setStyleSheet(f"background:#F5F7FA;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # Title
        title = QLabel("控制台")
        title.setStyleSheet(
            f"color:#003087; font-size:20px; font-weight:bold;"
        )
        lay.addWidget(title)

        # Metric cards row
        cards_row = QHBoxLayout()
        self._card_total    = _MetricCard("在职人员总数", "—", "#003087")
        self._card_risk     = _MetricCard("高风险人员", "—", "#C0392B")
        self._card_contract = _MetricCard("合同30天内到期", "—", "#E67E22")
        self._card_depts    = _MetricCard("部门数量", "—", "#27AE60")
        for c in (self._card_total, self._card_risk,
                  self._card_contract, self._card_depts):
            cards_row.addWidget(c)
        lay.addLayout(cards_row)

        # Bottom two-column layout
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # High-risk list
        risk_frame = self._make_list_section(
            "⚠ 高风险人员清单", "_risk_list"
        )
        bottom_row.addWidget(risk_frame, 1)

        # Contract expiry list
        cont_frame = self._make_list_section(
            "📋 合同到期预警 (30天)", "_contract_list"
        )
        bottom_row.addWidget(cont_frame, 1)

        # Upcoming tasks
        task_frame = self._make_list_section(
            "📌 待跟进事项", "_task_list"
        )
        bottom_row.addWidget(task_frame, 1)

        lay.addLayout(bottom_row, 1)

    def _make_list_section(self, title: str, attr: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "background:white; border:1px solid #DDE3EE; border-radius:10px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)

        t = QLabel(title)
        t.setStyleSheet("color:#003087; font-weight:bold; font-size:13px; border:none;")
        lay.addWidget(t)

        lst = QListWidget()
        lst.setStyleSheet(
            "border:none; font-size:12px;"
            "QListWidget::item{padding:5px 0;}"
        )
        setattr(self, attr, lst)
        lay.addWidget(lst, 1)
        return frame

    def refresh(self):
        emp_mgr   = self._mgr.get("employee")
        stab_mgr  = self._mgr.get("stability")
        cont_mgr  = self._mgr.get("contract")

        total = emp_mgr.count() if emp_mgr else 0
        risk_items = stab_mgr.get_high_risk_employees() if stab_mgr else []
        expiring   = cont_mgr.get_expiring_soon(30) if cont_mgr else []

        depts = len(emp_mgr.list_departments()) if emp_mgr else 0

        self._card_total.set_value(str(total))
        self._card_risk.set_value(str(len(risk_items)))
        self._card_contract.set_value(str(len(expiring)))
        self._card_depts.set_value(str(depts))

        # High-risk list
        self._risk_list.clear()
        for item in risk_items:
            li = QListWidgetItem(f"🔴 {item['name']}  ({item['employee_id']})")
            li.setForeground(QColor("#C0392B"))
            self._risk_list.addItem(li)

        # Contract list
        self._contract_list.clear()
        for item in expiring:
            d = item["days_left"]
            icon = "🔴" if d <= 7 else "🟡"
            li = QListWidgetItem(f"{icon} {item['name']} — 剩余 {d} 天")
            self._contract_list.addItem(li)

        # Task list (planned raises, position adjustments)
        self._task_list.clear()
        sal_mgr = self._mgr.get("salary")
        if sal_mgr and emp_mgr:
            for emp in emp_mgr.list_employees():
                s = sal_mgr.get_current(emp.employee_id)
                if s and s.planned_raise_date:
                    from db.models import _days_until
                    d = _days_until(s.planned_raise_date)
                    if d is not None and 0 <= d <= 60:
                        li = QListWidgetItem(
                            f"💰 {emp.name} — 规划调薪 ({d}天后)"
                        )
                        self._task_list.addItem(li)
