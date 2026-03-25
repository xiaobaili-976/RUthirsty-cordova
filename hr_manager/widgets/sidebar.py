"""Sidebar — left panel with search, high-risk list, contract alerts, backup button."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from styles import (
    _BLUE, _LIGHT, _BORDER, _RED, _YELLOW, _GREEN,
    _RED_LIGHT, _YELLOW_LIGHT, BTN_SECONDARY, SIDEBAR_QSS
)


class Sidebar(QWidget):
    employee_selected = pyqtSignal(str)   # employee_id

    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self.setStyleSheet(SIDEBAR_QSS + f"QWidget#Sidebar{{background:{_LIGHT};}}")
        self._mgr = managers
        self._build()
        self.refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(8)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("SearchBox")
        self._search.setPlaceholderText("🔍 搜索姓名/工号")
        self._search.setFixedHeight(30)
        self._search.textChanged.connect(self._on_search)
        lay.addWidget(self._search)

        # Search results
        self._search_list = QListWidget()
        self._search_list.setMaximumHeight(130)
        self._search_list.hide()
        self._search_list.itemClicked.connect(self._on_item_click)
        self._search_list.setStyleSheet(
            f"border:1px solid {_BORDER}; border-radius:4px; font-size:12px;"
        )
        lay.addWidget(self._search_list)

        # High-risk section
        self._risk_lbl = QLabel("⚠ 高风险人员")
        self._risk_lbl.setStyleSheet(
            f"color:{_RED}; font-weight:bold; font-size:12px; margin-top:8px;"
        )
        lay.addWidget(self._risk_lbl)
        self._risk_list = QListWidget()
        self._risk_list.setMaximumHeight(120)
        self._risk_list.setStyleSheet(
            f"border:1px solid {_BORDER}; border-radius:4px; font-size:11px;"
        )
        self._risk_list.itemClicked.connect(self._on_item_click)
        lay.addWidget(self._risk_list)

        # Contract expiry section
        self._contract_lbl = QLabel("📋 合同即将到期")
        self._contract_lbl.setStyleSheet(
            f"color:#E67E22; font-weight:bold; font-size:12px; margin-top:8px;"
        )
        lay.addWidget(self._contract_lbl)
        self._contract_list = QListWidget()
        self._contract_list.setMaximumHeight(120)
        self._contract_list.setStyleSheet(
            f"border:1px solid {_BORDER}; border-radius:4px; font-size:11px;"
        )
        self._contract_list.itemClicked.connect(self._on_item_click)
        lay.addWidget(self._contract_list)

        lay.addStretch(1)

        # Backup button
        backup_btn = QPushButton("💾 数据备份")
        backup_btn.setStyleSheet(BTN_SECONDARY)
        backup_btn.setFixedHeight(32)
        backup_btn.clicked.connect(self._on_backup)
        lay.addWidget(backup_btn)

    def refresh(self):
        self._refresh_risk()
        self._refresh_contracts()

    def _refresh_risk(self):
        self._risk_list.clear()
        stab_mgr = self._mgr.get("stability")
        if not stab_mgr:
            return
        for item in stab_mgr.get_high_risk_employees():
            li = QListWidgetItem(f"🔴 {item['name']} ({item['employee_id']})")
            li.setData(Qt.ItemDataRole.UserRole, item["employee_id"])
            li.setForeground(QColor(_RED))
            self._risk_list.addItem(li)

    def _refresh_contracts(self):
        self._contract_list.clear()
        cont_mgr = self._mgr.get("contract")
        if not cont_mgr:
            return
        for item in cont_mgr.get_expiring_soon(30):
            d = item["days_left"]
            color = _RED if d <= 7 else "#E67E22"
            li = QListWidgetItem(
                f"{'🔴' if d<=7 else '🟡'} {item['name']} ({d}天)"
            )
            li.setData(Qt.ItemDataRole.UserRole, item["employee_id"])
            li.setForeground(QColor(color))
            self._contract_list.addItem(li)

    def _on_search(self, text: str):
        if not text.strip():
            self._search_list.hide()
            return
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        results = emp_mgr.search(text.strip())
        self._search_list.clear()
        for e in results[:10]:
            li = QListWidgetItem(f"{e.name}  {e.employee_id}")
            li.setData(Qt.ItemDataRole.UserRole, e.employee_id)
            self._search_list.addItem(li)
        self._search_list.setVisible(bool(results))

    def _on_item_click(self, item: QListWidgetItem):
        eid = item.data(Qt.ItemDataRole.UserRole)
        if eid:
            self.employee_selected.emit(eid)

    def _on_backup(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        dest = QFileDialog.getExistingDirectory(self, "选择备份目录")
        if dest:
            bk_mgr = self._mgr.get("backup")
            if bk_mgr:
                path = bk_mgr.backup_to_file(dest)
                QMessageBox.information(self, "备份成功", f"备份已保存到:\n{path}")
