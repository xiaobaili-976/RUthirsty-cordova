"""
Data models — pure Python dataclasses, one per DB table.
No SQLite logic here; all I/O is in managers/*.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── helpers ──────────────────────────────────────────────────────────────────

def _age_from_dob(dob: Optional[str]) -> Optional[int]:
    if not dob:
        return None
    try:
        born = date.fromisoformat(dob)
        today = date.today()
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )
    except ValueError:
        return None


def _tenure_months(hire_date: Optional[str]) -> Optional[int]:
    if not hire_date:
        return None
    try:
        hired = date.fromisoformat(hire_date)
        today = date.today()
        return (today.year - hired.year) * 12 + (today.month - hired.month)
    except ValueError:
        return None


def _days_until(target_date: Optional[str]) -> Optional[int]:
    if not target_date:
        return None
    try:
        return (date.fromisoformat(target_date) - date.today()).days
    except ValueError:
        return None


# ── models ────────────────────────────────────────────────────────────────────

@dataclass
class User:
    id: int = 0
    username: str = ""
    password_hash: str = ""
    role: str = "admin"
    created_at: str = ""


@dataclass
class Department:
    dept_id: int = 0
    dept_name: str = ""
    description: str = ""
    head_employee_id: str = ""   # FK → employees.employee_id (nullable)
    sort_order: int = 0
    created_at: str = ""


@dataclass
class Group:
    group_id: int = 0
    dept_id: int = 0
    group_name: str = ""
    description: str = ""
    lead_employee_id: str = ""   # FK → employees.employee_id (nullable)
    sort_order: int = 0
    created_at: str = ""


@dataclass
class Employee:
    employee_id: str = ""        # PK, human-assigned e.g. "EMP-001"
    name: str = ""
    gender: str = ""
    dob: str = ""                # "YYYY-MM-DD"
    id_number: str = ""
    phone: str = ""
    email: str = ""
    # education: list stored as JSON in DB, parsed to list on read
    bachelor_school: str = ""
    bachelor_major: str = ""
    bachelor_grad_year: str = ""
    master_school: str = ""
    master_major: str = ""
    master_grad_year: str = ""
    education_level: str = ""    # 本科/硕士/博士/其他
    dept_id: Optional[int] = None
    group_id: Optional[int] = None
    job_title: str = ""
    job_level: str = ""          # 职级 e.g. P5
    job_grade: str = ""          # 职等 e.g. 高级工程师
    qualification: str = ""      # 任职资格
    perf_latest: str = ""        # 最近一次绩效
    perf_3y: str = ""            # 近3年绩效
    perf_5times: str = ""        # 近5次绩效
    perf_5y: str = ""            # 近5年绩效
    status: str = "active"       # active / probation / resigned
    avatar_path: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @property
    def age(self) -> Optional[int]:
        return _age_from_dob(self.dob)

    @property
    def display_status(self) -> str:
        mapping = {"active": "在职", "probation": "试用期", "resigned": "已离职"}
        return mapping.get(self.status, self.status)


@dataclass
class Contract:
    contract_id: int = 0
    employee_id: str = ""
    employee_name: str = ""      # joined, not stored
    contract_type: str = ""      # 固定期/无固定期/实习
    hire_date: str = ""          # "YYYY-MM-DD"
    start_date: str = ""
    end_date: str = ""           # empty = open-ended
    renewal_date: str = ""       # next renewal reminder
    probation_end: str = ""
    status: str = "active"       # active / expired / terminated
    notes: str = ""
    created_at: str = ""

    @property
    def tenure_months(self) -> Optional[int]:
        return _tenure_months(self.hire_date)

    @property
    def days_to_renewal(self) -> Optional[int]:
        return _days_until(self.renewal_date)

    @property
    def days_to_end(self) -> Optional[int]:
        return _days_until(self.end_date)


@dataclass
class Salary:
    salary_id: int = 0
    employee_id: str = ""
    employee_name: str = ""      # joined, not stored
    effective_date: str = ""
    base_salary: float = 0.0     # decrypted on read
    performance_pay: float = 0.0
    total_salary: float = 0.0
    cr: float = 0.0              # compa-ratio
    pay_band: str = ""
    band_min: float = 0.0
    band_mid: float = 0.0
    band_max: float = 0.0
    bonus_last: float = 0.0      # 最近一次年终奖
    raise_source: str = ""       # 调薪来源
    raise_reason: str = ""
    planned_raise_date: str = ""
    planned_raise_amount: float = 0.0
    approved_by: str = ""
    created_at: str = ""

    @property
    def days_since_raise(self) -> Optional[int]:
        d = _days_until(self.effective_date)
        return -d if d is not None else None   # negative delta = past


@dataclass
class Position:
    position_id: int = 0
    employee_id: str = ""
    employee_name: str = ""
    effective_date: str = ""
    level: str = ""              # 职级
    grade: str = ""              # 职等
    adjustment_type: str = ""    # 晋升/降级/平调/入职
    reason: str = ""
    approved_by: str = ""
    planned_date: str = ""
    planned_type: str = ""
    planned_source: str = ""
    created_at: str = ""

    @property
    def days_since_adjustment(self) -> Optional[int]:
        d = _days_until(self.effective_date)
        return -d if d is not None else None


@dataclass
class Esop:
    esop_id: int = 0
    employee_id: str = ""
    employee_name: str = ""
    grant_date: str = ""
    shares_granted: float = 0.0
    shares_vested: float = 0.0
    shares_unvested: float = 0.0
    annual_guideline: float = 0.0  # 年度指导线
    grant_upper: float = 0.0       # 授予上限
    grant_lower: float = 0.0       # 授予下限
    saturation: float = 0.0        # 饱和度 0.0–1.0  (computed: vested/granted)
    talent_result: str = ""        # 上次人才识别结果
    vest_schedule: str = ""        # JSON string
    plan_name: str = ""
    notes: str = ""
    created_at: str = ""

    def compute_saturation(self) -> float:
        if self.shares_granted > 0:
            return min(self.shares_vested / self.shares_granted, 1.0)
        return 0.0


@dataclass
class CommLogEntry:
    date: str = ""
    method: str = ""    # 面谈/电话/微信
    content: str = ""
    emotion: str = ""   # 情绪表达
    risk_points: str = ""
    follow_up: str = ""
    follow_up_person: str = ""


@dataclass
class Stability:
    stability_id: int = 0
    employee_id: str = ""
    employee_name: str = ""
    assessment_date: str = ""
    # Family dimensions
    is_only_child: str = ""
    marital_status: str = ""
    children: str = ""
    family_jobs: str = ""
    address: str = ""
    commute_distance: str = ""
    housing: str = ""
    # Career dimensions
    job_match: int = 5           # 1–10
    promotion_expectation: str = ""
    growth_needs: str = ""
    transfer_willingness: str = ""
    salary_level_expectation: str = ""
    # Work dimensions
    workload: int = 5            # 1–10
    daily_state: str = ""
    superior_cooperation: int = 5
    team_integration: int = 5
    work_satisfaction: int = 5
    # Core demand
    urgent_demand_type: str = ""
    urgent_demand_detail: str = ""
    # Family life
    family_harmony: int = 5
    major_family_events: str = ""
    life_pressure: int = 5
    emotional_stability: int = 5
    # Personality
    personality_type: str = ""
    hobbies: str = ""
    social_circle: str = ""
    value_alignment: int = 5
    # Scores (decrypted on read)
    family_score: float = 5.0
    career_score: float = 5.0
    work_score: float = 5.0
    overall_score: float = 5.0
    risk_level: str = "green"    # plaintext: green/yellow/red
    risk_tags: str = ""          # comma-separated auto tags
    comm_log: list = field(default_factory=list)  # list[CommLogEntry]
    assessed_by: str = ""
    created_at: str = ""

    @property
    def risk_level_display(self) -> str:
        return {"green": "稳定", "yellow": "需关注", "red": "高风险"}.get(
            self.risk_level, self.risk_level
        )
