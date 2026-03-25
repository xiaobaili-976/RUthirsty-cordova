"""StabilityForm — multi-tab stability assessment dialog with comm log."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit, QCompleter,
    QMessageBox, QWidget, QTabWidget, QSlider, QScrollArea, QListWidget,
    QListWidgetItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _GREEN, _YELLOW, _RED,
    BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER, INPUT_QSS,
    RISK_COLOR, RISK_BG
)


def _to_qdate(iso: str) -> QDate:
    try:
        d = date.fromisoformat(iso)
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


def _slider_row(label: str, lo=1, hi=10, default=5) -> tuple:
    """Return (QWidget container, QSlider, QLabel for value)."""
    container = QWidget()
    h = QHBoxLayout(container)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(lo, hi)
    slider.setValue(default)
    slider.setFixedWidth(160)
    val_lbl = QLabel(str(default))
    val_lbl.setFixedWidth(24)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val_lbl.setStyleSheet(f"color:{_BLUE}; font-weight:bold;")
    slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
    h.addWidget(slider)
    h.addWidget(val_lbl)
    h.addStretch(1)
    return container, slider, val_lbl


def _make_form(parent_widget) -> "QFormLayout":
    form = QFormLayout(parent_widget)
    form.setContentsMargins(20, 12, 20, 12)
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    return form
    """Build a scrollable form. fields = list of (label, widget).
    Returns (QScrollArea, list of widgets added)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")
    inner = QWidget()
    inner.setStyleSheet("background:white;")
    scroll.setWidget(inner)
    form = QFormLayout(inner)
    form.setContentsMargins(20, 12, 20, 12)
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    for lbl_text, widget in fields:
        form.addRow(lbl_text, widget)
    return scroll


