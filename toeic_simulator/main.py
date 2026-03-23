"""Entry point for TOEIC Speaking Test Simulator."""
import sys
import os

# Determine the directory that contains questions.json / images/
# When frozen by PyInstaller:  sys.executable  points to the .exe file
# When running as a script:    __file__         points to this file
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from engine import ExamEngine
from window import MainWindow


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("TOEIC Speaking Test Simulator")

    engine = ExamEngine(BASE_DIR)
    win = MainWindow(engine)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
