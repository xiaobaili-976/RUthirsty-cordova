"""Entry point — TOEIC Speaking Test Simulator v2."""
import sys
import os

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from engine   import ExamEngine
from recorder import RecorderManager
from window   import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("TOEIC Speaking Test Simulator")

    # Global tooltip style — 微软雅黑 12 px, black text, no background box
    app.setStyleSheet("""
        QToolTip {
            background: transparent;
            color: #000000;
            border: none;
            font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
            font-size: 12px;
            padding: 2px 4px;
        }
    """)

    engine   = ExamEngine(BASE_DIR)
    recorder = RecorderManager(BASE_DIR)

    win = MainWindow(engine, recorder)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