class CommLogSubDialog(QDialog):
    """Sub-dialog to add a single communication log entry."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增沟通记录")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{_LIGHT};")
        self._result = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.addWidget(QLabel("新增沟通记录", styleSheet="color:white;font-size:13px;font-weight:bold;"))
        root.addWidget(hdr)

        content = QWidget()
        content.setStyleSheet("background:white;")
        form = QFormLayout(content)
        form.setContentsMargins(20, 14, 20, 12)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        form.addRow("沟通日期", self._date_edit)

        self._type_edit = QLineEdit()
        self._type_edit.setPlaceholderText("如: 一对一谈话 / 部门会议")
        form.addRow("沟通类型", self._type_edit)

        self._summary_edit = QTextEdit()
        self._summary_edit.setFixedHeight(80)
        form.addRow("沟通摘要", self._summary_edit)

        self._followup_edit = QLineEdit()
        self._followup_edit.setPlaceholderText("后续行动")
        form.addRow("后续行动", self._followup_edit)

        self._by_edit = QLineEdit()
        form.addRow("记录人", self._by_edit)

        for w in content.findChildren((QLineEdit, QTextEdit, QDateEdit)):
            w.setStyleSheet(INPUT_QSS)

        root.addWidget(content)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 8, 20, 14)
        btn_row.addStretch(1)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.setFixedHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.setFixedHeight(32)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    def _on_save(self):
        from db.models import CommLogEntry
        self._result = CommLogEntry(
            comm_date=self._date_edit.date().toString("yyyy-MM-dd"),
            comm_type=self._type_edit.text().strip(),
            summary=self._summary_edit.toPlainText().strip(),
            followup=self._followup_edit.text().strip(),
            recorded_by=self._by_edit.text().strip(),
        )
        self.accept()

    def get_entry(self):
        return self._result


class StabilityForm(QDialog):
    def __init__(self, managers: dict, assessment=None, open_comm_tab: bool = False, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._assessment = assessment
        self._editing = assessment is not None
        self._open_comm_tab = open_comm_tab
        self._comm_log = list(assessment.comm_log) if assessment and assessment.comm_log else []
        self.setWindowTitle("编辑稳定性评估" if self._editing else "新增稳定性评估")
        self.setMinimumWidth(640)
        self.setMinimumHeight(580)
        self.setStyleSheet(f"background:{_LIGHT};")
        self._build()
        if self._editing:
            self._populate()
        if open_comm_tab:
            self._tabs.setCurrentIndex(7)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr.setFixedHeight(46)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(20, 0, 20, 0)
        ttl = QLabel("编辑稳定性评估" if self._editing else "新增稳定性评估")
        ttl.setStyleSheet("color:white;font-size:14px;font-weight:bold;")
        hl.addWidget(ttl)
        root.addWidget(hdr)

        # Employee ID (above tabs)
        top_bar = QWidget()
        top_bar.setStyleSheet("background:white; border-bottom:1px solid #dde3ee;")
        tb_lay = QHBoxLayout(top_bar)
        tb_lay.setContentsMargins(20, 8, 20, 8)
        tb_lay.addWidget(QLabel("员工工号 *:", styleSheet=f"color:{_BLUE};font-weight:bold;"))
        self._eid_edit = QLineEdit()
        self._eid_edit.setPlaceholderText("输入工号或姓名搜索…")
        self._eid_edit.setFixedWidth(220)
        emp_mgr = self._mgr.get("employee")
        if emp_mgr:
            emps = emp_mgr.list_employees()
            suggestions = [f"{e.employee_id} {e.name}" for e in emps]
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._eid_edit.setCompleter(completer)
        self._eid_edit.setStyleSheet(INPUT_QSS)
        tb_lay.addWidget(self._eid_edit)
        tb_lay.addSpacing(16)
        tb_lay.addWidget(QLabel("评估日期:"))
        self._assess_date = QDateEdit()
        self._assess_date.setCalendarPopup(True)
        self._assess_date.setDate(QDate.currentDate())
        self._assess_date.setStyleSheet(INPUT_QSS)
        self._assess_date.setFixedWidth(130)
        tb_lay.addWidget(self._assess_date)
        tb_lay.addStretch(1)
        root.addWidget(top_bar)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: white; }}
            QTabBar::tab {{
                padding: 7px 14px; font-size: 12px;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{ color:{_BLUE}; border-bottom:2px solid {_BLUE}; font-weight:bold; }}
        """)
        root.addWidget(self._tabs, 1)

        self._build_tab1()
        self._build_tab2()
        self._build_tab3()
        self._build_tab4()
        self._build_tab5()
        self._build_tab6()
        self._build_tab7()
        self._build_tab8()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 8, 20, 14)
        btn_row.addStretch(1)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("保存评估")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # ── Tab builders ─────────────────────────────────────────────────────

    def _build_tab1(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        self._only_child = QComboBox(); self._only_child.addItems(["否", "是"])
        form.addRow("独生子女", self._only_child)
        self._marital = QLineEdit(); self._marital.setPlaceholderText("已婚/未婚/离异")
        form.addRow("婚姻状况", self._marital)
        self._children = QLineEdit(); self._children.setPlaceholderText("子女数量/年龄")
        form.addRow("子女情况", self._children)
        self._family_jobs = QLineEdit(); self._family_jobs.setPlaceholderText("家庭成员职业")
        form.addRow("家庭成员职业", self._family_jobs)
        self._address = QLineEdit()
        form.addRow("居住地址", self._address)
        self._commute = QLineEdit(); self._commute.setPlaceholderText("如: 30分钟 / 15公里")
        form.addRow("通勤距离", self._commute)
        self._housing = QLineEdit(); self._housing.setPlaceholderText("自购/租房/公司宿舍")
        form.addRow("住房情况", self._housing)

        for w2 in w.findChildren((QLineEdit, QComboBox)):
            w2.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "基本情况")

    def _build_tab2(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        row, self._job_match_slider, self._job_match_lbl = _slider_row("", 1, 10, 5)
        form.addRow("岗位匹配度(1-10)", row)
        self._promo_exp = QLineEdit(); self._promo_exp.setPlaceholderText("晋升期望描述")
        form.addRow("晋升期望", self._promo_exp)
        self._growth_needs = QLineEdit()
        form.addRow("成长需求", self._growth_needs)
        self._transfer_will = QLineEdit(); self._transfer_will.setPlaceholderText("高/中/低")
        form.addRow("转岗意愿", self._transfer_will)
        self._salary_exp = QLineEdit(); self._salary_exp.setPlaceholderText("薪酬满意度/期望")
        form.addRow("薪酬水平期望", self._salary_exp)

        for w2 in w.findChildren(QLineEdit):
            w2.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "职业发展")

    def _build_tab3(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        row, self._workload_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("工作量(1-10)", row)
        self._daily_state = QLineEdit(); self._daily_state.setPlaceholderText("日常工作状态描述")
        form.addRow("日常工作状态", self._daily_state)
        row2, self._sup_coop_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("上级配合度(1-10)", row2)
        row3, self._team_int_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("团队融合度(1-10)", row3)
        row4, self._work_sat_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("工作满意度(1-10)", row4)

        for w2 in w.findChildren(QLineEdit):
            w2.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "工作状态")

    def _build_tab4(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        self._urg_type = QComboBox()
        self._urg_type.addItems(["薪酬晋升", "工作内容", "团队关系", "家庭原因", "个人发展", "其他"])
        form.addRow("核心诉求类型", self._urg_type)
        self._urg_detail = QTextEdit()
        self._urg_detail.setFixedHeight(100)
        self._urg_detail.setPlaceholderText("详细描述核心诉求…")
        form.addRow("核心诉求详情", self._urg_detail)

        self._urg_type.setStyleSheet(INPUT_QSS)
        self._urg_detail.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "核心诉求")

    def _build_tab5(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        row, self._fam_harm_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("家庭和睦度(1-10)", row)
        self._maj_fam_events = QTextEdit()
        self._maj_fam_events.setFixedHeight(60)
        self._maj_fam_events.setPlaceholderText("重大家庭事件描述")
        form.addRow("重大家庭事件", self._maj_fam_events)
        row2, self._life_press_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("生活压力(1-10)", row2)
        row3, self._emo_stab_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("情绪稳定性(1-10)", row3)

        self._maj_fam_events.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "家庭生活")

    def _build_tab6(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        self._personality = QLineEdit(); self._personality.setPlaceholderText("如: INTJ / 外向型")
        form.addRow("性格类型", self._personality)
        self._hobbies = QLineEdit()
        form.addRow("兴趣爱好", self._hobbies)
        self._social = QLineEdit(); self._social.setPlaceholderText("社交圈描述")
        form.addRow("社交圈", self._social)
        row, self._val_align_slider, _ = _slider_row("", 1, 10, 5)
        form.addRow("价值观匹配度(1-10)", row)

        for w2 in w.findChildren(QLineEdit):
            w2.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "个人特质")

    def _build_tab7(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        form = _make_form(w)

        self._fam_score = QDoubleSpinBox()
        self._fam_score.setRange(0, 10)
        self._fam_score.setDecimals(1)
        self._fam_score.setSingleStep(0.5)
        self._fam_score.setValue(5.0)
        self._fam_score.valueChanged.connect(self._update_overall)
        form.addRow("家庭分(0-10)", self._fam_score)

        self._car_score = QDoubleSpinBox()
        self._car_score.setRange(0, 10)
        self._car_score.setDecimals(1)
        self._car_score.setSingleStep(0.5)
        self._car_score.setValue(5.0)
        self._car_score.valueChanged.connect(self._update_overall)
        form.addRow("职业分(0-10)", self._car_score)

        self._wk_score = QDoubleSpinBox()
        self._wk_score.setRange(0, 10)
        self._wk_score.setDecimals(1)
        self._wk_score.setSingleStep(0.5)
        self._wk_score.setValue(5.0)
        self._wk_score.valueChanged.connect(self._update_overall)
        form.addRow("工作分(0-10)", self._wk_score)

        overall_row = QHBoxLayout()
        self._overall_lbl = QLabel("5.0")
        self._overall_lbl.setStyleSheet(
            f"color:{_BLUE}; font-size:18px; font-weight:bold; "
            f"padding:4px 10px; background:#E8F0FE; border-radius:4px;"
        )
        overall_row.addWidget(self._overall_lbl)
        self._risk_badge = QLabel("需关注")
        self._risk_badge.setStyleSheet(
            f"color:{_YELLOW}; background:#FEF9E7; border:1px solid {_YELLOW}; "
            f"border-radius:10px; padding:3px 10px; font-weight:bold; font-size:12px;"
        )
        overall_row.addWidget(self._risk_badge)
        overall_row.addStretch(1)
        form.addRow("综合评分（自动）", overall_row)

        self._risk_tags = QLineEdit()
        self._risk_tags.setPlaceholderText("用逗号分隔，如: 薪资不满,家庭压力")
        form.addRow("风险标签", self._risk_tags)

        self._assessed_by = QLineEdit()
        form.addRow("评估人", self._assessed_by)

        for w2 in w.findChildren((QLineEdit, QDoubleSpinBox)):
            w2.setStyleSheet(INPUT_QSS)
        self._tabs.addTab(w, "综合评分")

    def _build_tab8(self):
        w = QWidget()
        w.setStyleSheet("background:white;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("沟通记录列表", styleSheet=f"color:{_BLUE};font-weight:bold;font-size:13px;"))
        top_bar.addStretch(1)
        add_comm_btn = QPushButton("+ 新增沟通记录")
        add_comm_btn.setStyleSheet(BTN_PRIMARY)
        add_comm_btn.setFixedHeight(30)
        add_comm_btn.clicked.connect(self._add_comm_entry)
        top_bar.addWidget(add_comm_btn)
        lay.addLayout(top_bar)

        self._comm_list = QListWidget()
        self._comm_list.setStyleSheet(
            f"QListWidget {{ border:1px solid {_BORDER}; border-radius:5px; }}"
            f"QListWidget::item {{ padding:8px 10px; border-bottom:1px solid {_BORDER}; }}"
            f"QListWidget::item:selected {{ background:#E8F0FE; color:{_BLUE}; }}"
        )
        lay.addWidget(self._comm_list, 1)
        self._refresh_comm_list()
        self._tabs.addTab(w, "沟通记录")

    # ── Helpers ───────────────────────────────────────────────────────────

    def _update_overall(self):
        fs = self._fam_score.value()
        cs = self._car_score.value()
        ws = self._wk_score.value()
        overall = (fs + cs + ws) / 3.0
        self._overall_lbl.setText(f"{overall:.1f}")
        if overall >= 7:
            risk, color, bg = "稳定", _GREEN, "#E9F7EF"
        elif overall >= 4:
            risk, color, bg = "需关注", _YELLOW, "#FEF9E7"
        else:
            risk, color, bg = "高风险", _RED, "#FDECEA"
        self._risk_badge.setText(risk)
        self._risk_badge.setStyleSheet(
            f"color:{color}; background:{bg}; border:1px solid {color}; "
            f"border-radius:10px; padding:3px 10px; font-weight:bold; font-size:12px;"
        )

    def _refresh_comm_list(self):
        self._comm_list.clear()
        for entry in self._comm_log:
            text = f"[{entry.comm_date}] {entry.comm_type or '沟通'}  —  {entry.summary or ''}"
            if entry.followup:
                text += f"\n    → 后续: {entry.followup}"
            item = QListWidgetItem(text)
            self._comm_list.addItem(item)

    def _add_comm_entry(self):
        dlg = CommLogSubDialog(parent=self)
        if dlg.exec():
            entry = dlg.get_entry()
            if entry:
                self._comm_log.insert(0, entry)
                self._refresh_comm_list()

    def _populate(self):
        s = self._assessment
        self._eid_edit.setText(s.employee_id)
        self._eid_edit.setReadOnly(True)
        if s.assessment_date:
            self._assess_date.setDate(_to_qdate(s.assessment_date))

        # Tab 1
        idx = self._only_child.findText("是" if s.is_only_child == "是" else "否")
        self._only_child.setCurrentIndex(max(0, idx))
        self._marital.setText(s.marital_status)
        self._children.setText(s.children)
        self._family_jobs.setText(s.family_jobs)
        self._address.setText(s.address)
        self._commute.setText(s.commute_distance)
        self._housing.setText(s.housing)

        # Tab 2
        self._job_match_slider.setValue(int(s.job_match) if s.job_match else 5)
        self._promo_exp.setText(s.promotion_expectation)
        self._growth_needs.setText(s.growth_needs)
        self._transfer_will.setText(s.transfer_willingness)
        self._salary_exp.setText(s.salary_level_expectation)

        # Tab 3
        self._workload_slider.setValue(int(s.workload) if s.workload else 5)
        self._daily_state.setText(s.daily_state)
        self._sup_coop_slider.setValue(int(s.superior_cooperation) if s.superior_cooperation else 5)
        self._team_int_slider.setValue(int(s.team_integration) if s.team_integration else 5)
        self._work_sat_slider.setValue(int(s.work_satisfaction) if s.work_satisfaction else 5)

        # Tab 4
        idx = self._urg_type.findText(s.urgent_demand_type)
        if idx >= 0:
            self._urg_type.setCurrentIndex(idx)
        self._urg_detail.setPlainText(s.urgent_demand_detail)

        # Tab 5
        self._fam_harm_slider.setValue(int(s.family_harmony) if s.family_harmony else 5)
        self._maj_fam_events.setPlainText(s.major_family_events)
        self._life_press_slider.setValue(int(s.life_pressure) if s.life_pressure else 5)
        self._emo_stab_slider.setValue(int(s.emotional_stability) if s.emotional_stability else 5)

        # Tab 6
        self._personality.setText(s.personality_type)
        self._hobbies.setText(s.hobbies)
        self._social.setText(s.social_circle)
        self._val_align_slider.setValue(int(s.value_alignment) if s.value_alignment else 5)

        # Tab 7
        self._fam_score.setValue(float(s.family_score))
        self._car_score.setValue(float(s.career_score))
        self._wk_score.setValue(float(s.work_score))
        self._update_overall()
        self._risk_tags.setText(s.risk_tags)
        self._assessed_by.setText(s.assessed_by)

    def _parse_employee_id(self) -> str:
        text = self._eid_edit.text().strip()
        return text.split()[0] if text else ""

    def _compute_risk_level(self, overall: float) -> str:
        if overall >= 7:
            return "green"
        elif overall >= 4:
            return "yellow"
        return "red"

    def _on_save(self):
        stab_mgr = self._mgr.get("stability")
        if not stab_mgr:
            return
        eid = self._parse_employee_id()
        if not eid:
            QMessageBox.warning(self, "提示", "请填写员工工号")
            return

        fs = self._fam_score.value()
        cs = self._car_score.value()
        ws = self._wk_score.value()
        overall = (fs + cs + ws) / 3.0

        from db.models import Stability
        s = Stability(
            stability_id=self._assessment.stability_id if self._editing else None,
            employee_id=eid,
            employee_name="",
            assessment_date=self._assess_date.date().toString("yyyy-MM-dd"),
            is_only_child=self._only_child.currentText(),
            marital_status=self._marital.text().strip(),
            children=self._children.text().strip(),
            family_jobs=self._family_jobs.text().strip(),
            address=self._address.text().strip(),
            commute_distance=self._commute.text().strip(),
            housing=self._housing.text().strip(),
            job_match=self._job_match_slider.value(),
            promotion_expectation=self._promo_exp.text().strip(),
            growth_needs=self._growth_needs.text().strip(),
            transfer_willingness=self._transfer_will.text().strip(),
            salary_level_expectation=self._salary_exp.text().strip(),
            workload=self._workload_slider.value(),
            daily_state=self._daily_state.text().strip(),
            superior_cooperation=self._sup_coop_slider.value(),
            team_integration=self._team_int_slider.value(),
            work_satisfaction=self._work_sat_slider.value(),
            urgent_demand_type=self._urg_type.currentText(),
            urgent_demand_detail=self._urg_detail.toPlainText().strip(),
            family_harmony=self._fam_harm_slider.value(),
            major_family_events=self._maj_fam_events.toPlainText().strip(),
            life_pressure=self._life_press_slider.value(),
            emotional_stability=self._emo_stab_slider.value(),
            personality_type=self._personality.text().strip(),
            hobbies=self._hobbies.text().strip(),
            social_circle=self._social.text().strip(),
            value_alignment=self._val_align_slider.value(),
            family_score=fs,
            career_score=cs,
            work_score=ws,
            overall_score=overall,
            risk_level=self._compute_risk_level(overall),
            risk_tags=self._risk_tags.text().strip(),
            comm_log=self._comm_log,
            assessed_by=self._assessed_by.text().strip(),
            created_at="",
        )
        ok = stab_mgr.update_assessment(s) if self._editing else stab_mgr.add_assessment(s)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "保存失败，请检查员工工号是否存在")
