"""EmployeeForm — add/edit dialog for employees."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QScrollArea, QWidget,
    QGroupBox, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _TEXT_SEC,
    BTN_PRIMARY, BTN_SECONDARY, INPUT_QSS
)


def _to_qdate(iso: str) -> QDate:
    try:
        d = date.fromisoformat(iso)
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{_BLUE}; font-size:13px; font-weight:bold; "
        f"border-bottom:1px solid {_BORDER}; padding-bottom:4px; margin-top:8px;"
    )
    return lbl


class EmployeeForm(QDialog):
    def __init__(self, managers: dict, employee=None, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._employee = employee
        self._editing = employee is not None
        self.setWindowTitle("编辑人员" if self._editing else "新增人员")
        self.setMinimumWidth(720)
        self.setMinimumHeight(680)
        self.setStyleSheet(f"background:{_LIGHT};")
        self._build()
        if self._editing:
            self._populate()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr.setFixedHeight(48)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 0, 20, 0)
        ttl = QLabel("编辑人员" if self._editing else "新增人员")
        ttl.setStyleSheet("color:white; font-size:15px; font-weight:bold;")
        hdr_lay.addWidget(ttl)
        root.addWidget(hdr)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        content.setStyleSheet("background:white;")
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(8)

        # ── 基本信息 ──
        lay.addWidget(_section_label("基本信息"))
        basic_grid = QHBoxLayout()

        left_form = QFormLayout()
        left_form.setSpacing(8)
        left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._id_edit = QLineEdit()
        self._id_edit.setReadOnly(self._editing)
        if self._editing:
            self._id_edit.setStyleSheet("background:#f0f0f0; border:1px solid #ddd; border-radius:4px; padding:5px;")
        left_form.addRow("工号 *", self._id_edit)

        self._name_edit = QLineEdit()
        left_form.addRow("姓名 *", self._name_edit)

        self._gender_cb = QComboBox()
        self._gender_cb.addItems(["男", "女"])
        left_form.addRow("性别", self._gender_cb)

        dob_row = QHBoxLayout()
        self._dob_edit = QDateEdit()
        self._dob_edit.setCalendarPopup(True)
        self._dob_edit.setDate(QDate(1990, 1, 1))
        self._dob_edit.dateChanged.connect(self._update_age)
        dob_row.addWidget(self._dob_edit)
        self._age_lbl = QLabel("年龄: -")
        self._age_lbl.setStyleSheet(f"color:{_TEXT_SEC}; font-size:12px; margin-left:6px;")
        dob_row.addWidget(self._age_lbl)
        dob_row.addStretch(1)
        left_form.addRow("出生日期", dob_row)

        right_form = QFormLayout()
        right_form.setSpacing(8)
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._phone_edit = QLineEdit()
        right_form.addRow("手机", self._phone_edit)

        self._email_edit = QLineEdit()
        right_form.addRow("邮箱", self._email_edit)

        self._status_cb = QComboBox()
        self._status_cb.addItems(["在职", "试用期", "已离职"])
        right_form.addRow("状态", self._status_cb)

        self._type_cb = QComboBox()
        self._type_cb.addItems(["", "华为", "OD", "外包"])
        right_form.addRow("员工类型 *", self._type_cb)

        basic_grid.addLayout(left_form)
        basic_grid.addSpacing(20)
        basic_grid.addLayout(right_form)
        lay.addLayout(basic_grid)

        # ── 岗位信息 ──
        lay.addWidget(_section_label("岗位信息"))
        pos_grid = QHBoxLayout()

        pos_left = QFormLayout()
        pos_left.setSpacing(8)
        pos_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._dept_cb = QComboBox()
        self._dept_cb.currentIndexChanged.connect(self._on_dept_changed)
        pos_left.addRow("部门", self._dept_cb)

        self._group_cb = QComboBox()
        pos_left.addRow("小组", self._group_cb)

        self._title_edit = QLineEdit()
        pos_left.addRow("职位", self._title_edit)

        pos_right = QFormLayout()
        pos_right.setSpacing(8)
        pos_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._level_edit = QLineEdit()
        pos_right.addRow("职级", self._level_edit)

        self._grade_edit = QLineEdit()
        pos_right.addRow("职等", self._grade_edit)

        self._qual_edit = QLineEdit()
        pos_right.addRow("资质", self._qual_edit)

        pos_grid.addLayout(pos_left)
        pos_grid.addSpacing(20)
        pos_grid.addLayout(pos_right)
        lay.addLayout(pos_grid)

        # ── 教育背景 ──
        lay.addWidget(_section_label("教育背景"))
        edu_grid = QHBoxLayout()

        edu_left = QFormLayout()
        edu_left.setSpacing(8)
        edu_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._edu_cb = QComboBox()
        self._edu_cb.addItems(["本科", "硕士", "博士", "其他"])
        edu_left.addRow("最高学历", self._edu_cb)

        self._bsch_edit = QLineEdit()
        edu_left.addRow("本科院校", self._bsch_edit)

        self._bmaj_edit = QLineEdit()
        edu_left.addRow("本科专业", self._bmaj_edit)

        self._byr_edit = QLineEdit()
        self._byr_edit.setPlaceholderText("如: 2015")
        edu_left.addRow("本科毕业年", self._byr_edit)

        edu_right = QFormLayout()
        edu_right.setSpacing(8)
        edu_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._msch_edit = QLineEdit()
        edu_right.addRow("研究生院校", self._msch_edit)

        self._mmaj_edit = QLineEdit()
        edu_right.addRow("研究生专业", self._mmaj_edit)

        self._myr_edit = QLineEdit()
        self._myr_edit.setPlaceholderText("如: 2018")
        edu_right.addRow("研究生毕业年", self._myr_edit)

        edu_grid.addLayout(edu_left)
        edu_grid.addSpacing(20)
        edu_grid.addLayout(edu_right)
        lay.addLayout(edu_grid)

        # ── 绩效信息 ──
        lay.addWidget(_section_label("绩效信息"))
        perf_grid = QHBoxLayout()

        perf_left = QFormLayout()
        perf_left.setSpacing(8)
        perf_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._perf_latest = QLineEdit()
        perf_left.addRow("最近绩效", self._perf_latest)

        self._perf_3y = QLineEdit()
        perf_left.addRow("近3年绩效", self._perf_3y)

        perf_right = QFormLayout()
        perf_right.setSpacing(8)
        perf_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._perf_5t = QLineEdit()
        perf_right.addRow("连续5次绩效", self._perf_5t)

        self._perf_5y = QLineEdit()
        perf_right.addRow("近5年绩效", self._perf_5y)

        perf_grid.addLayout(perf_left)
        perf_grid.addSpacing(20)
        perf_grid.addLayout(perf_right)
        lay.addLayout(perf_grid)

        # ── 备注 ──
        lay.addWidget(_section_label("备注"))
        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(70)
        lay.addWidget(self._notes_edit)

        # Apply input style
        for w in content.findChildren((QLineEdit, QTextEdit, QComboBox, QDateEdit)):
            if not (w is self._id_edit and self._editing):
                w.setStyleSheet(INPUT_QSS)

        # Buttons footer
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

        # Populate dept combo
        self._load_depts()

    def _load_depts(self):
        emp_mgr = self._mgr.get("employee")
        self._dept_cb.clear()
        self._dept_cb.addItem("-- 未分配 --", None)
        if emp_mgr:
            for d in emp_mgr.list_departments():
                self._dept_cb.addItem(d["dept_name"], d["dept_id"])

    def _on_dept_changed(self, _=None):
        emp_mgr = self._mgr.get("employee")
        self._group_cb.clear()
        self._group_cb.addItem("-- 未分配 --", None)
        if not emp_mgr:
            return
        dept_id = self._dept_cb.currentData()
        if dept_id is None:
            return
        for g in emp_mgr.list_groups(dept_id=dept_id):
            self._group_cb.addItem(g["group_name"], g["group_id"])

    def _update_age(self):
        d = self._dob_edit.date()
        today = date.today()
        age = today.year - d.year() - ((today.month, today.day) < (d.month(), d.day()))
        self._age_lbl.setText(f"年龄: {age}")

    def _populate(self):
        e = self._employee
        self._id_edit.setText(e.employee_id)
        self._name_edit.setText(e.name)
        idx = self._gender_cb.findText(e.gender)
        if idx >= 0:
            self._gender_cb.setCurrentIndex(idx)
        if e.dob:
            self._dob_edit.setDate(_to_qdate(e.dob))
        self._update_age()
        self._phone_edit.setText(e.phone)
        self._email_edit.setText(e.email)

        _status_map_rev = {"active": "在职", "probation": "试用期", "resigned": "已离职"}
        st = _status_map_rev.get(e.status, "在职")
        idx = self._status_cb.findText(st)
        if idx >= 0:
            self._status_cb.setCurrentIndex(idx)

        # Employee type
        etype = getattr(e, "employee_type", "") or ""
        idx = self._type_cb.findText(etype)
        if idx >= 0:
            self._type_cb.setCurrentIndex(idx)

        # Dept / group
        for i in range(self._dept_cb.count()):
            if self._dept_cb.itemData(i) == e.dept_id:
                self._dept_cb.setCurrentIndex(i)
                break
        self._on_dept_changed()
        for i in range(self._group_cb.count()):
            if self._group_cb.itemData(i) == e.group_id:
                self._group_cb.setCurrentIndex(i)
                break

        self._title_edit.setText(e.job_title)
        self._level_edit.setText(e.job_level)
        self._grade_edit.setText(e.job_grade)
        self._qual_edit.setText(e.qualification)

        idx = self._edu_cb.findText(e.education_level)
        if idx >= 0:
            self._edu_cb.setCurrentIndex(idx)
        self._bsch_edit.setText(e.bachelor_school)
        self._bmaj_edit.setText(e.bachelor_major)
        self._byr_edit.setText(e.bachelor_grad_year)
        self._msch_edit.setText(e.master_school)
        self._mmaj_edit.setText(e.master_major)
        self._myr_edit.setText(e.master_grad_year)

        self._perf_latest.setText(e.perf_latest)
        self._perf_3y.setText(e.perf_3y)
        self._perf_5t.setText(e.perf_5times)
        self._perf_5y.setText(e.perf_5y)
        self._notes_edit.setPlainText(e.notes)

    def _on_save(self):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return

        eid = self._id_edit.text().strip()
        name = self._name_edit.text().strip()
        if not eid or not name:
            QMessageBox.warning(self, "提示", "工号和姓名为必填项")
            return

        _status_map = {"在职": "active", "试用期": "probation", "已离职": "resigned"}

        from db.models import Employee
        emp = Employee(
            employee_id=eid,
            name=name,
            gender=self._gender_cb.currentText(),
            dob=self._dob_edit.date().toString("yyyy-MM-dd"),
            id_number="",
            phone=self._phone_edit.text().strip(),
            email=self._email_edit.text().strip(),
            bachelor_school=self._bsch_edit.text().strip(),
            bachelor_major=self._bmaj_edit.text().strip(),
            bachelor_grad_year=self._byr_edit.text().strip(),
            master_school=self._msch_edit.text().strip(),
            master_major=self._mmaj_edit.text().strip(),
            master_grad_year=self._myr_edit.text().strip(),
            education_level=self._edu_cb.currentText(),
            dept_id=self._dept_cb.currentData(),
            group_id=self._group_cb.currentData(),
            job_title=self._title_edit.text().strip(),
            job_level=self._level_edit.text().strip(),
            job_grade=self._grade_edit.text().strip(),
            qualification=self._qual_edit.text().strip(),
            perf_latest=self._perf_latest.text().strip(),
            perf_3y=self._perf_3y.text().strip(),
            perf_5times=self._perf_5t.text().strip(),
            perf_5y=self._perf_5y.text().strip(),
            status=_status_map.get(self._status_cb.currentText(), "active"),
            employee_type=self._type_cb.currentText(),
            avatar_path="",
            notes=self._notes_edit.toPlainText().strip(),
            created_at="",
            updated_at="",
        )

        if self._editing:
            ok = emp_mgr.update_employee(emp)
        else:
            ok = emp_mgr.add_employee(emp)

        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查工号是否重复或数据是否完整")
