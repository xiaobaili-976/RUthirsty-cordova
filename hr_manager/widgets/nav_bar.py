"""NavBar — top navigation with 8 module tabs + settings button."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor

from styles import _BLUE, _GOLD, NAV_HEIGHT, NAV_QSS, NAV_TAB_QSS


_TABS = [
    ("🏠 首页",   "控制台"),
    ("🌐 架构",   "组织架构"),
    ("👥 人员",   "基础信息"),
    ("📋 合同",   "合同管理"),
    ("💰 薪酬",   "薪酬管理"),
    ("📊 人岗",   "人岗管理"),
    ("🏆 激励",   "长期激励"),
    ("🌦 晴雨表", "稳定性晴雨表"),
]


class NavBar(QWidget):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(NAV_HEIGHT)
        self.setStyleSheet(NAV_QSS)
        self._active = 0
        self._btns: list[QPushButton] = []
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(0)

        # Brand label
        brand = QLabel("HR Manager")
        brand.setStyleSheet(
            f"color:{_GOLD}; font-size:15px; font-weight:bold;"
            f"font-family:'Microsoft YaHei'; padding-right:24px;"
        )
        lay.addWidget(brand)

        for i, (icon_label, tooltip) in enumerate(_TABS):
            btn = QPushButton(icon_label)
            btn.setToolTip(tooltip)
            btn.setFixedHeight(NAV_HEIGHT)
            btn.setMinimumWidth(70)
            btn.setStyleSheet(NAV_TAB_QSS)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda checked, idx=i: self._on_tab(idx))
            self._btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch(1)

        # Settings button
        self._settings_btn = QPushButton("⚙ 设置")
        self._settings_btn.setStyleSheet(NAV_TAB_QSS)
        self._settings_btn.setFixedHeight(NAV_HEIGHT)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self._settings_btn)

        self._set_active(0)

    def _on_tab(self, idx: int):
        self._set_active(idx)
        self.tab_changed.emit(idx)

    def _set_active(self, idx: int):
        self._active = idx
        for i, btn in enumerate(self._btns):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    @property
    def settings_button(self) -> QPushButton:
        return self._settings_btn
