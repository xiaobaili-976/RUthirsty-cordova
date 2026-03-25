"""
MainWindow — top-level window assembling all UI regions.
Nav → (Sidebar | StackedWidget | RightDrawer) → StatusBar
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QStatusBar, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from styles import (
    _BG, _LIGHT, _BORDER, _RED,
    NAV_HEIGHT, STATUS_QSS
)
from widgets.nav_bar import NavBar
from widgets.sidebar import Sidebar
from widgets.right_drawer import RightDrawer

# Pages
from pages.dashboard_page import DashboardPage
from pages.employee_page   import EmployeePage
from pages.contract_page   import ContractPage
from pages.salary_page     import SalaryPage
from pages.position_page   import PositionPage
from pages.esop_page       import EsopPage
from pages.stability_page  import StabilityPage


class MainWindow(QMainWindow):
    def __init__(self, managers: dict, parent=None):
        """
        managers = {
            'auth': AuthManager,
            'employee': EmployeeManager,
            'contract': ContractManager,
            'salary': SalaryManager,
            'position': PositionManager,
            'esop': EsopManager,
            'stability': StabilityManager,
            'backup': BackupManager,
        }
        """
        super().__init__(parent)
        self._mgr = managers
        self.setWindowTitle("人员信息与组织架构可视化管理系统")
        self.setMinimumSize(1280, 780)
        self.setStyleSheet(f"background:{_BG};")
        self._build_ui()
        self._refresh_status()
        # Periodic refresh every 60s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(60_000)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Navigation bar ────────────────────────────────────────────────
        self._nav = NavBar(self)
        self._nav.tab_changed.connect(self._on_tab)
        root.addWidget(self._nav)

        # ── Body row ──────────────────────────────────────────────────────
        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)

        self._sidebar = Sidebar(self._mgr, self)
        self._sidebar.employee_selected.connect(self._on_employee_selected)
        body_row.addWidget(self._sidebar)

        # ── Page stack ────────────────────────────────────────────────────
        # Tab indices: 0=首页, 1=基础信息, 2=合同, 3=薪酬, 4=人岗, 5=激励, 6=晴雨表
        # Tab 7 = 设置 (no page — opens dialog)
        self._stack = QStackedWidget()
        self._dash_page = DashboardPage(self._mgr, self)
        self._dash_page.employee_selected.connect(self._on_employee_selected)
        self._pages = [
            self._dash_page,                    # 0 首页
            EmployeePage(self._mgr, self),       # 1 基础信息
            ContractPage(self._mgr, self),       # 2 合同管理
            SalaryPage(self._mgr, self),         # 3 薪酬管理
            PositionPage(self._mgr, self),       # 4 人岗管理
            EsopPage(self._mgr, self),           # 5 长期激励
            StabilityPage(self._mgr, self),      # 6 晴雨表
        ]
        for p in self._pages:
            self._stack.addWidget(p)
        body_row.addWidget(self._stack, 1)

        # ── Right drawer ──────────────────────────────────────────────────
        self._drawer = RightDrawer(self._mgr, self)
        body_row.addWidget(self._drawer)

        root.addLayout(body_row, 1)

        # ── Status bar ────────────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(STATUS_QSS)
        self.setStatusBar(self._status_bar)

        self._lbl_user      = QLabel()
        self._lbl_total     = QLabel()
        self._lbl_risk      = QLabel()
        self._lbl_contracts = QLabel()
        self._lbl_updated   = QLabel()
        for lbl in (self._lbl_user, self._lbl_total,
                    self._lbl_risk, self._lbl_contracts, self._lbl_updated):
            lbl.setStyleSheet("padding: 0 12px; font-size:11px; color:#666;")
            self._status_bar.addWidget(lbl)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_tab(self, index: int):
        if index == 7:
            # Settings — open dialog
            self._open_settings()
            # Keep nav highlight on previous tab
            self._nav._set_active(self._stack.currentIndex())
            return
        self._stack.setCurrentIndex(index)
        self._pages[index].refresh()

    def _open_settings(self):
        try:
            from dialogs.settings_dialog import SettingsDialog
            dlg = SettingsDialog(self._mgr, self)
            dlg.exec()
        except Exception as e:
            print(f"[Settings] {e}")

    def _on_employee_selected(self, employee_id: str):
        self._drawer.load_employee(employee_id)

    def _refresh_status(self):
        auth     = self._mgr.get("auth")
        emp_mgr  = self._mgr.get("employee")
        stab_mgr = self._mgr.get("stability")
        cont_mgr = self._mgr.get("contract")

        user       = auth.current_user if auth else "—"
        total      = len(emp_mgr.list_employees()) if emp_mgr else 0
        risk_count = len(stab_mgr.get_high_risk_employees()) if stab_mgr else 0
        expiring   = len(cont_mgr.get_expiring_soon(270)) if cont_mgr else 0

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        self._lbl_user.setText(f"👤 {user}")
        self._lbl_total.setText(f"人员总数: {total}")
        self._lbl_risk.setText(
            f"高风险: <span style='color:#C0392B;font-weight:bold;'>{risk_count}</span>"
            if risk_count else "高风险: 0"
        )
        self._lbl_contracts.setText(f"合同到期(9个月内): {expiring}")
        self._lbl_updated.setText(f"更新: {now}")

    def refresh_all(self):
        for p in self._pages:
            p.refresh()
        self._refresh_status()
        self._sidebar.refresh()
