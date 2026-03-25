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
    _BLUE, _GOLD, _BG, _LIGHT, _BORDER, _RED, _GREEN,
    NAV_HEIGHT, NAV_QSS, NAV_TAB_QSS, STATUS_QSS
)
from widgets.nav_bar import NavBar
from widgets.sidebar import Sidebar
from widgets.right_drawer import RightDrawer

# Pages (imported lazily to keep startup fast)
from pages.dashboard_page import DashboardPage
from pages.org_page       import OrgChartPage as OrgPage
from pages.employee_page  import EmployeePage
from pages.contract_page  import ContractPage
from pages.salary_page    import SalaryPage
from pages.position_page  import PositionPage
from pages.esop_page      import EsopPage
from pages.stability_page import StabilityPage


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
        # Periodic refresh every 60s (contract countdown, risk counts)
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
        self._stack = QStackedWidget()
        self._pages = [
            DashboardPage(self._mgr, self),
            OrgPage(self._mgr, self),
            EmployeePage(self._mgr, self),
            ContractPage(self._mgr, self),
            SalaryPage(self._mgr, self),
            PositionPage(self._mgr, self),
            EsopPage(self._mgr, self),
            StabilityPage(self._mgr, self),
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
        self._stack.setCurrentIndex(index)
        self._pages[index].refresh()

    def _on_employee_selected(self, employee_id: str):
        self._drawer.load_employee(employee_id)

    def _refresh_status(self):
        auth = self._mgr.get("auth")
        emp_mgr = self._mgr.get("employee")
        stab_mgr = self._mgr.get("stability")
        cont_mgr = self._mgr.get("contract")

        user = auth.current_user if auth else "—"
        total = len(emp_mgr.list_employees()) if emp_mgr else 0
        risk_count = len(stab_mgr.get_high_risk_employees()) if stab_mgr else 0
        expiring = len(cont_mgr.get_expiring_soon(30)) if cont_mgr else 0

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        self._lbl_user.setText(f"👤 {user}")
        self._lbl_total.setText(f"人员总数: {total}")
        self._lbl_risk.setText(
            f"高风险: <span style='color:#C0392B;font-weight:bold;'>{risk_count}</span>"
            if risk_count else f"高风险: 0"
        )
        self._lbl_contracts.setText(f"合同到期(30天): {expiring}")
        self._lbl_updated.setText(f"更新: {now}")

    def refresh_all(self):
        for p in self._pages:
            p.refresh()
        self._refresh_status()
        self._sidebar.refresh()
