"""Entry point — TOEIC Speaking Pro."""
import sys
import os

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from engine          import ExamEngine
from recorder        import RecorderManager
from window          import MainWindow
from license_manager import LicenseManager
from marks_manager   import MarksManager
from review_engine   import ReviewEngine


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("TOEIC Speaking Pro")

    # Global tooltip style — 微软雅黑 12 px, white text, no background box
    app.setStyleSheet("""
        QToolTip {
            background: transparent;
            color: #FFFFFF;
            border: none;
            font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
            font-size: 12px;
            padding: 2px 4px;
        }
    """)

    engine      = ExamEngine(BASE_DIR)
    recorder    = RecorderManager(BASE_DIR)
    license_mgr = LicenseManager(BASE_DIR)
    marks_mgr   = MarksManager(BASE_DIR)
    rev_engine  = ReviewEngine(engine)

    win = MainWindow(
        engine,
        recorder,
        license_mgr=license_mgr,
        marks_mgr=marks_mgr,
        review_engine=rev_engine,
    )
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
