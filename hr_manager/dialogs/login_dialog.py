"""
LoginDialog — modal login window.
Default credentials: admin / admin123
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPen

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import _BLUE, _GOLD, _BG, _LIGHT, _BORDER


class LoginDialog(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._auth = auth_manager
        self._logged_in = False
        self.setWindowTitle("HR Manager — 登录")
        self.setFixedSize(400, 340)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setStyleSheet(f"background:{_BG};")
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 32)
        lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        title = QLabel("人员信息管理系统")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{_BLUE}; margin-bottom:4px;")
        lay.addWidget(title)

        sub = QLabel("HR Manager v1.0")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#888; font-size:12px; margin-bottom:28px;")
        lay.addWidget(sub)

        # ── Form ──────────────────────────────────────────────────────────
        field_style = (
            f"border:1px solid {_BORDER}; border-radius:6px; padding:8px 12px;"
            f"font-size:13px; background:{_LIGHT};"
            f"selection-background-color:{_BLUE};"
        )

        lbl_user = QLabel("用户名")
        lbl_user.setStyleSheet("font-size:12px; color:#555; margin-top:16px; margin-bottom:4px;")
        lay.addWidget(lbl_user)
        self._edit_user = QLineEdit()
        self._edit_user.setPlaceholderText("请输入用户名")
        self._edit_user.setStyleSheet(field_style)
        self._edit_user.setFixedHeight(38)
        self._edit_user.setText("admin")
        lay.addWidget(self._edit_user)

        lbl_pw = QLabel("密码")
        lbl_pw.setStyleSheet("font-size:12px; color:#555; margin-top:12px; margin-bottom:4px;")
        lay.addWidget(lbl_pw)
        self._edit_pw = QLineEdit()
        self._edit_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_pw.setPlaceholderText("请输入密码")
        self._edit_pw.setStyleSheet(field_style)
        self._edit_pw.setFixedHeight(38)
        lay.addWidget(self._edit_pw)

        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet("color:#C0392B; font-size:12px; margin-top:6px;")
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._err_lbl)

        lay.addStretch(1)

        # ── Login button ──────────────────────────────────────────────────
        btn = QPushButton("登 录")
        btn.setFixedHeight(42)
        btn.setStyleSheet(
            f"background:{_BLUE}; color:white; border:none; border-radius:6px;"
            f"font-size:14px; font-weight:bold;"
            f"QPushButton:hover{{background:#004bb5;}}"
            f"QPushButton:pressed{{background:#002060;}}"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_login)
        lay.addWidget(btn)

        self._edit_pw.returnPressed.connect(self._on_login)
        self._edit_user.returnPressed.connect(self._edit_pw.setFocus)

    def _on_login(self):
        username = self._edit_user.text().strip()
        password = self._edit_pw.text()
        if not username or not password:
            self._err_lbl.setText("用户名和密码不能为空")
            return
        if self._auth.login(username, password):
            self._logged_in = True
            self.accept()
        else:
            self._err_lbl.setText("用户名或密码错误，请重试")
            self._edit_pw.clear()
            self._edit_pw.setFocus()

    def accepted_login(self) -> bool:
        return self._logged_in
