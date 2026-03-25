"""RightDrawer — animated slide-out employee detail panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QColor

from styles import _BLUE, _LIGHT, _BORDER, _BG, _TEXT, _TEXT_SEC, BTN_PRIMARY, RISK_COLOR


class RightDrawer(QWidget):
    DRAWER_W = 340

    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._current_eid = ""
        self.setFixedWidth(0)
        self.setStyleSheet(f"background:{_BG}; border-left:1px solid {_BORDER};")
        self._build()
        self._anim = QPropertyAnimation(self, b"maximumWidth")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(48)
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(14, 0, 10, 0)

        self._title_lbl = QLabel("人员详情")
        self._title_lbl.setStyleSheet("color:white; font-size:14px; font-weight:bold;")
        hdr_lay.addWidget(self._title_lbl, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            "background:transparent; color:rgba(255,255,255,0.8); border:none; font-size:14px;"
            "QPushButton:hover{color:white;}"
        )
        close_btn.clicked.connect(self.close_drawer)
        hdr_lay.addWidget(close_btn)
        lay.addWidget(hdr)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        content = QWidget()
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(14, 14, 14, 14)
        self._content_lay.setSpacing(10)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

    def open_drawer(self):
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(self.DRAWER_W)
        self._anim.start()

    def close_drawer(self):
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(0)
        self._anim.start()

    def load_employee(self, employee_id: str):
        self._current_eid = employee_id
        self._populate(employee_id)
        self.open_drawer()

    def _populate(self, eid: str):
        # Clear previous content
        while self._content_lay.count():
            item = self._content_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        emp = emp_mgr.get_employee(eid)
        if not emp:
            return

        self._title_lbl.setText(f"{emp.name}  {emp.employee_id}")

        # Basic info card
        self._add_section("基本信息", [
            ("姓名", emp.name),
            ("工号", emp.employee_id),
            ("性别", emp.gender),
            ("年龄", f"{emp.age} 岁" if emp.age else ""),
            ("出生日期", emp.dob),
            ("手机", emp.phone),
            ("邮箱", emp.email),
            ("状态", emp.display_status),
        ])

        # Job info
        depts = {r["dept_id"]: r["dept_name"] for r in emp_mgr.list_departments()}
        groups = {r["group_id"]: r["group_name"] for r in emp_mgr.list_groups()}
        self._add_section("岗位信息", [
            ("部门", depts.get(emp.dept_id, "")),
            ("小组", groups.get(emp.group_id, "")),
            ("职位", emp.job_title),
            ("职级", emp.job_level),
            ("职等", emp.job_grade),
        ])

        # Education
        self._add_section("教育背景", [
            ("学历", emp.education_level),
            ("本科院校", emp.bachelor_school),
            ("本科专业", emp.bachelor_major),
            ("硕士院校", emp.master_school),
            ("硕士专业", emp.master_major),
        ])

        # Performance
        self._add_section("绩效信息", [
            ("最近绩效", emp.perf_latest),
            ("近3年绩效", emp.perf_3y),
            ("近5次绩效", emp.perf_5times),
            ("近5年绩效", emp.perf_5y),
        ])

        # Contract
        cont_mgr = self._mgr.get("contract")
        if cont_mgr:
            c = cont_mgr.get_active_contract(eid)
            if c:
                days = c.days_to_renewal
                days_str = f"{days} 天" if days is not None else ""
                if days is not None and days <= 30:
                    days_str = f"⚠ {days_str}"
                self._add_section("合同信息", [
                    ("合同类型", c.contract_type),
                    ("入职日期", c.hire_date),
                    ("工作时长", f"{c.tenure_months} 个月" if c.tenure_months else ""),
                    ("续签倒计时", days_str),
                ])

        # Stability
        stab_mgr = self._mgr.get("stability")
        if stab_mgr:
            s = stab_mgr.get_latest(eid)
            if s:
                color = RISK_COLOR.get(s.risk_level, "#888")
                badge = QLabel(f"  稳定性: {s.risk_level_display}  ")
                badge.setStyleSheet(
                    f"background:{color}; color:white; border-radius:10px;"
                    f"font-size:12px; font-weight:bold; padding:3px 8px;"
                )
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._content_lay.addWidget(badge)

        self._content_lay.addStretch(1)

    def _add_section(self, title: str, fields: list):
        frame = QFrame()
        frame.setStyleSheet(
            f"background:{_LIGHT}; border:1px solid {_BORDER}; border-radius:6px;"
        )
        flay = QVBoxLayout(frame)
        flay.setContentsMargins(10, 8, 10, 8)
        flay.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color:{_BLUE}; font-weight:bold; font-size:12px; border:none;"
        )
        flay.addWidget(title_lbl)

        for key, val in fields:
            if not val:
                continue
            row = QHBoxLayout()
            row.setSpacing(6)
            k_lbl = QLabel(f"{key}:")
            k_lbl.setStyleSheet(f"color:{_TEXT_SEC}; font-size:11px; border:none;")
            k_lbl.setFixedWidth(70)
            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet(f"color:{_TEXT}; font-size:12px; border:none;")
            v_lbl.setWordWrap(True)
            row.addWidget(k_lbl)
            row.addWidget(v_lbl, 1)
            flay.addLayout(row)

        self._content_lay.addWidget(frame)
