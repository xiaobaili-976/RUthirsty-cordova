"""
Main window — PyQt6 UI for TOEIC Speaking Pro.

Changes vs v3 (original preserved, incremental additions only)
──────────────────────────────────────────────────────────────
  [PRO-1] Window / app title updated to "TOEIC Speaking Pro".
  [PRO-2] Home page: two mode-entry buttons added below original button row
          (考试模拟模式 / 背诵复习模式) — original buttons fully preserved.
  [PRO-3] Exam page timer bar: 语音评分 button added right of 跳过 (disabled
          until recording stops; re-disables when new recording starts).
  [PRO-4] Answer dialog: 朗读答案 / 停止朗读 buttons added before 关闭;
          dialog close auto-stops TTS.
  [PRO-5] Review mode page (page index 3): independent 背诵复习 page with
          4 sub-modes (随机练习 / 答案速背 / 高频题专练 / 薄弱题巩固),
          per-question mark buttons (★高频 / ●薄弱), manual recording, and
          语音评分.
  [PRO-6] All original exam flow / timer / recording / TTS logic untouched.
"""
import html as _html
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QListWidget, QListWidgetItem,
    QDialog, QTextEdit, QMessageBox,
    QInputDialog, QLineEdit, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSlot, QPoint, QSize, QTimer
from PyQt6.QtGui import (
    QFont, QPixmap, QResizeEvent,
    QPainter, QPen, QPolygon, QBrush, QColor, QIcon, QKeyEvent,
)

# ── Palette ───────────────────────────────────────────────────────────────────
_BLUE   = "#003087"
_GOLD   = "#FFD700"
_BG     = "#FFFFFF"
_LIGHT  = "#F5F7FA"
_BORDER = "#DDE3EE"
_HI     = "#EEF3FF"

# ── Shared button styles ──────────────────────────────────────────────────────
_BTN = f"""
QPushButton {{
    background:{_BLUE}; color:white;
    font-size:20px; font-weight:bold;
    padding:14px 52px; border-radius:7px;
}}
QPushButton:hover   {{ background:#0044B3; }}
QPushButton:pressed {{ background:#002060; }}
QPushButton:disabled{{ background:#8899BB; }}
"""
_BTN_SM = f"""
QPushButton {{
    background:{_BLUE}; color:white;
    font-size:15px; font-weight:bold;
    padding:9px 28px; border-radius:6px;
}}
QPushButton:hover   {{ background:#0044B3; }}
QPushButton:disabled{{ background:#8899BB; }}
"""
_SKIP_BTN = """
QPushButton {
    background:#555; color:white;
    font-size:13px; font-weight:bold;
    padding:5px 16px; border-radius:5px;
    min-width:70px;
}
QPushButton:hover   { background:#333; }
QPushButton:disabled{ background:#BBB; color:#888; }
"""
# [OPT-3/4] Unified header icon-button style — flat, transparent container.
# White QPainter icons render crisply on the dark-blue header.
_HDR_BTN = """
QPushButton {
    background: transparent;
    border: none;
    padding: 3px;
    border-radius: 15px;
    min-width:  30px;
    max-width:  30px;
    min-height: 30px;
    max-height: 30px;
}
QPushButton:hover   { background: rgba(255, 255, 255, 0.18); }
QPushButton:pressed { background: rgba(0,   0,   0,   0.15); }
"""
_ICON_SZ = QSize(24, 24)   # icon canvas / display size

# [PRO] Small action button style for review mode controls
_BTN_ACT = f"""
QPushButton {{
    background:{_BLUE}; color:white;
    font-size:13px; font-weight:bold;
    padding:7px 18px; border-radius:6px;
}}
QPushButton:hover   {{ background:#0044B3; }}
QPushButton:disabled{{ background:#AABBCC; color:#DDD; }}
"""
# Mark buttons — neutral state
_MARK_OFF = """
QPushButton {
    background:#F0F0F0; color:#555;
    font-size:13px; font-weight:bold;
    padding:7px 16px; border-radius:6px;
    border: 1px solid #CCC;
}
QPushButton:hover { background:#E0E0E0; }
"""
# Mark buttons — active (marked) state
_MARK_WEAK_ON = """
QPushButton {
    background:#FF6B6B; color:white;
    font-size:13px; font-weight:bold;
    padding:7px 16px; border-radius:6px;
}
QPushButton:hover { background:#E05050; }
"""
_MARK_HF_ON = """
QPushButton {
    background:#F5A623; color:white;
    font-size:13px; font-weight:bold;
    padding:7px 16px; border-radius:6px;
}
QPushButton:hover { background:#D4901D; }
"""
# Sub-mode buttons — inactive/active
_SUB_OFF = f"""
QPushButton {{
    background:#F0F2F5; color:{_BLUE};
    font-size:15px; font-weight:bold;
    padding:10px 22px; border-radius:7px;
    border:2px solid {_BORDER};
}}
QPushButton:hover {{ background:{_HI}; }}
"""
_SUB_ON = f"""
QPushButton {{
    background:{_BLUE}; color:white;
    font-size:15px; font-weight:bold;
    padding:10px 22px; border-radius:7px;
    border:2px solid {_BLUE};
}}
"""


def _make_home_qicon() -> QIcon:
    """
    House icon (24×24 canvas, 2 px white pen):
      • Isosceles-triangle roof  — apex (12,2), base corners (1,11) / (23,11)
      • Rectangular body         — (4,11) → (20,21)
      • Door hint                — horizontal line at y=19, x 10–14
    """
    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    # Roof
    p.drawPolygon(QPolygon([QPoint(12, 2), QPoint(1, 11), QPoint(23, 11)]))
    # Body
    p.drawRect(4, 11, 16, 10)
    # Door (1-px horizontal line inside body)
    p.drawLine(10, 19, 14, 19)
    p.end()
    return QIcon(pm)


def _make_book_qicon() -> QIcon:
    """
    Book / reference icon (24×24 canvas, 2 px white pen):
      • Rounded-rect shell  — 20×20, radius 4, origin (2,2)
      • Right spine line    — x=16, y 6–18
      • Two page lines      — x 5–15, at y=10 and y=14
    """
    from PyQt6.QtCore import QRectF
    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    # Outer rounded rect
    p.drawRoundedRect(QRectF(2, 2, 20, 20), 4, 4)
    # Spine (right vertical)
    p.drawLine(16, 6, 16, 18)
    # Two page lines (horizontal)
    p.drawLine(5, 10, 15, 10)
    p.drawLine(5, 14, 15, 14)
    p.end()
    return QIcon(pm)


