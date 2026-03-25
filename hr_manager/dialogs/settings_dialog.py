"""SettingsDialog — password change, backup/restore, about."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QTabWidget, QWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from styles import _BLUE, _LIGHT, _BORDER, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER, INPUT_QSS

_APP_VERSION = "1.0.0"


class SettingsDialog(QDialog):
    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(480)
        self.setStyleSheet(f"background:{_LIGHT};")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_BLUE};")
        hdr.setFixedHeight(46)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(20, 0, 20, 0)
        ttl = QLabel("系统设置")
        ttl.setStyleSheet("color:white; font-size:15px; font-weight:bold;")
        hl.addWidget(ttl)
        root.addWidget(hdr)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: white; }}
            QTabBar::tab {{
                padding: 8px 18px; font-size: 13px;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color:{_BLUE}; border-bottom:2px solid {_BLUE}; font-weight:bold;
            }}
        """)

        tabs.addTab(self._build_password_tab(), "修改密码")
        tabs.addTab(self._build_backup_tab(), "数据备份")
        tabs.addTab(self._build_about_tab(), "关于")

        root.addWidget(tabs, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 8, 20, 14)
        btn_row.addStretch(1)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(BTN_SECONDARY)
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _build_password_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:white;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._old_pw = QLineEdit()
        self._old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._old_pw.setPlaceholderText("当前密码")
        form.addRow("当前密码", self._old_pw)

        self._new_pw = QLineEdit()
        self._new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pw.setPlaceholderText("至少6位")
        form.addRow("新密码", self._new_pw)

        self._confirm_pw = QLineEdit()
        self._confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pw.setPlaceholderText("再次输入新密码")
        form.addRow("确认新密码", self._confirm_pw)

        for widget in [self._old_pw, self._new_pw, self._confirm_pw]:
            widget.setStyleSheet(INPUT_QSS)

        lay.addLayout(form)

        change_btn = QPushButton("修改密码")
        change_btn.setStyleSheet(BTN_PRIMARY)
        change_btn.setFixedHeight(36)
        change_btn.clicked.connect(self._on_change_password)
        lay.addWidget(change_btn)
        lay.addStretch(1)
        return w

    def _build_backup_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:white;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 24, 30, 20)
        lay.setSpacing(16)

        # Backup section
        bk_title = QLabel("备份数据")
        bk_title.setStyleSheet(f"color:{_BLUE}; font-size:14px; font-weight:bold;")
        lay.addWidget(bk_title)

        bk_desc = QLabel("将数据库和加密密钥备份至指定文件夹。")
        bk_desc.setStyleSheet("color:#666; font-size:12px;")
        bk_desc.setWordWrap(True)
        lay.addWidget(bk_desc)

        backup_btn = QPushButton("选择备份目录并备份")
        backup_btn.setStyleSheet(BTN_PRIMARY)
        backup_btn.setFixedHeight(36)
        backup_btn.clicked.connect(self._on_backup)
        lay.addWidget(backup_btn)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_BORDER};")
        lay.addWidget(sep)

        # Restore section
        rs_title = QLabel("恢复数据")
        rs_title.setStyleSheet(f"color:#C0392B; font-size:14px; font-weight:bold;")
        lay.addWidget(rs_title)

        rs_desc = QLabel("从备份目录恢复数据。注意：此操作将覆盖当前所有数据！")
        rs_desc.setStyleSheet("color:#C0392B; font-size:12px;")
        rs_desc.setWordWrap(True)
        lay.addWidget(rs_desc)

        restore_btn = QPushButton("选择备份目录并恢复")
        restore_btn.setStyleSheet(BTN_DANGER)
        restore_btn.setFixedHeight(36)
        restore_btn.clicked.connect(self._on_restore)
        lay.addWidget(restore_btn)

        # Export section
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background:{_BORDER};")
        lay.addWidget(sep2)

        exp_title = QLabel("导出 Excel")
        exp_title.setStyleSheet(f"color:{_BLUE}; font-size:14px; font-weight:bold;")
        lay.addWidget(exp_title)

        export_btn = QPushButton("导出所有数据到 Excel")
        export_btn.setStyleSheet(BTN_SECONDARY)
        export_btn.setFixedHeight(36)
        export_btn.clicked.connect(self._on_export)
        lay.addWidget(export_btn)

        lay.addStretch(1)
        return w

    def _build_about_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:white;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 30, 40, 20)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo_lbl = QLabel("HR")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet(
            f"color:white; background:{_BLUE}; font-size:32px; font-weight:bold; "
            f"border-radius:12px; padding:16px 20px;"
        )
        logo_lbl.setFixedSize(80, 80)
        logo_row = QHBoxLayout()
        logo_row.addStretch(1)
        logo_row.addWidget(logo_lbl)
        logo_row.addStretch(1)
        lay.addLayout(logo_row)

        name_lbl = QLabel("HR Manager")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"color:{_BLUE}; font-size:20px; font-weight:bold;")
        lay.addWidget(name_lbl)

        ver_lbl = QLabel(f"版本: v{_APP_VERSION}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("color:#888; font-size:13px;")
        lay.addWidget(ver_lbl)

        desc_lbl = QLabel("企业人力资源管理系统\n支持员工管理、合同管理、薪酬管理、ESOP、稳定性评估等功能。")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setStyleSheet("color:#555; font-size:12px; line-height:1.6;")
        desc_lbl.setWordWrap(True)
        lay.addWidget(desc_lbl)

        lay.addStretch(1)
        return w

    # ── Actions ───────────────────────────────────────────────────────────

    def _on_change_password(self):
        auth_mgr = self._mgr.get("auth")
        if not auth_mgr:
            QMessageBox.warning(self, "错误", "认证模块未加载")
            return
        old_pw = self._old_pw.text()
        new_pw = self._new_pw.text()
        confirm = self._confirm_pw.text()
        if not old_pw or not new_pw:
            QMessageBox.warning(self, "提示", "请填写当前密码和新密码")
            return
        if len(new_pw) < 6:
            QMessageBox.warning(self, "提示", "新密码至少6位")
            return
        if new_pw != confirm:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致")
            return
        username = auth_mgr.current_user or "admin"
        ok = auth_mgr.change_password(username, old_pw, new_pw)
        if ok:
            QMessageBox.information(self, "成功", "密码修改成功！")
            self._old_pw.clear()
            self._new_pw.clear()
            self._confirm_pw.clear()
        else:
            QMessageBox.warning(self, "失败", "当前密码不正确")

    def _on_backup(self):
        backup_mgr = self._mgr.get("backup")
        if not backup_mgr:
            QMessageBox.warning(self, "错误", "备份模块未加载")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, "选择备份目录")
        if not dest_dir:
            return
        result = backup_mgr.backup_to_file(dest_dir)
        QMessageBox.information(self, "备份成功", f"备份已保存至:\n{result}")

    def _on_restore(self):
        backup_mgr = self._mgr.get("backup")
        if not backup_mgr:
            QMessageBox.warning(self, "错误", "备份模块未加载")
            return
        if QMessageBox.question(
            self, "确认恢复",
            "此操作将覆盖当前所有数据！确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        src_dir = QFileDialog.getExistingDirectory(self, "选择备份目录")
        if not src_dir:
            return
        ok = backup_mgr.restore_from_dir(src_dir)
        if ok:
            QMessageBox.information(self, "恢复成功", "数据已恢复，请重启应用以使数据生效。")
        else:
            QMessageBox.warning(self, "恢复失败", "备份目录中未找到有效备份文件")

    def _on_export(self):
        backup_mgr = self._mgr.get("backup")
        if not backup_mgr:
            QMessageBox.warning(self, "错误", "备份模块未加载")
            return
        dest_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", "hr_export.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not dest_path:
            return
        ok = backup_mgr.export_to_excel(dest_path, self._mgr)
        if ok:
            QMessageBox.information(self, "导出成功", f"数据已导出至:\n{dest_path}")
        else:
            QMessageBox.warning(self, "导出失败", "导出失败，请检查 openpyxl 是否已安装")
