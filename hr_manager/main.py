"""
main.py — application entry point.

Bootstraps:
  1. Resolves data directory (works both dev and PyInstaller onefile)
  2. Initialises DB, crypto, all managers
  3. Shows login dialog
  4. Opens MainWindow on successful login
"""
import sys
import os

# ── Path resolution (dev vs. PyInstaller onefile) ────────────────────────────
if getattr(sys, "frozen", False):
    # Running as compiled EXE — place data next to the EXE
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

_DATA_DIR = os.path.join(_BASE, "data")
_DB_PATH  = os.path.join(_DATA_DIR, "hr_manager.db")
_KEY_PATH = os.path.join(_DATA_DIR, "hr_crypto.key")

# Ensure sys.path includes the hr_manager package root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from db.database       import DatabaseManager
from db.crypto         import FieldCrypto
from managers.auth_manager      import AuthManager
from managers.employee_manager  import EmployeeManager
from managers.contract_manager  import ContractManager
from managers.salary_manager    import SalaryManager
from managers.position_manager  import PositionManager
from managers.esop_manager      import EsopManager
from managers.stability_manager import StabilityManager
from managers.backup_manager    import BackupManager
from dialogs.login_dialog import LoginDialog
from window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HR Manager")
    app.setApplicationVersion("1.0.0")

    # Default font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # High-DPI
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # ── Init backend ──────────────────────────────────────────────────────
    try:
        db     = DatabaseManager(_DB_PATH)
        crypto = FieldCrypto(_KEY_PATH)
    except Exception as exc:
        QMessageBox.critical(None, "初始化失败", f"数据库初始化错误:\n{exc}")
        return 1

    managers = {
        "auth":      AuthManager(db),
        "employee":  EmployeeManager(db),
        "contract":  ContractManager(db),
        "salary":    SalaryManager(db, crypto),
        "position":  PositionManager(db),
        "esop":      EsopManager(db),
        "stability": StabilityManager(db, crypto),
        "backup":    BackupManager(_DB_PATH, _KEY_PATH, _DATA_DIR),
    }

    # ── Login ─────────────────────────────────────────────────────────────
    login_dlg = LoginDialog(managers["auth"])
    if login_dlg.exec() != LoginDialog.DialogCode.Accepted:
        return 0

    # ── Main window ───────────────────────────────────────────────────────
    win = MainWindow(managers)
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