class MainWindow(QMainWindow):
    def __init__(self, engine, recorder, license_mgr=None,
                 marks_mgr=None, review_engine=None):
        super().__init__()
        self._engine         = engine
        self._recorder       = recorder
        self._license        = license_mgr
        self._marks_mgr      = marks_mgr        # [PRO] MarksManager
        self._review_engine  = review_engine    # [PRO] ReviewEngine
        self._current_answer = ""
        self._is_recording   = False
        self._last_wav_path  = ""               # [PRO] last WAV for voice scoring

        # [PRO] Review-mode state
        self._review_qs:     list  = []   # current question list
        self._review_idx:    int   = 0    # current position
        self._review_speed:  bool  = False  # speed mode: auto-show answer
        self._review_mode:   str   = ""     # "random"/"speed"/"high_freq"/"weak"
        self._rev_recording: bool  = False
        self._rev_last_wav:  str   = ""
        self._rev_cur_image: str   = ""

        # [PRO] Lazy TTS for UI (answer read-aloud, review TTS)
        self._ui_tts = None   # created on first use

        # [PRO] Voice scorer
        self._voice_scorer = None   # created on first use

        self.setWindowTitle("TOEIC Speaking Pro")   # [PRO-1]
        self.setMinimumSize(1024, 768)
        self.resize(1280, 820)
        self.setStyleSheet(f"QMainWindow{{background:{_BG};}}")

        self._build_ui()
        self._connect_signals()
        self._populate_sets()

        # Trial countdown timer (fires every second to refresh header label)
        self._trial_timer = QTimer(self)
        self._trial_timer.setInterval(1000)
        self._trial_timer.timeout.connect(self._update_trial_label)
        if self._license and not self._license.is_dev_mode():
            self._trial_timer.start()
        self._update_trial_label()

    # ─────────────────────────────────────────────────────────────────────────
    # Lazy helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _get_ui_tts(self):
        """Return (and lazily create) the UI TTSManager."""
        if self._ui_tts is None:
            from tts_manager import TTSManager
            self._ui_tts = TTSManager()
        return self._ui_tts

    def _get_voice_scorer(self):
        if self._voice_scorer is None:
            from voice_scorer import VoiceScorer
            self._voice_scorer = VoiceScorer()
        return self._voice_scorer

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._make_header())

        self._pages = QStackedWidget()
        vbox.addWidget(self._pages, 1)

        for page in (self._make_set_select_page(),   # 0
                     self._make_exam_page(),          # 1
                     self._make_end_page(),           # 2
                     self._make_review_page()):       # 3  [PRO-5]
            self._pages.addWidget(page)

    # ── Header ────────────────────────────────────────────────────────────────
    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(58)
        hdr.setStyleSheet(f"background:{_BLUE};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(28, 0, 16, 0)

        title = QLabel("TOEIC\u00ae Speaking Pro")   # [PRO-1]
        title.setStyleSheet("color:white; font-size:18px; font-weight:bold;")
        lay.addWidget(title)

        # Trial / license status label (shown unobtrusively near title)
        self._trial_lbl = QLabel("")
        self._trial_lbl.setStyleSheet(
            "color: rgba(255,255,200,0.85); font-size:11px;"
            "padding-left: 16px;"
        )
        lay.addWidget(self._trial_lbl)

        lay.addStretch()

        # REC indicator
        self._rec_dot = QLabel("● REC")
        self._rec_dot.setStyleSheet(
            "color:#FF4444; font-size:13px; font-weight:bold;"
        )
        self._rec_dot.hide()
        lay.addWidget(self._rec_dot)
        lay.addSpacing(14)

        # [OPT-3] Home button — house icon (QPainter-drawn), same size as answer button
        self._home_btn = QPushButton()
        self._home_btn.setIcon(_make_home_qicon())
        self._home_btn.setIconSize(_ICON_SZ)
        self._home_btn.setStyleSheet(_HDR_BTN)
        self._home_btn.setToolTip("返回主页")
        self._home_btn.clicked.connect(self._on_home)
        self._home_btn.hide()
        lay.addWidget(self._home_btn)

        lay.addSpacing(8)                         # [OPT-3] 8 px between buttons

        # [OPT-4] Answer button — book icon (QPainter-drawn), same size as home button
        self._ans_btn = QPushButton()
        self._ans_btn.setIcon(_make_book_qicon())
        self._ans_btn.setIconSize(_ICON_SZ)
        self._ans_btn.setStyleSheet(_HDR_BTN)
        self._ans_btn.setToolTip("参考答案")
        self._ans_btn.clicked.connect(self._show_answer)
        self._ans_btn.hide()
        lay.addWidget(self._ans_btn)

        lay.addSpacing(12)
        return hdr

    # ── Set-selection page ────────────────────────────────────────────────────
    def _make_set_select_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(80, 48, 80, 48)
        lay.setSpacing(16)

        t1 = QLabel("TOEIC\u00ae Speaking Pro")
        t1.setStyleSheet(f"font-size:40px; font-weight:bold; color:{_BLUE};")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t1)

        t2 = QLabel("请选择练习套题  /  Select a Question Set")
        t2.setStyleSheet("font-size:20px; color:#555;")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t2)

        lay.addSpacing(24)

        self._set_list = QListWidget()
        self._set_list.setStyleSheet(f"""
            QListWidget {{
                border:2px solid {_BORDER}; border-radius:8px;
                font-size:17px; padding:6px; background:white;
            }}
            QListWidget::item {{ padding:12px 20px; border-radius:6px; }}
            QListWidget::item:selected {{ background:{_BLUE}; color:white; }}
            QListWidget::item:hover:!selected {{ background:{_HI}; }}
        """)
        self._set_list.setMinimumHeight(200)
        self._set_list.itemDoubleClicked.connect(lambda _: self._on_confirm_set())
        lay.addWidget(self._set_list, 1)

        lay.addSpacing(24)

        # Original button row — fully preserved
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        self._confirm_btn = QPushButton("确认选择  /  Start Exam")
        self._confirm_btn.setStyleSheet(_BTN)
        self._confirm_btn.clicked.connect(self._on_confirm_set)
        btn_row.addWidget(self._confirm_btn)

        quit_btn = QPushButton("退出程序")
        quit_btn.setStyleSheet(_BTN_SM)
        quit_btn.clicked.connect(self.close)
        btn_row.addWidget(quit_btn)

        update_btn = QPushButton("更新题库")
        update_btn.setStyleSheet(_BTN_SM)
        update_btn.setToolTip("选择新的 Excel / CSV 题库文件覆盖本地题库，更新后重启生效")
        update_btn.clicked.connect(self._on_update_bank)
        btn_row.addWidget(update_btn)

        btn_row.insertStretch(0)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        # ── [PRO-2] Mode entry buttons ─────────────────────────────────────
        lay.addSpacing(24)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{_BORDER};")
        lay.addWidget(sep)

        lay.addSpacing(10)

        mode_hint = QLabel("选择练习模式  /  Choose Practice Mode")
        mode_hint.setStyleSheet("font-size:14px; color:#888;")
        mode_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(mode_hint)

        lay.addSpacing(10)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(24)
        mode_row.addStretch()

        exam_mode_btn = QPushButton("考试模拟模式")
        exam_mode_btn.setStyleSheet(_BTN)
        exam_mode_btn.clicked.connect(self._on_confirm_set)
        mode_row.addWidget(exam_mode_btn)

        review_mode_btn = QPushButton("背诵复习模式")
        review_mode_btn.setStyleSheet(_BTN)
        review_mode_btn.clicked.connect(self._on_enter_review)
        mode_row.addWidget(review_mode_btn)

        mode_row.addStretch()
        lay.addLayout(mode_row)

        return page

    # ── Exam page ─────────────────────────────────────────────────────────────
    def _make_exam_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(52, 32, 52, 0)
        lay.setSpacing(0)

        # Question title
        self._q_title = QLabel("")
        self._q_title.setStyleSheet(
            f"font-size:21px; font-weight:bold; color:{_BLUE};"
            f"padding-bottom:12px; border-bottom:2px solid {_BLUE}; margin-bottom:18px;"
        )
        self._q_title.setWordWrap(True)
        lay.addWidget(self._q_title)

        # Content stack: 0=text, 1=image
        self._content_stack = QStackedWidget()
        lay.addWidget(self._content_stack, 1)

        # — text page —
        tp   = QWidget()
        tp_l = QVBoxLayout(tp)
        tp_l.setContentsMargins(0, 0, 0, 0)
        self._text_lbl = QLabel("")
        self._text_lbl.setStyleSheet("font-size:19px; color:#111; line-height:1.8;")
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._text_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sc = QScrollArea()
        sc.setWidget(self._text_lbl)
        sc.setWidgetResizable(True)
        sc.setStyleSheet("border:none;")
        tp_l.addWidget(sc)

        # — image page —
        ip   = QWidget()
        ip_l = QVBoxLayout(ip)
        ip_l.setContentsMargins(0, 0, 0, 0)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._img_lbl.setStyleSheet(
            f"border:1px solid {_BORDER}; background:#fafafa;"
        )
        ip_l.addWidget(self._img_lbl)

        self._content_stack.addWidget(tp)   # index 0
        self._content_stack.addWidget(ip)   # index 1
        self._current_image = ""

        # Secondary content (PART3/4)
        self._sec_frame = QFrame()
        self._sec_frame.setStyleSheet(
            f"background:{_HI}; border-radius:7px; margin-top:10px;"
        )
        si = QVBoxLayout(self._sec_frame)
        si.setContentsMargins(18, 12, 18, 12)
        self._sec_lbl = QLabel("")
        self._sec_lbl.setStyleSheet(
            "font-size:17px; color:#333; font-style:italic;"
        )
        self._sec_lbl.setWordWrap(True)
        si.addWidget(self._sec_lbl)
        self._sec_frame.hide()
        lay.addWidget(self._sec_frame)

        # Timer bar: phase label | stretch | countdown | 20px | skip button | score button
        tbar = QFrame()
        tbar.setFixedHeight(66)
        tbar.setStyleSheet(
            f"background:{_LIGHT}; border-top:1px solid {_BORDER}; margin-top:10px;"
        )
        tb = QHBoxLayout(tbar)
        tb.setContentsMargins(20, 0, 20, 0)

        self._phase_lbl = QLabel("")
        self._phase_lbl.setStyleSheet("font-size:15px; color:#666;")
        tb.addWidget(self._phase_lbl)
        tb.addStretch()

        # [OPT-2] Sole canonical timer display
        self._countdown_lbl = QLabel("")
        self._countdown_lbl.setStyleSheet(
            f"font-size:34px; font-weight:bold; color:{_BLUE};"
        )
        tb.addWidget(self._countdown_lbl)

        tb.addSpacing(20)

        # [OPT-5] Skip button — enabled for both timer AND TTS phases
        self._skip_btn = QPushButton("跳过 ▶▶")
        self._skip_btn.setStyleSheet(_SKIP_BTN)
        self._skip_btn.setEnabled(False)   # disabled until exam begins
        self._skip_btn.clicked.connect(self._engine.skip)
        tb.addWidget(self._skip_btn)

        # [PRO-3] Voice scoring button — enabled only after a recording completes
        tb.addSpacing(8)
        self._score_btn = QPushButton("语音评分")
        self._score_btn.setStyleSheet(_SKIP_BTN)
        self._score_btn.setEnabled(False)
        self._score_btn.setToolTip("录音完成后可点击评分（需联网）")
        self._score_btn.clicked.connect(
            lambda: self._on_voice_score(self._last_wav_path, self._current_answer)
        )
        tb.addWidget(self._score_btn)

        lay.addWidget(tbar)
        return page

    # ── End page ──────────────────────────────────────────────────────────────
    def _make_end_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        t = QLabel("Test Complete  /  考试结束")
        t.setStyleSheet(f"font-size:42px; font-weight:bold; color:{_BLUE};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)

        self._end_msg = QLabel("")
        self._end_msg.setStyleSheet("font-size:16px; color:#444;")
        self._end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._end_msg.setWordWrap(True)
        lay.addWidget(self._end_msg)

        lay.addSpacing(40)

        row = QHBoxLayout()
        row.setSpacing(20)

        restart = QPushButton("重新选择套题  /  Choose Again")
        restart.setStyleSheet(_BTN_SM)
        restart.clicked.connect(self._on_restart)
        row.addWidget(restart)

        quit_b = QPushButton("退出程序")
        quit_b.setStyleSheet(_BTN_SM)
        quit_b.clicked.connect(self.close)
        row.addWidget(quit_b)

        lay.addLayout(row)
        return page

    # ── Review mode page [PRO-5] ──────────────────────────────────────────────
    def _make_review_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Top bar: sub-mode buttons ──────────────────────────────────────
        top_bar = QFrame()
        top_bar.setStyleSheet(
            f"background:{_LIGHT}; border-bottom:1px solid {_BORDER};"
        )
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(24, 12, 24, 12)
        top_lay.setSpacing(12)

        # Back to home (text style to match header)
        back_btn = QPushButton("← 返回首页")
        back_btn.setStyleSheet(_BTN_SM)
        back_btn.clicked.connect(self._on_review_home)
        top_lay.addWidget(back_btn)

        top_lay.addSpacing(16)

        # Sub-mode buttons
        self._rev_mode_btns: dict = {}
        modes = [
            ("random",    "随机练习"),
            ("speed",     "答案速背"),
            ("high_freq", "高频题专练"),
            ("weak",      "薄弱题巩固"),
        ]
        for key, label in modes:
            btn = QPushButton(label)
            btn.setStyleSheet(_SUB_OFF)
            btn.clicked.connect(lambda _=False, k=key: self._load_review_mode(k))
            self._rev_mode_btns[key] = btn
            top_lay.addWidget(btn)

        top_lay.addStretch()

        # Question counter label
        self._rev_counter_lbl = QLabel("0 / 0")
        self._rev_counter_lbl.setStyleSheet(
            f"font-size:14px; color:{_BLUE}; font-weight:bold;"
        )
        top_lay.addWidget(self._rev_counter_lbl)

        lay.addWidget(top_bar)

        # ── Content area ───────────────────────────────────────────────────
        content_area = QWidget()
        content_area.setStyleSheet(f"background:{_BG};")
        c_lay = QVBoxLayout(content_area)
        c_lay.setContentsMargins(52, 20, 52, 0)
        c_lay.setSpacing(0)

        # Question title
        self._rev_q_title = QLabel("")
        self._rev_q_title.setStyleSheet(
            f"font-size:19px; font-weight:bold; color:{_BLUE};"
            f"padding-bottom:10px; border-bottom:2px solid {_BLUE}; margin-bottom:14px;"
        )
        self._rev_q_title.setWordWrap(True)
        c_lay.addWidget(self._rev_q_title)

        # Part label
        self._rev_part_lbl = QLabel("")
        self._rev_part_lbl.setStyleSheet("font-size:13px; color:#888; margin-bottom:8px;")
        c_lay.addWidget(self._rev_part_lbl)

        # Content stack: 0=text, 1=image
        self._rev_content_stack = QStackedWidget()
        c_lay.addWidget(self._rev_content_stack, 1)

        # text page
        rtp   = QWidget()
        rtp_l = QVBoxLayout(rtp)
        rtp_l.setContentsMargins(0, 0, 0, 0)
        self._rev_text_lbl = QLabel("")
        self._rev_text_lbl.setStyleSheet("font-size:17px; color:#111; line-height:1.8;")
        self._rev_text_lbl.setWordWrap(True)
        self._rev_text_lbl.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._rev_text_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        rsc = QScrollArea()
        rsc.setWidget(self._rev_text_lbl)
        rsc.setWidgetResizable(True)
        rsc.setStyleSheet("border:none;")
        rtp_l.addWidget(rsc)

        # image page
        rip   = QWidget()
        rip_l = QVBoxLayout(rip)
        rip_l.setContentsMargins(0, 0, 0, 0)
        self._rev_img_lbl = QLabel()
        self._rev_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rev_img_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._rev_img_lbl.setStyleSheet(
            f"border:1px solid {_BORDER}; background:#fafafa;"
        )
        rip_l.addWidget(self._rev_img_lbl)

        self._rev_content_stack.addWidget(rtp)   # index 0
        self._rev_content_stack.addWidget(rip)   # index 1

        # Secondary frame (Part 3/4 question text)
        self._rev_sec_frame = QFrame()
        self._rev_sec_frame.setStyleSheet(
            f"background:{_HI}; border-radius:7px; margin-top:8px;"
        )
        rsi = QVBoxLayout(self._rev_sec_frame)
        rsi.setContentsMargins(16, 10, 16, 10)
        self._rev_sec_lbl = QLabel("")
        self._rev_sec_lbl.setStyleSheet(
            "font-size:15px; color:#333; font-style:italic;"
        )
        self._rev_sec_lbl.setWordWrap(True)
        rsi.addWidget(self._rev_sec_lbl)
        self._rev_sec_frame.hide()
        c_lay.addWidget(self._rev_sec_frame)

        # Answer area (hidden by default; shown in speed mode or on button click)
        self._rev_ans_frame = QFrame()
        self._rev_ans_frame.setStyleSheet(
            f"background:#F8F8F8; border:1px solid {_BORDER}; "
            f"border-radius:6px; margin-top:8px;"
        )
        raf = QVBoxLayout(self._rev_ans_frame)
        raf.setContentsMargins(12, 8, 12, 8)
        ans_title = QLabel("参考答案 / Reference Answer")
        ans_title.setStyleSheet(
            f"color:{_BLUE}; font-size:12px; font-weight:bold; border:none;"
        )
        raf.addWidget(ans_title)
        self._rev_ans_te = QTextEdit()
        self._rev_ans_te.setReadOnly(True)
        self._rev_ans_te.setMinimumHeight(80)
        self._rev_ans_te.setMaximumHeight(160)
        self._rev_ans_te.setStyleSheet(
            "background:#F8F8F8; border:none; color:#333;"
        )
        raf.addWidget(self._rev_ans_te)
        self._rev_ans_frame.hide()
        c_lay.addWidget(self._rev_ans_frame)

        lay.addWidget(content_area, 1)

        # ── Bottom control bar ─────────────────────────────────────────────
        ctrl_bar = QFrame()
        ctrl_bar.setFixedHeight(110)
        ctrl_bar.setStyleSheet(
            f"background:{_LIGHT}; border-top:1px solid {_BORDER};"
        )
        cb = QVBoxLayout(ctrl_bar)
        cb.setContentsMargins(24, 8, 24, 8)
        cb.setSpacing(6)

        # Row 1: navigation + marks
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self._rev_prev_btn = QPushButton("◀  上一题")
        self._rev_prev_btn.setStyleSheet(_BTN_ACT)
        self._rev_prev_btn.clicked.connect(self._on_review_prev)
        row1.addWidget(self._rev_prev_btn)

        self._rev_next_btn = QPushButton("下一题  ▶")
        self._rev_next_btn.setStyleSheet(_BTN_ACT)
        self._rev_next_btn.clicked.connect(self._on_review_next)
        row1.addWidget(self._rev_next_btn)

        row1.addStretch()

        self._rev_weak_btn = QPushButton("● 标记薄弱")
        self._rev_weak_btn.setStyleSheet(_MARK_OFF)
        self._rev_weak_btn.clicked.connect(self._on_toggle_weak)
        row1.addWidget(self._rev_weak_btn)

        self._rev_hf_btn = QPushButton("★ 标记高频")
        self._rev_hf_btn.setStyleSheet(_MARK_OFF)
        self._rev_hf_btn.clicked.connect(self._on_toggle_high_freq)
        row1.addWidget(self._rev_hf_btn)

        cb.addLayout(row1)

        # Row 2: answer actions + recording + scoring
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self._rev_ans_btn = QPushButton("查看答案")
        self._rev_ans_btn.setStyleSheet(_BTN_ACT)
        self._rev_ans_btn.clicked.connect(self._on_review_show_answer)
        row2.addWidget(self._rev_ans_btn)

        self._rev_tts_btn = QPushButton("朗读答案")
        self._rev_tts_btn.setStyleSheet(_BTN_ACT)
        self._rev_tts_btn.clicked.connect(self._on_review_tts_read)
        row2.addWidget(self._rev_tts_btn)

        self._rev_tts_stop_btn = QPushButton("停止朗读")
        self._rev_tts_stop_btn.setStyleSheet(_BTN_ACT)
        self._rev_tts_stop_btn.clicked.connect(self._on_review_tts_stop)
        row2.addWidget(self._rev_tts_stop_btn)

        row2.addSpacing(16)

        self._rev_rec_btn = QPushButton("▶ 开始录音")
        self._rev_rec_btn.setStyleSheet(_BTN_ACT)
        self._rev_rec_btn.clicked.connect(self._on_review_rec_toggle)
        row2.addWidget(self._rev_rec_btn)

        self._rev_score_btn = QPushButton("语音评分")
        self._rev_score_btn.setStyleSheet(_BTN_ACT)
        self._rev_score_btn.setEnabled(False)
        self._rev_score_btn.setToolTip("录音完成后可点击评分（需联网）")
        self._rev_score_btn.clicked.connect(
            lambda: self._on_voice_score(self._rev_last_wav, self._rev_current_answer())
        )
        row2.addWidget(self._rev_score_btn)

        row2.addStretch()

        # REC indicator for review
        self._rev_rec_dot = QLabel("● REC")
        self._rev_rec_dot.setStyleSheet(
            "color:#FF4444; font-size:12px; font-weight:bold;"
        )
        self._rev_rec_dot.hide()
        row2.addWidget(self._rev_rec_dot)

        cb.addLayout(row2)
        lay.addWidget(ctrl_bar)

        # Empty state label (shown when no questions are available)
        self._rev_empty_lbl = QLabel(
            "暂无题目\n\n请先在随机练习或答案速背中标记题目，\n"
            "再使用高频题专练或薄弱题巩固模式。"
        )
        self._rev_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rev_empty_lbl.setStyleSheet(
            "font-size:16px; color:#999; line-height:2;"
        )
        self._rev_empty_lbl.hide()

        return page

    # ─────────────────────────────────────────────────────────────────────────
    # Signal wiring
    # ─────────────────────────────────────────────────────────────────────────
    def _connect_signals(self):
        e = self._engine
        e.update_display.connect(self._on_display)
        e.update_timer.connect(self._on_timer)
        e.exam_finished.connect(self._on_end)
        e.answer_updated.connect(self._on_answer_updated)
        e.skip_available.connect(self._skip_btn.setEnabled)   # [OPT-5]
        e.rec_start.connect(self._on_rec_start)
        e.rec_stop.connect(self._on_rec_stop)

        if self._recorder:
            self._recorder.transcription_ready.connect(self._on_transcription)

    # ─────────────────────────────────────────────────────────────────────────
    # Slots — original exam flow (untouched)
    # ─────────────────────────────────────────────────────────────────────────
    def _populate_sets(self):
        self._set_list.clear()
        for s in self._engine.sets:
            item = QListWidgetItem(f"  {s['name']}")
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self._set_list.addItem(item)
        if self._set_list.count():
            self._set_list.setCurrentRow(0)

    def _on_confirm_set(self):
        if not self._require_license():
            return
        items = self._set_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先选择一套题目再开始考试。")
            return
        set_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._engine.load_set(set_id)
        self._current_answer = ""
        self._last_wav_path  = ""         # [PRO] reset last WAV
        self._score_btn.setEnabled(False) # [PRO] reset score button
        # show both header buttons when entering exam
        self._home_btn.show()
        self._ans_btn.show()
        self._pages.setCurrentIndex(1)
        self._engine.start_exam()

    def _on_restart(self):
        """Return from end page to set-selection."""
        self._home_btn.hide()
        self._ans_btn.hide()
        self._rec_dot.hide()
        self._pages.setCurrentIndex(0)

    def _on_home(self):
        """
        [OPT-3] Home button handler — abort exam, save recording, return to
        set-selection without any confirmation dialog.
        """
        # Stop recording first so the WAV is properly saved
        if self._is_recording:
            self._on_rec_stop()

        # Abort the exam engine (stops timer / interrupts TTS)
        self._engine.abort()

        # Reset header controls
        self._home_btn.hide()
        self._ans_btn.hide()
        self._rec_dot.hide()
        self._countdown_lbl.setText("")
        self._phase_lbl.setText("")
        self._skip_btn.setEnabled(False)
        self._pages.setCurrentIndex(0)

    def _on_end(self):
        self._rec_dot.hide()
        self._home_btn.hide()
        self._ans_btn.hide()
        set_name = ""
        items = self._set_list.selectedItems()
        if items:
            set_name = items[0].text().strip()
        msg = (f"您已完成「{set_name}」的全部题目练习。\n\n"
               "录音文件已保存至 records/ 文件夹。")
        if self._recorder and self._recorder.available and self._recorder._model:
            msg += "\n语音转写文本已同步保存（.txt 文件）。"
        elif self._recorder and self._recorder.available:
            msg += ("\n（提示：将 vosk 模型放入 model/ 文件夹可启用"
                    "语音转文字功能）")
        self._end_msg.setText(msg)
        self._pages.setCurrentIndex(2)

    @pyqtSlot(dict)
    def _on_display(self, data: dict):
        self._q_title.setText(data.get("title", ""))
        image = data.get("image", "")
        if image:
            self._current_image = image
            self._content_stack.setCurrentIndex(1)
            self._load_image(image)
        else:
            self._current_image = ""
            self._content_stack.setCurrentIndex(0)
            self._text_lbl.setText(data.get("content", ""))

        sec = data.get("secondary", "")
        if sec:
            self._sec_lbl.setText(sec)
            self._sec_frame.show()
        else:
            self._sec_frame.hide()

    @pyqtSlot(int, str)
    def _on_timer(self, seconds: int, phase: str):
        """[OPT-2] Timer updates only the bottom bar — no header label."""
        if seconds < 0:
            self._countdown_lbl.setText("")
            self._phase_lbl.setText("")
            return

        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}"

        danger = seconds <= 10
        self._countdown_lbl.setText(ts)
        self._countdown_lbl.setStyleSheet(
            f"font-size:34px; font-weight:bold; "
            f"color:{'#CC0000' if danger else _BLUE};"
        )
        if phase:
            self._phase_lbl.setText(phase)

    @pyqtSlot(str)
    def _on_answer_updated(self, text: str):
        self._current_answer = text

    @pyqtSlot(str, str)
    def _on_rec_start(self, subdir: str, hint: str):
        if self._recorder:
            self._recorder.start_recording(subdir, hint)
        self._rec_dot.show()
        self._is_recording   = True
        self._score_btn.setEnabled(False)   # [PRO] disable while recording

    @pyqtSlot()
    def _on_rec_stop(self):
        if self._recorder:
            self._recorder.stop_recording()
            # [PRO] capture last WAV path for voice scoring
            if hasattr(self._recorder, "_current_wav") and self._recorder._current_wav:
                self._last_wav_path = self._recorder._current_wav
        self._rec_dot.hide()
        self._is_recording = False
        # [PRO] enable voice scoring after recording
        if self._last_wav_path:
            self._score_btn.setEnabled(True)

    @pyqtSlot(str, str)
    def _on_transcription(self, wav_path: str, text: str):
        print(f"[Window] Transcript ready for {os.path.basename(wav_path)}")

    # ─────────────────────────────────────────────────────────────────────────
    # Answer dialog  [OPT-1 + PRO-4]
    # ─────────────────────────────────────────────────────────────────────────
    def _show_answer(self):
        """
        Answer popup — 800 px wide, #F8F8F8 background, 12 px padding.
        Shows reference answer in Calibri 14pt · 1.5× line-height · #333333.
        [PRO-4] 朗读答案 / 停止朗读 buttons added at bottom.
        """
        if not self._require_license():
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("参考答案")
        dlg.setMinimumWidth(800)
        dlg.resize(800, 360)
        dlg.setWindowFlags(
            dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        dlg.setStyleSheet("""
            QDialog {
                background: #F8F8F8;
                border-radius: 8px;
            }
            QLabel {
                color: #555555;
                font-size: 13px;
            }
            QTextEdit {
                background: #F8F8F8;
                border: 1px solid #DDDDDD;
                border-radius: 5px;
                color: #333333;
                selection-background-color: #AACCEE;
            }
            QPushButton {
                background: #003087; color: white;
                font-size: 13px; font-weight: bold;
                padding: 5px 22px; border-radius: 5px;
            }
            QPushButton:hover { background: #0044B3; }
        """)

        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(12, 12, 12, 10)
        vb.setSpacing(8)

        # Title label
        title_lbl = QLabel("参考答案 / Reference Answer")
        title_lbl.setStyleSheet(
            f"color:{_BLUE}; font-size:14px; font-weight:bold;"
        )
        vb.addWidget(title_lbl)

        te = QTextEdit()
        te.setReadOnly(True)
        te.setMinimumHeight(80)
        te.document().setDocumentMargin(6)

        raw = self._current_answer.strip() if self._current_answer else ""
        if raw:
            escaped = _html.escape(raw).replace("\n", "<br>")
            html_body = (
                f'<p style="'
                f'font-family: Calibri, Georgia, Arial, sans-serif;'
                f'font-size: 14pt;'
                f'color: #333333;'
                f'line-height: 1.5;'
                f'margin: 0;'
                f'text-align: left;'
                f'">{escaped}</p>'
            )
        else:
            html_body = (
                '<p style="'
                'font-family: Calibri, Georgia, Arial, sans-serif;'
                'font-size: 14pt; color: #888888; font-style: italic; '
                'line-height: 1.5; margin: 0;">'
                '（本题暂无参考答案）</p>'
            )
        te.setHtml(html_body)
        vb.addWidget(te)

        # [PRO-4] Bottom button row: TTS controls + close
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        tts_read_btn = QPushButton("朗读答案")
        btn_row.addWidget(tts_read_btn)

        tts_stop_btn = QPushButton("停止朗读")
        btn_row.addWidget(tts_stop_btn)

        btn_row.addStretch()

        close = QPushButton("关闭")
        close.clicked.connect(dlg.accept)
        btn_row.addWidget(close)

        vb.addLayout(btn_row)

        # Wire TTS actions
        ui_tts = self._get_ui_tts()
        tts_read_btn.clicked.connect(lambda: ui_tts.speak(raw) if raw else None)
        tts_stop_btn.clicked.connect(ui_tts.interrupt)
        dlg.finished.connect(lambda _: ui_tts.interrupt())

        dlg.exec()

    # ─────────────────────────────────────────────────────────────────────────
    # Review mode — page navigation  [PRO-5]
    # ─────────────────────────────────────────────────────────────────────────
    def _on_enter_review(self):
        """Navigate to review page; load random mode by default."""
        if not self._require_license():
            return
        if not self._review_engine:
            QMessageBox.information(
                self, "提示",
                "背诵复习功能正在初始化，请稍后重试。"
            )
            return
        # Stop any review TTS before entering
        if self._ui_tts:
            self._ui_tts.interrupt()
        self._home_btn.hide()
        self._ans_btn.hide()
        self._rec_dot.hide()
        self._pages.setCurrentIndex(3)
        # Default: random mode
        self._load_review_mode("random")

    def _on_review_home(self):
        """Return from review page to set-selection."""
        if self._ui_tts:
            self._ui_tts.interrupt()
        # Stop review recording if active
        if self._rev_recording:
            self._rev_stop_recording()
        self._pages.setCurrentIndex(0)

    def _load_review_mode(self, mode: str):
        """Load question list for the given sub-mode and show first question."""
        self._review_mode  = mode
        self._review_speed = (mode == "speed")

        if not self._review_engine:
            return

        if mode == "random":
            qs = self._review_engine.get_random_questions()
        elif mode == "speed":
            qs = self._review_engine.get_all_questions()
        elif mode == "high_freq":
            if not self._marks_mgr:
                QMessageBox.information(
                    self, "提示", "标记功能不可用，请重启软件。"
                )
                return
            qs = self._review_engine.get_high_freq_questions(self._marks_mgr)
        elif mode == "weak":
            if not self._marks_mgr:
                QMessageBox.information(
                    self, "提示", "标记功能不可用，请重启软件。"
                )
                return
            qs = self._review_engine.get_weak_questions(self._marks_mgr)
        else:
            qs = self._review_engine.get_random_questions()

        # Update sub-mode button styles
        for k, btn in self._rev_mode_btns.items():
            btn.setStyleSheet(_SUB_ON if k == mode else _SUB_OFF)

        if not qs:
            self._review_qs  = []
            self._review_idx = 0
            self._rev_counter_lbl.setText("0 / 0")
            self._rev_q_title.setText("暂无题目")
            self._rev_part_lbl.setText("")
            self._rev_text_lbl.setText(
                "本模式暂无题目。\n请先在随机练习或答案速背中"
                "使用 ★标记高频 / ●标记薄弱 标记题目后再使用此模式。"
            )
            self._rev_content_stack.setCurrentIndex(0)
            self._rev_sec_frame.hide()
            self._rev_ans_frame.hide()
            self._rev_prev_btn.setEnabled(False)
            self._rev_next_btn.setEnabled(False)
            return

        self._review_qs  = qs
        self._review_idx = 0
        self._show_review_question()

    def _show_review_question(self):
        """Render the current review question (self._review_idx)."""
        if not self._review_qs:
            return

        q   = self._review_qs[self._review_idx]
        tot = len(self._review_qs)

        self._rev_counter_lbl.setText(f"{self._review_idx + 1} / {tot}")
        self._rev_q_title.setText(q["title"])
        self._rev_part_lbl.setText(q["part_label"])

        # Content
        image = q.get("image", "")
        if image:
            self._rev_cur_image = image
            self._rev_content_stack.setCurrentIndex(1)
            self._load_rev_image(image)
        else:
            self._rev_cur_image = ""
            self._rev_content_stack.setCurrentIndex(0)
            self._rev_text_lbl.setText(q.get("content", ""))

        # Secondary (Part 3/4)
        sec = q.get("secondary", "")
        if sec:
            self._rev_sec_lbl.setText(sec)
            self._rev_sec_frame.show()
        else:
            self._rev_sec_frame.hide()

        # Answer area
        raw = (q.get("answer") or "").strip()
        if self._review_speed:
            # Speed mode: always show answer
            self._set_rev_answer_html(raw)
            self._rev_ans_frame.show()
        else:
            self._rev_ans_frame.hide()

        # Navigation buttons
        self._rev_prev_btn.setEnabled(self._review_idx > 0)
        self._rev_next_btn.setEnabled(self._review_idx < tot - 1)

        # Mark button states
        self._update_mark_buttons(q["id"])

        # Reset recording state for this question
        self._rev_score_btn.setEnabled(bool(self._rev_last_wav))

    def _set_rev_answer_html(self, raw: str):
        """Render answer text into the review answer QTextEdit."""
        if raw:
            escaped = _html.escape(raw).replace("\n", "<br>")
            html_body = (
                f'<p style="'
                f'font-family: Calibri, Georgia, Arial, sans-serif;'
                f'font-size: 13pt; color: #333333; line-height: 1.5; margin:0;">'
                f'{escaped}</p>'
            )
        else:
            html_body = (
                '<p style="font-family:Calibri,Arial,sans-serif;'
                'font-size:13pt;color:#888;font-style:italic;margin:0;">'
                '（本题暂无参考答案）</p>'
            )
        self._rev_ans_te.setHtml(html_body)

    def _rev_current_answer(self) -> str:
        """Return the answer text of the currently displayed review question."""
        if self._review_qs and 0 <= self._review_idx < len(self._review_qs):
            return self._review_qs[self._review_idx].get("answer", "")
        return ""

    def _update_mark_buttons(self, qid: str):
        """Update ★/● button styles to reflect current mark state."""
        if not self._marks_mgr:
            self._rev_weak_btn.setEnabled(False)
            self._rev_hf_btn.setEnabled(False)
            return
        is_w  = self._marks_mgr.is_weak(qid)
        is_hf = self._marks_mgr.is_high_freq(qid)
        self._rev_weak_btn.setStyleSheet(_MARK_WEAK_ON if is_w  else _MARK_OFF)
        self._rev_hf_btn.setStyleSheet(_MARK_HF_ON   if is_hf else _MARK_OFF)

    # ── Review navigation ─────────────────────────────────────────────────────
    def _on_review_prev(self):
        if self._review_idx > 0:
            # Stop TTS before navigating
            if self._ui_tts:
                self._ui_tts.interrupt()
            self._review_idx -= 1
            self._show_review_question()

    def _on_review_next(self):
        if self._review_idx < len(self._review_qs) - 1:
            if self._ui_tts:
                self._ui_tts.interrupt()
            self._review_idx += 1
            self._show_review_question()

    # ── Review marks ──────────────────────────────────────────────────────────
    def _on_toggle_weak(self):
        if not self._marks_mgr or not self._review_qs:
            return
        qid = self._review_qs[self._review_idx]["id"]
        is_now = self._marks_mgr.toggle_weak(qid)
        self._rev_weak_btn.setStyleSheet(_MARK_WEAK_ON if is_now else _MARK_OFF)

    def _on_toggle_high_freq(self):
        if not self._marks_mgr or not self._review_qs:
            return
        qid = self._review_qs[self._review_idx]["id"]
        is_now = self._marks_mgr.toggle_high_freq(qid)
        self._rev_hf_btn.setStyleSheet(_MARK_HF_ON if is_now else _MARK_OFF)

    # ── Review answer ─────────────────────────────────────────────────────────
    def _on_review_show_answer(self):
        """Toggle answer visibility in review mode."""
        if self._rev_ans_frame.isVisible():
            self._rev_ans_frame.hide()
        else:
            raw = self._rev_current_answer().strip()
            self._set_rev_answer_html(raw)
            self._rev_ans_frame.show()

    # ── Review TTS ────────────────────────────────────────────────────────────
    def _on_review_tts_read(self):
        raw = self._rev_current_answer().strip()
        if not raw:
            QMessageBox.information(self, "提示", "本题暂无参考答案可朗读。")
            return
        self._get_ui_tts().speak(raw)

    def _on_review_tts_stop(self):
        if self._ui_tts:
            self._ui_tts.interrupt()

    # ── Review recording ──────────────────────────────────────────────────────
    def _on_review_rec_toggle(self):
        if self._rev_recording:
            self._rev_stop_recording()
        else:
            self._rev_start_recording()

    def _rev_start_recording(self):
        if not self._recorder or not self._recorder.available:
            QMessageBox.information(
                self, "录音不可用",
                "未检测到麦克风或 pyaudio 未安装。"
            )
            return
        if not self._review_qs:
            return
        q   = self._review_qs[self._review_idx]
        subdir = f"records/review/set_{q['set_id']}"
        hint   = f"rev_{q['id'].replace(':', '_')}"
        self._recorder.start_recording(subdir, hint)
        self._rev_recording = True
        self._rev_rec_dot.show()
        self._rev_rec_btn.setText("■ 停止录音")
        self._rev_score_btn.setEnabled(False)

    def _rev_stop_recording(self):
        if self._recorder:
            self._recorder.stop_recording()
            if hasattr(self._recorder, "_current_wav") and self._recorder._current_wav:
                self._rev_last_wav = self._recorder._current_wav
        self._rev_recording = False
        self._rev_rec_dot.hide()
        self._rev_rec_btn.setText("▶ 开始录音")
        if self._rev_last_wav:
            self._rev_score_btn.setEnabled(True)

    # ─────────────────────────────────────────────────────────────────────────
    # Voice scoring  [PRO-3 / PRO-5]
    # ─────────────────────────────────────────────────────────────────────────
    def _on_voice_score(self, wav_path: str, answer_text: str):
        """Trigger async voice scoring and show result dialog."""
        if not wav_path:
            QMessageBox.information(self, "提示", "录音文件不存在，请先完成录音。")
            return

        scorer = self._get_voice_scorer()

        # Disable button while scoring
        sender_btn = self.sender()
        if sender_btn:
            sender_btn.setEnabled(False)
            sender_btn.setText("评分中…")

        def _callback(result, error):
            # Restore button on main thread
            QTimer.singleShot(0, lambda: self._on_score_result(
                result, error, sender_btn
            ))

        scorer.score_async(wav_path, answer_text, _callback)

    def _on_score_result(self, result, error, btn):
        """Show scoring result dialog (called on main thread)."""
        if btn:
            btn.setEnabled(True)
            btn.setText("语音评分")

        if error:
            QMessageBox.warning(self, "语音评分", error)
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("语音评分结果")
        dlg.setMinimumWidth(360)
        dlg.setStyleSheet(f"""
            QDialog {{ background:{_BG}; }}
            QLabel  {{ font-size:14px; color:#333; }}
        """)
        vb = QVBoxLayout(dlg)
        vb.setSpacing(10)
        vb.setContentsMargins(24, 20, 24, 16)

        title = QLabel("语音评分结果  /  Score Report")
        title.setStyleSheet(f"font-size:16px; font-weight:bold; color:{_BLUE};")
        vb.addWidget(title)

        scores = [
            ("发音准确度  Pronunciation",  result.get("pronunciation", 0)),
            ("流利度  Fluency",            result.get("fluency",       0)),
            ("内容完整性  Completeness",   result.get("completeness",  0)),
            ("综合得分  Overall",          result.get("overall",       0)),
        ]
        for label, score in scores:
            row = QHBoxLayout()
            lbl = QLabel(label)
            sc  = QLabel(f"{score:.1f}")
            sc.setStyleSheet(
                f"font-size:22px; font-weight:bold; color:{_BLUE};"
            )
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(sc)
            vb.addLayout(row)

        close = QPushButton("关闭")
        close.setStyleSheet(_BTN_SM)
        close.clicked.connect(dlg.accept)
        vb.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)

        dlg.exec()

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _load_image(self, path: str):
        pm = QPixmap(path)
        if pm.isNull():
            self._content_stack.setCurrentIndex(0)
            self._text_lbl.setText(f"[Image not found: {path}]")
            return
        w = max(self._img_lbl.width() - 20, 600)
        h = max(self._img_lbl.height() - 20, 400)
        self._img_lbl.setPixmap(
            pm.scaled(w, h,
                      Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
        )

    def _load_rev_image(self, path: str):
        """Load image for review content stack."""
        import os as _os
        if not _os.path.isabs(path):
            from engine import ExamEngine  # noqa: F401 (just to get base_dir)
            path = _os.path.join(self._engine._base_dir, path)
        pm = QPixmap(path)
        if pm.isNull():
            self._rev_content_stack.setCurrentIndex(0)
            self._rev_text_lbl.setText(f"[Image not found: {path}]")
            return
        w = max(self._rev_img_lbl.width() - 20, 500)
        h = max(self._rev_img_lbl.height() - 20, 350)
        self._rev_img_lbl.setPixmap(
            pm.scaled(w, h,
                      Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
        )

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._content_stack.currentIndex() == 1 and self._current_image:
            self._load_image(self._current_image)
        if (self._pages.currentIndex() == 3
                and self._rev_content_stack.currentIndex() == 1
                and self._rev_cur_image):
            self._load_rev_image(self._rev_cur_image)

    def keyPressEvent(self, event: QKeyEvent):
        """Ctrl+Shift+T → developer unlock dialog."""
        if (event.modifiers() == (Qt.KeyboardModifier.ControlModifier
                                   | Qt.KeyboardModifier.ShiftModifier)
                and event.key() == Qt.Key.Key_T):
            self._on_dev_unlock()
        else:
            super().keyPressEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # License / trial helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _require_license(self) -> bool:
        """Return True if user may proceed (dev mode or trial active)."""
        if self._license is None:
            return True
        if self._license.is_unlocked():
            return True
        QMessageBox.warning(
            self, "试用期已到期",
            "软件试用期已结束，感谢您的使用。\n\n请联系开发者获取授权。",
        )
        return False

    def _update_trial_label(self):
        """Refresh the trial countdown label in the header."""
        if self._license is None:
            self._trial_lbl.hide()
            return
        if self._license.is_dev_mode():
            self._trial_lbl.hide()
            return
        secs = self._license.trial_remaining_seconds()
        if secs <= 0:
            self._trial_lbl.setText("试用已到期")
            self._trial_lbl.setStyleSheet(
                "color: #FF8888; font-size:11px; padding-left:16px;"
            )
            self._trial_timer.stop()
        else:
            h, r = divmod(secs, 3600)
            m, s = divmod(r, 60)
            self._trial_lbl.setText(
                f"试用期剩余 {h:02d}:{m:02d}:{s:02d}"
            )
            self._trial_lbl.setStyleSheet(
                "color: rgba(255,255,200,0.85); font-size:11px; padding-left:16px;"
            )
        self._trial_lbl.show()

    def _on_update_bank(self):
        """更新题库：选择 Excel/CSV 文件覆盖本地题库，重启后生效。"""
        import shutil
        path, _ = QFileDialog.getOpenFileName(
            self, "选择新题库文件", "",
            "题库文件 (*.xlsx *.csv);;所有文件 (*)"
        )
        if not path:
            return
        base = self._engine._base_dir
        ext  = os.path.splitext(path)[1].lower()
        if ext == ".xlsx":
            dest = os.path.join(base, "question_bank.xlsx")
        else:
            dest = os.path.join(base, "question_bank.csv")
        try:
            shutil.copy2(path, dest)
            QMessageBox.information(
                self, "题库更新成功",
                f"题库已更新为：\n{os.path.basename(path)}\n\n请重启软件使新题库生效。"
            )
        except Exception as exc:
            QMessageBox.warning(self, "更新失败", f"文件复制失败：{exc}")

    def _on_dev_unlock(self):
        """Ctrl+Shift+T handler — prompt for developer password."""
        if self._license is None:
            return
        if self._license.is_dev_mode():
            QMessageBox.information(self, "开发者模式", "已处于开发者模式。")
            return
        pwd, ok = QInputDialog.getText(
            self, "开发者模式", "请输入开发口令：",
            QLineEdit.EchoMode.Password,
        )
        if ok and self._license.unlock_dev(pwd):
            self._trial_timer.stop()
            self._update_trial_label()
            QMessageBox.information(self, "成功", "开发者模式已启用。")
        elif ok:
            QMessageBox.warning(self, "错误", "口令不正确。")
