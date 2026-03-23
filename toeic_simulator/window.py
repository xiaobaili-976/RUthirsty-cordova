"""Main window — PyQt6 UI for the TOEIC Speaking Test Simulator."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QResizeEvent


# ── Shared style constants ────────────────────────────────────────────────────
_BLUE   = "#003087"
_GOLD   = "#FFD700"
_BG     = "#FFFFFF"
_LIGHT  = "#F5F7FA"
_BORDER = "#DDE3EE"
_HIGHLIGHT = "#EEF3FF"

_BTN_STYLE = f"""
QPushButton {{
    background: {_BLUE}; color: white;
    font-size: 20px; font-weight: bold;
    padding: 14px 52px; border-radius: 7px;
}}
QPushButton:hover   {{ background: #0044B3; }}
QPushButton:pressed {{ background: #002060; }}
"""

_SMALL_BTN = f"""
QPushButton {{
    background: {_BLUE}; color: white;
    font-size: 16px; font-weight: bold;
    padding: 10px 36px; border-radius: 6px;
}}
QPushButton:hover   {{ background: #0044B3; }}
"""


class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self.setWindowTitle("TOEIC Speaking Test Simulator")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 820)
        self.setStyleSheet(f"QMainWindow {{ background: {_BG}; }}")

        self._build_ui()
        self._connect_signals()
        self._show_page(self._start_page)

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._make_header())

        self._pages = QStackedWidget()
        vbox.addWidget(self._pages, 1)

        self._start_page = self._make_start_page()
        self._exam_page  = self._make_exam_page()
        self._end_page   = self._make_end_page()
        for p in (self._start_page, self._exam_page, self._end_page):
            self._pages.addWidget(p)

    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(58)
        hdr.setStyleSheet(f"background: {_BLUE};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(28, 0, 28, 0)

        title = QLabel("TOEIC\u00ae Speaking Test Simulator")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        lay.addWidget(title)
        lay.addStretch()

        self._hdr_timer = QLabel("")
        self._hdr_timer.setStyleSheet(
            f"color: {_GOLD}; font-size: 22px; font-weight: bold; min-width: 110px;"
        )
        self._hdr_timer.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        lay.addWidget(self._hdr_timer)
        return hdr

    # ── Start page ────────────────────────────────────────────────────────────
    def _make_start_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {_BG};")
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(14)

        lbl1 = QLabel("TOEIC\u00ae Speaking Test")
        lbl1.setStyleSheet(f"font-size: 46px; font-weight: bold; color: {_BLUE};")
        lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl1)

        lbl2 = QLabel("Simulator  /  模拟练习")
        lbl2.setStyleSheet("font-size: 28px; color: #666;")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl2)

        lay.addSpacing(28)

        hint = QLabel(
            "Ensure your speakers are working before starting.\n"
            "Edit  questions.json  to customise the question content.\n"
            "Place PART 2 images in the  images/  folder."
        )
        hint.setStyleSheet("font-size: 14px; color: #555; line-height: 1.6;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(hint)

        lay.addSpacing(36)

        self._start_btn = QPushButton("开始考试  /  Start Exam")
        self._start_btn.setStyleSheet(_BTN_STYLE)
        self._start_btn.clicked.connect(self._on_start)
        lay.addWidget(self._start_btn, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    # ── Exam page ─────────────────────────────────────────────────────────────
    def _make_exam_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(52, 32, 52, 0)
        lay.setSpacing(0)

        # Question title
        self._q_title = QLabel("")
        self._q_title.setStyleSheet(
            f"font-size: 21px; font-weight: bold; color: {_BLUE};"
            f"padding-bottom: 12px; border-bottom: 2px solid {_BLUE}; margin-bottom: 18px;"
        )
        self._q_title.setWordWrap(True)
        lay.addWidget(self._q_title)

        # Content stack (text vs image)
        self._content_stack = QStackedWidget()
        lay.addWidget(self._content_stack, 1)

        # — text page —
        text_page = QWidget()
        tp = QVBoxLayout(text_page)
        tp.setContentsMargins(0, 0, 0, 0)
        self._text_lbl = QLabel("")
        self._text_lbl.setStyleSheet("font-size: 19px; color: #111; line-height: 1.8;")
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._text_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        scroll = QScrollArea()
        scroll.setWidget(self._text_lbl)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        tp.addWidget(scroll)

        # — image page —
        img_page = QWidget()
        ip = QVBoxLayout(img_page)
        ip.setContentsMargins(0, 0, 0, 0)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._img_lbl.setStyleSheet(
            f"border: 1px solid {_BORDER}; background: #fafafa;"
        )
        ip.addWidget(self._img_lbl)

        self._content_stack.addWidget(text_page)   # 0 = text
        self._content_stack.addWidget(img_page)    # 1 = image
        self._current_image: str = ""

        # Secondary content (PART 3 / 4 question shown below background)
        self._sec_frame = QFrame()
        self._sec_frame.setStyleSheet(
            f"background: {_HIGHLIGHT}; border-radius: 7px; margin-top: 10px;"
        )
        sec_inner = QVBoxLayout(self._sec_frame)
        sec_inner.setContentsMargins(18, 12, 18, 12)
        self._sec_lbl = QLabel("")
        self._sec_lbl.setStyleSheet("font-size: 17px; color: #333; font-style: italic;")
        self._sec_lbl.setWordWrap(True)
        sec_inner.addWidget(self._sec_lbl)
        self._sec_frame.hide()
        lay.addWidget(self._sec_frame)

        # Timer bar
        tbar = QFrame()
        tbar.setFixedHeight(66)
        tbar.setStyleSheet(
            f"background: {_LIGHT}; border-top: 1px solid {_BORDER}; margin-top: 10px;"
        )
        tb = QHBoxLayout(tbar)
        tb.setContentsMargins(20, 0, 20, 0)

        self._phase_lbl = QLabel("")
        self._phase_lbl.setStyleSheet("font-size: 15px; color: #666;")
        tb.addWidget(self._phase_lbl)
        tb.addStretch()

        self._countdown_lbl = QLabel("")
        self._countdown_lbl.setStyleSheet(
            f"font-size: 34px; font-weight: bold; color: {_BLUE};"
        )
        tb.addWidget(self._countdown_lbl)

        lay.addWidget(tbar)
        return page

    # ── End page ─────────────────────────────────────────────────────────────
    def _make_end_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {_BG};")
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        t = QLabel("Test Complete  /  考试结束")
        t.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {_BLUE};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)

        msg = QLabel(
            "You have completed the TOEIC Speaking Test simulation.\n"
            "您已完成托业口语考试模拟测试。"
        )
        msg.setStyleSheet("font-size: 18px; color: #444;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(msg)

        lay.addSpacing(40)

        btn = QPushButton("重新开始  /  Restart")
        btn.setStyleSheet(_SMALL_BTN)
        btn.clicked.connect(self._on_restart)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    # ── Signal wiring ─────────────────────────────────────────────────────────
    def _connect_signals(self):
        self._engine.update_display.connect(self._on_display)
        self._engine.update_timer.connect(self._on_timer)
        self._engine.exam_finished.connect(self._on_end)

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_start(self):
        self._show_page(self._exam_page)
        self._engine.start_exam()

    def _on_restart(self):
        self._hdr_timer.setText("")
        self._show_page(self._start_page)

    def _on_end(self):
        self._hdr_timer.setText("")
        self._show_page(self._end_page)

    @pyqtSlot(dict)
    def _on_display(self, data: dict):
        title     = data.get("title", "")
        content   = data.get("content", "")
        secondary = data.get("secondary", "")
        image     = data.get("image", "")

        self._q_title.setText(title)

        if image:
            self._current_image = image
            self._content_stack.setCurrentIndex(1)
            self._load_image(image)
        else:
            self._current_image = ""
            self._content_stack.setCurrentIndex(0)
            self._text_lbl.setText(content)

        if secondary:
            self._sec_lbl.setText(secondary)
            self._sec_frame.show()
        else:
            self._sec_frame.hide()

    @pyqtSlot(int, str)
    def _on_timer(self, seconds: int, phase: str):
        if seconds < 0:
            self._countdown_lbl.setText("")
            self._phase_lbl.setText("")
            self._hdr_timer.setText("")
            return

        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}"

        danger = seconds <= 10
        clr = "#CC0000" if danger else _BLUE
        hclr = "#FF6060" if danger else _GOLD

        self._countdown_lbl.setText(ts)
        self._countdown_lbl.setStyleSheet(
            f"font-size: 34px; font-weight: bold; color: {clr};"
        )
        self._hdr_timer.setText(ts)
        self._hdr_timer.setStyleSheet(
            f"color: {hclr}; font-size: 22px; font-weight: bold;"
        )
        if phase:
            self._phase_lbl.setText(phase)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _show_page(self, page: QWidget):
        self._pages.setCurrentWidget(page)

    def _load_image(self, path: str):
        pm = QPixmap(path)
        if pm.isNull():
            self._content_stack.setCurrentIndex(0)
            self._text_lbl.setText(f"[Image not found: {path}]")
            return
        w = max(self._img_lbl.width() - 20, 600)
        h = max(self._img_lbl.height() - 20, 400)
        scaled = pm.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img_lbl.setPixmap(scaled)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        # Re-scale image if currently visible
        if self._content_stack.currentIndex() == 1 and self._current_image:
            self._load_image(self._current_image)
