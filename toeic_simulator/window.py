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
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QListWidget, QListWidgetItem,
    QDialog, QTextEdit, QMessageBox,
    QInputDialog, QLineEdit, QFileDialog,
    QDialogButtonBox, QFormLayout,
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
    font-size:14px; font-weight:bold;
    padding:4px 16px; border-radius:5px;
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
    font-size:15px; font-weight:bold;
    padding:6px 18px; border-radius:6px;
}}
QPushButton:hover   {{ background:#0044B3; }}
QPushButton:disabled{{ background:#AABBCC; color:#DDD; }}
"""
# Mark buttons — neutral state
_MARK_OFF = """
QPushButton {
    background:#F0F0F0; color:#555;
    font-size:14px; font-weight:bold;
    padding:6px 16px; border-radius:6px;
    border: 1px solid #CCC;
}
QPushButton:hover { background:#E0E0E0; }
"""
# Mark buttons — active (marked) state
_MARK_WEAK_ON = """
QPushButton {
    background:#FF6B6B; color:white;
    font-size:14px; font-weight:bold;
    padding:6px 16px; border-radius:6px;
}
QPushButton:hover { background:#E05050; }
"""
_MARK_HF_ON = """
QPushButton {
    background:#F5A623; color:white;
    font-size:14px; font-weight:bold;
    padding:6px 16px; border-radius:6px;
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
# ── Tab styles for 专项训练 page — pill buttons with bg colour ─────────────
_TAB_OFF = f"""
QPushButton {{
    background: #F0F2F5; color: {_BLUE};
    font-size: 15px; font-weight: bold;
    padding: 8px 20px; border-radius: 7px;
    border: 2px solid {_BORDER};
}}
QPushButton:hover {{ background: {_HI}; border-color: {_BLUE}; }}
"""
_TAB_ON = f"""
QPushButton {{
    background: {_BLUE}; color: white;
    font-size: 15px; font-weight: bold;
    padding: 8px 20px; border-radius: 7px;
    border: 2px solid {_BLUE};
}}
"""


def _make_gear_qicon() -> QIcon:
    """
    Gear / settings icon (24×24 canvas, 2 px white pen):
      • Outer circle — radius 9 centred at (12,12)
      • Inner circle  — radius 5 (hole)
      • 4 rectangular teeth at N / S / E / W
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
    # Outer ring
    p.drawEllipse(QRectF(3, 3, 18, 18))
    # Inner hole
    p.drawEllipse(QRectF(8, 8, 8, 8))
    # 4 teeth
    p.drawLine(11, 0, 11, 3)
    p.drawLine(13, 0, 13, 3)
    p.drawLine(11, 21, 11, 24)
    p.drawLine(13, 21, 13, 24)
    p.drawLine(0, 11, 3, 11)
    p.drawLine(0, 13, 3, 13)
    p.drawLine(21, 11, 24, 11)
    p.drawLine(21, 13, 24, 13)
    p.end()
    return QIcon(pm)


def _make_exit_qicon() -> QIcon:
    """
    Exit / close icon (24×24 canvas, 2 px white pen):
      • × shape: two diagonal lines
    """
    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawLine(5, 5, 19, 19)
    p.drawLine(19, 5, 5, 19)
    p.end()
    return QIcon(pm)


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


def _make_wave_qicon(color_hex: str = "#FFFFFF", size: int = 20) -> QIcon:
    """
    Symmetric 5-bar waveform icon for inline button use.
    Heights follow a bell curve; lines are rounded.
    """
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color_hex), 2.0, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    heights = [0.30, 0.58, 0.88, 0.58, 0.30]
    bar_w = max(2, size // 9)
    gap   = max(2, size // 7)
    n     = len(heights)
    total_w = n * bar_w + (n - 1) * gap
    x  = (size - total_w) // 2
    cy = size // 2
    for h_ratio in heights:
        h  = max(2, int(h_ratio * (size - 2)))
        y0 = cy - h // 2
        y1 = cy + h // 2
        mid = x + bar_w // 2
        p.drawLine(mid, y0, mid, y1)
        x += bar_w + gap
    p.end()
    return QIcon(pm)


def _make_mic_qicon(color_hex: str) -> QIcon:
    """
    Minimal line microphone icon, 24×24 px:
      • Rounded-rect capsule (body)
      • Semi-circle stand arc
      • Vertical stem + horizontal base
    """
    from PyQt6.QtCore import QRectF
    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color_hex), 1.8, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    # Capsule body
    p.drawRoundedRect(QRectF(8.5, 2, 7, 12), 3.5, 3.5)
    # Arc stand (bottom semicircle, centred at x=12 y=14)
    p.drawArc(QRectF(4, 8, 16, 10), 0, -180 * 16)
    # Stem
    p.drawLine(12, 18, 12, 22)
    # Base
    p.drawLine(8, 22, 16, 22)
    p.end()
    return QIcon(pm)


class _WAVPlayer:
    """Simple stop-able WAV playback in a background thread (pyaudio-based)."""

    def __init__(self):
        self._playing = False

    def play(self, wav_path: str, *, on_done=None):
        """Start playback; stops any ongoing playback first."""
        self.stop()
        self._playing = True
        threading.Thread(
            target=self._loop, args=(wav_path, on_done), daemon=True
        ).start()

    def stop(self):
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    def _loop(self, wav_path: str, on_done):
        try:
            import wave
            import pyaudio
            with wave.open(wav_path, "rb") as wf:
                pa = pyaudio.PyAudio()
                stream = pa.open(
                    format=pa.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )
                data = wf.readframes(1024)
                while data and self._playing:
                    stream.write(data)
                    data = wf.readframes(1024)
                stream.stop_stream()
                stream.close()
                pa.terminate()
        except Exception as exc:
            print(f"[WAVPlayer] {exc}")
        finally:
            self._playing = False
            if on_done:
                QTimer.singleShot(0, on_done)


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
        self._replay_display_paused: bool = False  # freeze display only during replay

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

        # Engine-selection config (lazy — needs base_dir from self._engine)
        self._scoring_cfg = None

        # [OPT-1] WAV player for recording playback
        self._wav_player = _WAVPlayer()

        # [OPT-4] Exam session tracking (for end-report)
        self._exam_start_time:       datetime | None = None
        self._exam_part_recordings:  dict = {}   # part_num(1-5) → recording count
        self._exam_is_part_mode:     bool = False
        self._exam_part_mode_num:    int  = 0

        # Activation state flag (set to True once permanently activated)
        self._activated = (
            self._license is not None
            and self._license._unlocked
            and not self._license.is_dev_mode()
            # dev mode keeps trial UI; permanent activation triggers cleanup
            and self._license._check_license_file()
        ) if self._license else False

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
        self._apply_activation_ui()   # set initial gear/exit state

        # After event loop starts: show blocking dialog if trial expired
        QTimer.singleShot(150, self._startup_check)

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
        """Legacy alias — routes to _get_active_scorer() for backward compat."""
        return self._get_active_scorer()

    # ── Engine-selection helpers ───────────────────────────────────────────────
    def _get_scoring_cfg(self):
        """Lazily create and return the ScoringEngineConfig instance."""
        if self._scoring_cfg is None:
            from scoring_engine_config import ScoringEngineConfig
            self._scoring_cfg = ScoringEngineConfig(self._engine._base_dir)
        return self._scoring_cfg

    def _get_active_scorer(self):
        """
        Return the scorer matching the currently selected engine.
        Discards and re-creates the cached scorer when the engine has changed.
        """
        engine = self._get_scoring_cfg().engine

        # Type-name map for staleness detection
        _type_for_engine = {
            "xunfei":  "VoiceScorer",
            "tencent": "TencentScorer",
            "chivox":  "ChivoxScorer",
            "local":   "LocalScorer",
        }
        if (self._voice_scorer is not None
                and type(self._voice_scorer).__name__
                    != _type_for_engine.get(engine)):
            self._voice_scorer = None   # engine changed → recreate

        if self._voice_scorer is None:
            base = self._engine._base_dir
            if engine == "xunfei":
                from voice_scorer import VoiceScorer
                self._voice_scorer = VoiceScorer(base)
            elif engine == "tencent":
                from alt_scorers import TencentScorer
                self._voice_scorer = TencentScorer(base)
            elif engine == "chivox":
                from alt_scorers import ChivoxScorer
                self._voice_scorer = ChivoxScorer(base)
            else:  # "local"
                from alt_scorers import LocalScorer
                self._voice_scorer = LocalScorer(base)

        return self._voice_scorer

    def _on_select_engine(self, engine_key: str):
        """Handle engine selection from the settings menu."""
        cfg = self._get_scoring_cfg()
        if cfg.engine == engine_key:
            return
        cfg.save(engine_key)
        self._voice_scorer = None   # force re-creation on next scoring call

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
        self._trial_lbl.hide()   # always hidden; shown only in settings dropdown

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

        lay.addSpacing(8)

        # Settings button — gear icon (pre-activation)
        self._settings_btn = QPushButton()
        self._settings_btn.setIcon(_make_gear_qicon())
        self._settings_btn.setIconSize(_ICON_SZ)
        self._settings_btn.setStyleSheet(_HDR_BTN)
        self._settings_btn.setToolTip("设置")
        self._settings_btn.clicked.connect(self._show_settings_dropdown)
        lay.addWidget(self._settings_btn)

        # Exit button — × icon (post-activation, replaces gear)
        self._exit_btn = QPushButton()
        self._exit_btn.setIcon(_make_exit_qicon())
        self._exit_btn.setIconSize(_ICON_SZ)
        self._exit_btn.setStyleSheet(_HDR_BTN)
        self._exit_btn.setToolTip("退出程序")
        self._exit_btn.clicked.connect(self.close)
        self._exit_btn.hide()
        lay.addWidget(self._exit_btn)

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

        # Main button row: Start Exam | 专项训练 (wave icon) | mic-test icon
        btn_row = QHBoxLayout()
        btn_row.setSpacing(24)
        btn_row.addStretch()

        self._confirm_btn = QPushButton("Start Exam  /  开始考试")
        self._confirm_btn.setStyleSheet(_BTN)
        self._confirm_btn.clicked.connect(self._on_confirm_set)
        btn_row.addWidget(self._confirm_btn)

        # 专项训练 button — inline waveform icon on left side
        train_btn = QPushButton("  专项训练")
        train_btn.setIcon(_make_wave_qicon("#FFFFFF", 20))
        train_btn.setIconSize(QSize(20, 20))
        train_btn.setStyleSheet(_BTN)
        train_btn.setToolTip("随机练习 / 答案速背 / 高频专练 / 薄弱巩固 / 单项集训")
        train_btn.clicked.connect(self._on_enter_review)
        btn_row.addWidget(train_btn)

        # Mic test icon button — 4 colour states (idle / testing / success / fail)
        self._mic_test_btn = QPushButton()
        self._mic_test_btn.setIcon(_make_mic_qicon("#BBBBBB"))
        self._mic_test_btn.setIconSize(QSize(22, 22))
        self._mic_test_btn.setToolTip(
            "麦克风试音\n录制 3 秒后自动回放，检测麦克风是否正常"
        )
        self._mic_test_btn.clicked.connect(self._on_mic_test)
        self._update_mic_btn_state("idle")   # apply initial style
        btn_row.addWidget(self._mic_test_btn)

        btn_row.addStretch()
        lay.addLayout(btn_row)

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
        self._text_lbl.setStyleSheet("font-size:19px; color:#111;")
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

        # [OPT-1] Replay button — enabled after recording; toggles play/stop
        tb.addSpacing(8)
        self._replay_btn = QPushButton("回放录音")
        self._replay_btn.setStyleSheet(_SKIP_BTN)
        self._replay_btn.setEnabled(False)
        self._replay_btn.setToolTip("回放最近一次录音（不影响计时）")
        self._replay_btn.clicked.connect(self._on_replay_toggle)
        tb.addWidget(self._replay_btn)

        lay.addWidget(tbar)
        return page

    # ── End page ──────────────────────────────────────────────────────────────
    def _make_end_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(80, 36, 80, 36)
        lay.setSpacing(12)

        t = QLabel("Test Complete  /  考试结束")
        t.setStyleSheet(f"font-size:38px; font-weight:bold; color:{_BLUE};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)

        # [OPT-4] Report area — rich text, scrollable
        self._report_te = QTextEdit()
        self._report_te.setReadOnly(True)
        self._report_te.setMinimumHeight(200)
        self._report_te.setStyleSheet(f"""
            QTextEdit {{
                background:{_LIGHT}; border:1px solid {_BORDER};
                border-radius:7px; font-size:14px; color:#333;
                padding:12px;
            }}
        """)
        lay.addWidget(self._report_te, 1)

        lay.addSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(16)
        row.addStretch()

        restart = QPushButton("重新选择套题  /  Choose Again")
        restart.setStyleSheet(_BTN_SM)
        restart.clicked.connect(self._on_restart)
        row.addWidget(restart)

        # [OPT-1] End-page replay button
        self._end_replay_btn = QPushButton("回放最近录音")
        self._end_replay_btn.setStyleSheet(_BTN_SM)
        self._end_replay_btn.setEnabled(False)
        self._end_replay_btn.setToolTip("回放本次考试最后一段录音")
        self._end_replay_btn.clicked.connect(self._on_end_replay_toggle)
        row.addWidget(self._end_replay_btn)

        quit_b = QPushButton("退出程序")
        quit_b.setStyleSheet(_BTN_SM)
        quit_b.clicked.connect(self.close)
        row.addWidget(quit_b)

        row.addStretch()
        lay.addLayout(row)
        return page

    # ── Review mode page [PRO-5] ──────────────────────────────────────────────
    def _make_review_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Top tab bar ────────────────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setStyleSheet(
            f"background:{_LIGHT}; border-bottom:1px solid {_BORDER};"
        )
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(24, 10, 24, 10)
        top_lay.setSpacing(10)

        # Back to home
        back_btn = QPushButton("← 返回首页")
        back_btn.setStyleSheet(_BTN_SM)
        back_btn.clicked.connect(self._on_review_home)
        top_lay.addWidget(back_btn)

        top_lay.addSpacing(12)

        # Five sub-mode tab buttons
        self._rev_mode_btns: dict = {}
        modes = [
            ("random",     "随机练习"),
            ("speed",      "答案速背"),
            ("high_freq",  "高频专练"),
            ("weak",       "薄弱巩固"),
            ("part_train", "单项集训"),
        ]
        for key, label in modes:
            btn = QPushButton(label)
            btn.setStyleSheet(_TAB_OFF)
            btn.clicked.connect(lambda _=False, k=key: self._load_review_mode(k))
            self._rev_mode_btns[key] = btn
            top_lay.addWidget(btn)

        top_lay.addStretch()

        # Question counter label
        self._rev_counter_lbl = QLabel("0 / 0")
        self._rev_counter_lbl.setStyleSheet(
            f"font-size:13px; color:{_BLUE}; font-weight:bold;"
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
        self._rev_content_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        c_lay.addWidget(self._rev_content_stack, 1)

        # text page
        rtp   = QWidget()
        rtp_l = QVBoxLayout(rtp)
        rtp_l.setContentsMargins(0, 0, 0, 0)
        self._rev_text_lbl = QLabel("")
        self._rev_text_lbl.setStyleSheet("font-size:17px; color:#111;")
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
            f"background:{_HI}; border-radius:7px; margin-top:2px;"
        )
        rsi = QVBoxLayout(self._rev_sec_frame)
        rsi.setContentsMargins(16, 10, 16, 4)
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
            f"border-radius:6px; margin-top:2px;"
        )
        raf = QVBoxLayout(self._rev_ans_frame)
        raf.setContentsMargins(12, 8, 12, 3)
        ans_title = QLabel("参考答案 / Reference Answer")
        ans_title.setStyleSheet(
            f"color:{_BLUE}; font-size:18px; font-weight:bold; border:none;"
        )
        raf.addWidget(ans_title)
        self._rev_ans_te = QTextEdit()
        self._rev_ans_te.setReadOnly(True)
        self._rev_ans_te.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._rev_ans_te.setStyleSheet(
            "background:#F8F8F8; border:none; color:#333;"
        )
        self._rev_ans_te.document().contentsChanged.connect(
            self._adjust_rev_ans_height
        )
        raf.addWidget(self._rev_ans_te)
        self._rev_ans_frame.hide()
        c_lay.addWidget(self._rev_ans_frame)

        # Small fixed gap at bottom of content area
        c_lay.addSpacing(10)

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
            "font-size:16px; color:#999;"
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
        self._replay_btn.setEnabled(False)  # [OPT-1]
        # [OPT-4] init exam tracking
        self._exam_start_time      = datetime.now()
        self._exam_part_recordings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self._exam_is_part_mode    = False
        self._exam_part_mode_num   = 0
        # show both header buttons when entering exam
        self._home_btn.show()
        self._ans_btn.show()
        self._pages.setCurrentIndex(1)
        self._engine.start_exam()

    def _on_restart(self):
        """Return from end page to set-selection."""
        self._wav_player.stop()
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

        # Stop playback
        self._wav_player.stop()

        # Abort the exam engine (stops timer / interrupts TTS)
        self._engine.abort()

        # Reset header controls
        self._home_btn.hide()
        self._ans_btn.hide()
        self._rec_dot.hide()
        self._countdown_lbl.setText("")
        self._phase_lbl.setText("")
        self._skip_btn.setEnabled(False)
        self._replay_btn.setEnabled(False)  # [OPT-1]
        self._pages.setCurrentIndex(0)

    def _on_end(self):
        self._rec_dot.hide()
        self._home_btn.hide()
        self._ans_btn.hide()
        # Enable end-page replay if there's a recording
        self._end_replay_btn.setEnabled(bool(self._last_wav_path))
        # Generate and display report
        self._report_te.setHtml(self._generate_exam_report())
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
        # Display frozen during replay; engine timer continues unaffected
        if self._replay_display_paused:
            return
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
        self._replay_btn.setEnabled(False)  # [OPT-1] disable replay during recording
        # [OPT-4] track part recordings by hint prefix "p1_", "p2_", …
        try:
            if hint and hint[0] == "p" and hint[1].isdigit():
                pn = int(hint[1])
                if 1 <= pn <= 5 and hasattr(self, "_exam_part_recordings"):
                    self._exam_part_recordings[pn] = (
                        self._exam_part_recordings.get(pn, 0) + 1
                    )
        except (IndexError, ValueError):
            pass

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
        # [OPT-1] enable replay after recording
        self._replay_btn.setEnabled(bool(self._last_wav_path))

    @pyqtSlot(str, str)
    def _on_transcription(self, wav_path: str, text: str):
        print(f"[Window] Transcript ready for {os.path.basename(wav_path)}")

    # ─────────────────────────────────────────────────────────────────────────
    # [OPT-1] Audio replay  ───────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _wav_duration(path: str) -> int:
        """Return WAV file duration in whole seconds (0 on error)."""
        try:
            import wave as _wave
            with _wave.open(path, "rb") as wf:
                return max(1, round(wf.getnframes() / wf.getframerate()))
        except Exception:
            return 0

    def _on_replay_toggle(self):
        """
        Exam-page recording playback.
        • Pauses engine timer AND freezes timer display.
        • Stops any running TTS (engine + UI).
        • Shows a modal countdown dialog: "录音回放中（N 秒）".
        • Dialog auto-closes when playback finishes; timer resumes.
        """
        # ── Stop ongoing playback ────────────────────────────────────────────
        if self._wav_player.is_playing():
            self._wav_player.stop()
            # _replay_display_paused and button text reset by _cleanup below
            return

        if not self._last_wav_path or not os.path.isfile(self._last_wav_path):
            return

        duration = self._wav_duration(self._last_wav_path)

        # ── Stop TTS + pause timer ───────────────────────────────────────────
        try:
            self._engine.tts.interrupt()
        except Exception:
            pass
        if self._ui_tts:
            self._ui_tts.interrupt()
        self._engine.pause_timer()

        # ── Freeze display ───────────────────────────────────────────────────
        self._replay_display_paused = True
        self._replay_btn.setText("停止回放")

        # ── Build countdown dialog ───────────────────────────────────────────
        dlg = QDialog(self)
        dlg.setWindowTitle("录音回放")
        dlg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
        )
        dlg.setMinimumWidth(300)
        dlg.setStyleSheet(f"QDialog {{ background:{_BG}; }}")
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(28, 22, 28, 18)
        vb.setSpacing(14)

        remaining = [duration]   # mutable for closures

        count_lbl = QLabel(f"录音回放中（{remaining[0]} 秒）")
        count_lbl.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{_BLUE};"
        )
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb.addWidget(count_lbl)

        stop_btn = QPushButton("停止回放")
        stop_btn.setStyleSheet(_BTN_SM)
        vb.addWidget(stop_btn, 0, Qt.AlignmentFlag.AlignCenter)

        # Countdown QTimer
        tick_timer = QTimer(dlg)
        tick_timer.setInterval(1000)

        def _tick():
            remaining[0] -= 1
            if remaining[0] > 0:
                count_lbl.setText(f"录音回放中（{remaining[0]} 秒）")
            else:
                tick_timer.stop()
                count_lbl.setText("回放完成")

        tick_timer.timeout.connect(_tick)

        # ── Cleanup (always called, regardless of how dialog closes) ─────────
        def _cleanup(_=None):
            tick_timer.stop()
            self._wav_player.stop()
            self._replay_display_paused = False
            self._replay_btn.setText("回放录音")
            self._engine.resume_timer()

        # on_done fires via QTimer.singleShot → runs inside dlg.exec() loop
        def _on_playback_done():
            tick_timer.stop()
            count_lbl.setText("回放完成")
            QTimer.singleShot(400, dlg.accept)

        stop_btn.clicked.connect(dlg.reject)
        dlg.finished.connect(_cleanup)

        # ── Start playback then open dialog (exec starts inner event loop) ───
        self._wav_player.play(self._last_wav_path, on_done=_on_playback_done)
        if duration > 0:
            tick_timer.start()
        dlg.exec()
        # Safety net (covers Esc / Alt-F4 close)
        self._replay_display_paused = False
        self._replay_btn.setText("回放录音")
        self._engine.resume_timer()

    def _on_end_replay_toggle(self):
        """Toggle end-page playback of the last recording."""
        if self._wav_player.is_playing():
            self._wav_player.stop()
            self._end_replay_btn.setText("回放最近录音")
        else:
            if not self._last_wav_path or not os.path.isfile(self._last_wav_path):
                return
            self._end_replay_btn.setText("停止回放")
            self._wav_player.play(
                self._last_wav_path,
                on_done=lambda: (
                    self._end_replay_btn.setText("回放最近录音")
                    if self._end_replay_btn else None
                ),
            )

    # ─────────────────────────────────────────────────────────────────────────
    # [OPT-2] Mic test  ───────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    # State colours: idle=gray, testing=blue, success=green, fail=red
    _MIC_COLORS = {
        "idle":    ("#BBBBBB", "#CCCCCC"),
        "testing": ("#5BA4CF", "#5BA4CF"),
        "success": ("#52B788", "#52B788"),
        "fail":    ("#E07070", "#E07070"),
    }

    def _update_mic_btn_state(self, state: str):
        """Update mic-test button icon colour and border to reflect state."""
        if not hasattr(self, "_mic_test_btn"):
            return
        icon_c, border_c = self._MIC_COLORS.get(state, ("#BBBBBB", "#CCCCCC"))
        self._mic_test_btn.setIcon(_make_mic_qicon(icon_c))
        self._mic_test_btn.setIconSize(QSize(22, 22))
        self._mic_test_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1.5px solid {border_c};
                border-radius: 8px;
                min-width: 42px; max-width: 42px;
                min-height: 42px; max-height: 42px;
                padding: 0px;
            }}
            QPushButton:hover {{ background: rgba(0,0,0,0.04); }}
        """)

    def _on_mic_test(self):
        """3-second mic test — record then auto-playback in an isolated dialog."""
        if not self._recorder or not self._recorder.available:
            self._update_mic_btn_state("fail")
            QMessageBox.information(
                self, "麦克风不可用",
                "未检测到麦克风或 pyaudio 未安装。\n请检查设备连接后重试。",
            )
            self._update_mic_btn_state("idle")
            return

        self._update_mic_btn_state("testing")

        dlg = QDialog(self)
        dlg.setWindowTitle("麦克风试音")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(f"QDialog {{ background:{_BG}; }}")
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(24, 20, 24, 16)
        vb.setSpacing(10)

        title_lbl = QLabel("麦克风试音检测")
        title_lbl.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{_BLUE};"
        )
        vb.addWidget(title_lbl)

        status_lbl = QLabel('点击 "开始试音" 录制 3 秒，然后自动回放。')
        status_lbl.setStyleSheet("font-size:13px; color:#555;")
        status_lbl.setWordWrap(True)
        vb.addWidget(status_lbl)

        count_lbl = QLabel("")
        count_lbl.setStyleSheet(
            f"font-size:36px; font-weight:bold; color:{_BLUE};"
        )
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_lbl.setMinimumHeight(52)
        vb.addWidget(count_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        start_btn = QPushButton("开始试音")
        start_btn.setStyleSheet(_BTN_SM)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(_BTN_SM)
        btn_row.addStretch()
        btn_row.addWidget(start_btn)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        vb.addLayout(btn_row)

        # Internal state (mutable dict so closures can mutate)
        state: dict = {"phase": "idle", "countdown": 3,
                       "wav_path": "", "qtimer": None}

        def _start():
            state["phase"] = "recording"
            state["countdown"] = 3
            start_btn.setEnabled(False)
            status_lbl.setText("正在录音中，请对着麦克风说话…")
            count_lbl.setText("3")
            self._recorder.start_recording("records/mic_test", "mic_test")
            state["wav_path"] = self._recorder._current_wav or ""
            qt = QTimer(dlg)
            state["qtimer"] = qt
            qt.setInterval(1000)

            def _tick():
                state["countdown"] -= 1
                count_lbl.setText(str(max(state["countdown"], 0)))
                if state["countdown"] <= 0:
                    qt.stop()
                    _stop_and_play()

            qt.timeout.connect(_tick)
            qt.start()

        def _stop_and_play():
            self._recorder.stop_recording()
            state["phase"] = "playing"
            status_lbl.setText("录音完成，正在回放…")
            count_lbl.setText("")
            QTimer.singleShot(600, _do_play)

        def _do_play():
            wav = state["wav_path"]
            if not wav or not os.path.isfile(wav):
                self._update_mic_btn_state("fail")
                status_lbl.setText("⚠ 录音文件未生成，请检查麦克风连接。")
                start_btn.setEnabled(True)
                state["phase"] = "idle"
                return
            self._wav_player.play(wav, on_done=_play_done)

        def _play_done():
            self._update_mic_btn_state("success")
            status_lbl.setText(
                "✓ 试音完成！若您听到了自己的声音，说明麦克风工作正常。"
            )
            count_lbl.setText("")
            start_btn.setEnabled(True)
            state["phase"] = "idle"

        def _cleanup(_=None):
            if state["phase"] == "recording":
                if state["qtimer"]:
                    state["qtimer"].stop()
                self._recorder.stop_recording()
            self._wav_player.stop()
            # Reset button to idle after dialog closes
            QTimer.singleShot(1500, lambda: self._update_mic_btn_state("idle"))

        start_btn.clicked.connect(_start)
        close_btn.clicked.connect(dlg.accept)
        dlg.finished.connect(_cleanup)
        dlg.exec()

    # ─────────────────────────────────────────────────────────────────────────
    # [OPT-3] Single-PART training  ───────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    def _on_part_training(self):
        """Show PART selection dialog then launch single-PART practice."""
        if not self._require_license():
            return
        items = self._set_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先选择一套题目。")
            return
        set_id = items[0].data(Qt.ItemDataRole.UserRole)

        dlg = QDialog(self)
        dlg.setWindowTitle("专项训练 — 选择练习部分")
        dlg.setMinimumWidth(360)
        dlg.setStyleSheet(f"QDialog {{ background:{_BG}; }}")
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(24, 20, 24, 16)
        vb.setSpacing(10)

        title_lbl = QLabel("选择要单独练习的 PART")
        title_lbl.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{_BLUE};"
        )
        vb.addWidget(title_lbl)

        hint_lbl = QLabel(
            "专项训练复用完整模考的计时规则，仅运行所选部分。"
        )
        hint_lbl.setStyleSheet("font-size:12px; color:#777;")
        hint_lbl.setWordWrap(True)
        vb.addWidget(hint_lbl)

        parts = [
            (1, "Part 1 — 朗读文章",   "Q1–2 · 45 s 准备 + 45 s 作答"),
            (2, "Part 2 — 描述图片",   "Q3–4 · 45 s 准备 + 30 s 作答"),
            (3, "Part 3 — 回答问题",   "Q5–7 · 3 s 准备 + 15/30 s 作答"),
            (4, "Part 4 — 信息问答",   "Q8–10 · 45 s 准备 + 15/30 s 作答"),
            (5, "Part 5 — 发表意见",   "Q11 · 45 s 准备 + 60 s 作答"),
        ]

        selected = [None]

        def _pick(pn):
            selected[0] = pn
            dlg.accept()

        for pnum, label, sub in parts:
            btn = QPushButton(f"{label}\n{sub}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{_LIGHT}; color:{_BLUE};
                    font-size:14px; font-weight:bold;
                    padding:10px 16px; border-radius:6px;
                    border:1.5px solid {_BORDER};
                    text-align:left;
                }}
                QPushButton:hover {{ background:{_HI}; border-color:{_BLUE}; }}
            """)
            btn.clicked.connect(lambda _=False, p=pnum: _pick(p))
            vb.addWidget(btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(_BTN_SM)
        cancel_btn.clicked.connect(dlg.reject)
        vb.addWidget(cancel_btn, 0, Qt.AlignmentFlag.AlignRight)

        dlg.exec()

        if selected[0] is not None:
            self._start_part_training(set_id, selected[0])

    def _start_part_training(self, set_id: int, part_num: int):
        """Launch the exam page in single-PART training mode."""
        self._current_answer = ""
        self._last_wav_path  = ""
        self._score_btn.setEnabled(False)
        self._replay_btn.setEnabled(False)
        self._exam_start_time      = datetime.now()
        self._exam_part_recordings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self._exam_is_part_mode    = True
        self._exam_part_mode_num   = part_num
        self._home_btn.show()
        self._ans_btn.show()
        self._pages.setCurrentIndex(1)
        self._engine.start_part_exam(set_id, part_num)

    # ─────────────────────────────────────────────────────────────────────────
    # [OPT-4] End-page exam report  ───────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    def _generate_exam_report(self) -> str:
        """Build an HTML report string for the end page."""
        lines: list[str] = []
        c = _BLUE  # accent colour

        lines.append(f'<h3 style="color:{c}; margin:0 0 10px 0;">考试结束报告</h3>')

        # ── Mode & set ────────────────────────────────────────────────────────
        if getattr(self, "_exam_is_part_mode", False):
            pn = getattr(self, "_exam_part_mode_num", 0)
            pnames = {1: "Part 1 朗读文章", 2: "Part 2 描述图片",
                      3: "Part 3 回答问题", 4: "Part 4 信息问答",
                      5: "Part 5 发表意见"}
            mode_str = f"专项训练 — {pnames.get(pn, f'Part {pn}')}"
        else:
            items = self._set_list.selectedItems()
            set_name = items[0].text().strip() if items else ""
            mode_str = f"完整模考" + (f" 「{set_name}」" if set_name else "")
        lines.append(f'<p style="margin:4px 0;"><b>训练模式：</b>{mode_str}</p>')

        # ── Elapsed time ──────────────────────────────────────────────────────
        if self._exam_start_time:
            elapsed = datetime.now() - self._exam_start_time
            total_s = int(elapsed.total_seconds())
            mins, secs = divmod(total_s, 60)
            lines.append(
                f'<p style="margin:4px 0;"><b>考试用时：</b>{mins} 分 {secs} 秒</p>'
            )

        # ── Part recording status ─────────────────────────────────────────────
        expected = {1: 2, 2: 2, 3: 3, 4: 3, 5: 1}
        pnames2 = {
            1: "Part 1 朗读文章",
            2: "Part 2 描述图片",
            3: "Part 3 回答问题",
            4: "Part 4 信息问答",
            5: "Part 5 发表意见",
        }
        lines.append('<p style="margin:8px 0 4px 0;"><b>各 PART 录音情况：</b></p>')
        lines.append('<table style="width:100%; border-spacing:0 4px;">')

        weak_parts: list[str] = []
        for pn in range(1, 6):
            # In part-mode, skip parts not involved
            if (self._exam_is_part_mode
                    and pn != self._exam_part_mode_num):
                continue
            actual = self._exam_part_recordings.get(pn, 0)
            exp    = expected[pn]
            if actual >= exp:
                badge = (f'<span style="color:green;">✓ 全部完成 '
                         f'({actual}/{exp})</span>')
            elif actual > 0:
                badge = (f'<span style="color:#E68A00;">⚠ 部分完成 '
                         f'({actual}/{exp})</span>')
                weak_parts.append(pnames2[pn])
            else:
                badge = (f'<span style="color:red;">✗ 未录音 '
                         f'(0/{exp})</span>')
                weak_parts.append(pnames2[pn])
            lines.append(
                f'<tr><td style="padding:2px 0; width:55%;">'
                f'{pnames2[pn]}</td>'
                f'<td>{badge}</td></tr>'
            )
        lines.append('</table>')

        # ── Suggestions ───────────────────────────────────────────────────────
        if weak_parts:
            wp_str = "、".join(weak_parts)
            lines.append(
                f'<p style="margin:8px 0 0 0; color:#CC4400;">'
                f'<b>建议加强：</b>{wp_str}</p>'
            )
        else:
            lines.append(
                '<p style="margin:8px 0 0 0; color:green;">'
                '<b>✓ 全部录音已完成！</b></p>'
            )

        # ── STT hint ──────────────────────────────────────────────────────────
        lines.append(
            '<p style="margin:8px 0 0 0; color:#888; font-size:12px;">'
            '录音文件已保存至 records/ 文件夹。'
        )
        if self._recorder and self._recorder.available and self._recorder._model:
            lines.append("语音转写文本已同步保存（.txt 文件）。")
        lines.append('</p>')

        return "".join(lines)

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
        """Navigate to 专项训练 page; load random mode by default."""
        if not self._require_license():
            return
        if not self._review_engine:
            QMessageBox.information(
                self, "提示",
                "专项训练功能正在初始化，请稍后重试。"
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
        # ── 单项集训: show part-selection dialog, then navigate to exam page ──
        if mode == "part_train":
            # Highlight the tab
            for k, btn in self._rev_mode_btns.items():
                btn.setStyleSheet(_TAB_ON if k == mode else _TAB_OFF)
            # Stop any ongoing TTS / recording
            if self._ui_tts:
                self._ui_tts.interrupt()
            if self._rev_recording:
                self._rev_stop_recording()
            # Show part-selection dialog (navigates to exam page on confirmation)
            self._on_part_training()
            # If user cancelled and we're still on review page, revert tab
            if self._pages.currentIndex() == 3:
                prev = self._review_mode or "random"
                for k, btn in self._rev_mode_btns.items():
                    btn.setStyleSheet(_TAB_ON if k == prev else _TAB_OFF)
            return

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

        # Update tab button styles
        for k, btn in self._rev_mode_btns.items():
            btn.setStyleSheet(_TAB_ON if k == mode else _TAB_OFF)

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

    def _adjust_rev_ans_height(self):
        """Auto-resize _rev_ans_te to fit its document content exactly."""
        doc = self._rev_ans_te.document()
        doc.adjustSize()
        h = int(doc.size().height()) + self._rev_ans_te.frameWidth() * 2 + 8
        self._rev_ans_te.setFixedHeight(max(40, h))

    def _set_rev_answer_html(self, raw: str):
        """Render answer text into the review answer QTextEdit."""
        if raw:
            escaped = _html.escape(raw).replace("\n", "<br>")
            html_body = (
                f'<p style="'
                f'font-family: Calibri, Georgia, Arial, sans-serif;'
                f'font-size: 16pt; color: #333333; line-height: 1.7; margin:0;">'
                f'{escaped}</p>'
            )
        else:
            html_body = (
                '<p style="font-family:Calibri,Arial,sans-serif;'
                'font-size:16pt;color:#888;font-style:italic;margin:0;">'
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
        """
        Entry point for voice scoring (exam page or review page).

        Timer pause/resume rules (highest priority):
          • ANY scoring-related dialog opens  → pause timer immediately
          • ANY scoring-related dialog closes → resume timer immediately
          • Zero exam-flow logic is touched
        """
        scorer = self._get_active_scorer()
        scorer._load_config()   # refresh credentials from file

        # Scenario 4: no recording file
        if not wav_path or not os.path.isfile(wav_path):
            self._engine.pause_timer()
            QMessageBox.information(self, "提示", "无有效录音，请重新录音。")
            self._engine.resume_timer()
            return

        # Scenario 1: credentials not configured → show config dialog
        if not scorer.has_credentials():
            self._engine.pause_timer()
            self._show_scorer_credentials_dialog(scorer)
            if not scorer.has_credentials():
                # User closed without saving valid credentials
                self._engine.resume_timer()
                return
            # Valid credentials saved; timer still paused → proceed to score

        else:
            # Have credentials; pause before launching request
            self._engine.pause_timer()

        btn = self.sender()
        self._do_voice_score(wav_path, answer_text, scorer, btn)

    def _do_voice_score(self, wav_path: str, answer_text: str, scorer, btn):
        """
        Show a modal "评估中" dialog and launch async scoring.
        Timer must already be paused before calling.

        Auto-retries up to _MAX_SCORE_RETRIES times on __TIMEOUT__, then
        auto-closes.  User can also manually cancel at any time.
        """
        _MAX_SCORE_RETRIES = 5
        _SCORE_TIMEOUT_SEC = 5   # matches VoiceScorer 5-second timeout

        # Stop any running TTS so the dialog is the only thing happening
        try:
            self._engine.tts.interrupt()
        except Exception:
            pass
        if self._ui_tts:
            self._ui_tts.interrupt()

        if btn:
            btn.setEnabled(False)

        # Shared mutable state across retry attempts
        state = {
            "retries":   0,       # attempts already made
            "cancelled": False,   # user clicked cancel
            "done":      False,   # async callback fired
            "result":    None,
            "error":     None,
        }

        def _launch_attempt():
            """Create a fresh dialog for one scoring attempt."""
            if state["cancelled"]:
                return

            # Reset per-attempt "done" flag so Esc detection works each round
            state["done"]   = False
            state["result"] = None
            state["error"]  = None

            attempt = state["retries"] + 1
            if attempt == 1:
                title_text = "正在评估中…"
            else:
                title_text = f"正在评估中… （第 {attempt} / {_MAX_SCORE_RETRIES} 次）"

            # ── Build dialog ───────────────────────────────────────────────
            dlg = QDialog(self)
            dlg.setWindowTitle("语音评分")
            dlg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
            )
            dlg.setModal(True)
            dlg.setMinimumWidth(320)
            dlg.setStyleSheet(f"QDialog {{ background:{_BG}; }}")
            vb = QVBoxLayout(dlg)
            vb.setContentsMargins(28, 24, 28, 18)
            vb.setSpacing(14)

            status_lbl = QLabel(title_text)
            status_lbl.setStyleSheet(
                f"font-size:16px; font-weight:bold; color:{_BLUE};"
            )
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vb.addWidget(status_lbl)

            countdown_rem = [_SCORE_TIMEOUT_SEC]
            count_lbl = QLabel(f"预计剩余 {countdown_rem[0]} 秒…")
            count_lbl.setStyleSheet("font-size:14px; color:#555;")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vb.addWidget(count_lbl)

            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet(_BTN_SM)
            vb.addWidget(cancel_btn, 0, Qt.AlignmentFlag.AlignCenter)

            # Countdown QTimer
            tick_timer = QTimer(dlg)
            tick_timer.setInterval(1000)

            def _tick():
                countdown_rem[0] -= 1
                if countdown_rem[0] > 0:
                    count_lbl.setText(f"预计剩余 {countdown_rem[0]} 秒…")
                else:
                    tick_timer.stop()
                    count_lbl.setText("等待服务器响应…")

            tick_timer.timeout.connect(_tick)
            tick_timer.start()

            # ── Async callback (fires on worker thread → route to main thread) ──
            def _callback(result, error):
                QTimer.singleShot(0, lambda: _on_main(dlg, status_lbl, count_lbl,
                                                       tick_timer, result, error))

            def _on_main(dlg, status_lbl, count_lbl, tick_timer, result, error):
                tick_timer.stop()
                state["done"]   = True
                state["result"] = result
                state["error"]  = error

                if state["cancelled"]:
                    return

                if error == "__TIMEOUT__":
                    state["retries"] += 1
                    if state["retries"] < _MAX_SCORE_RETRIES:
                        # Show "超时重试" then auto-close to trigger next attempt
                        status_lbl.setText(
                            f"超时，自动重试（第 {state['retries'] + 1} / "
                            f"{_MAX_SCORE_RETRIES} 次）…"
                        )
                        count_lbl.setText("")
                        QTimer.singleShot(800, dlg.accept)
                    else:
                        # All retries exhausted → auto-close
                        status_lbl.setText("评分超时，已达最大重试次数")
                        count_lbl.setText("自动关闭中…")
                        QTimer.singleShot(1200, dlg.reject)
                    return

                # Non-timeout result (success or error): close immediately
                dlg.accept()

            # ── Dialog finished handler ────────────────────────────────────
            def _on_finished(_code):
                tick_timer.stop()
                if state["cancelled"]:
                    # User cancelled
                    if btn:
                        btn.setEnabled(True)
                        btn.setText("语音评分")
                    self._engine.resume_timer()
                    return

                if not state["done"]:
                    # Dialog closed before async returned (e.g. Esc / Alt-F4)
                    state["cancelled"] = True
                    if btn:
                        btn.setEnabled(True)
                        btn.setText("语音评分")
                    self._engine.resume_timer()
                    return

                error  = state["error"]
                result = state["result"]

                if error == "__TIMEOUT__" and state["retries"] < _MAX_SCORE_RETRIES:
                    # Schedule next attempt after current exec() fully unwinds
                    QTimer.singleShot(100, _launch_attempt)
                    return

                # ── Final outcome ──────────────────────────────────────────
                if btn:
                    btn.setEnabled(True)
                    btn.setText("语音评分")

                if error == "__TIMEOUT__":
                    # Already shown "已达最大重试次数" inside dialog; just resume
                    self._engine.resume_timer()
                    return

                if error:
                    if "网络" in error or "oserror" in error.lower():
                        msg = "请检查网络连接，语音评分需联网使用。"
                    elif "未配置" in error:
                        msg = error
                    else:
                        msg = "评分失败，请重试。"
                    QMessageBox.warning(self, "语音评分", msg)
                    self._engine.resume_timer()
                    return

                # Success
                self._show_score_result_dialog(result)
                self._engine.resume_timer()

            def _on_user_cancel():
                state["cancelled"] = True
                tick_timer.stop()
                dlg.reject()

            cancel_btn.clicked.connect(_on_user_cancel)
            dlg.finished.connect(_on_finished)

            scorer.score_async(wav_path, answer_text, _callback)
            dlg.exec()

        _launch_attempt()

    def _show_score_result_dialog(self, result: dict):
        """Show scoring result dialog (timer must already be paused)."""
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

    def _show_xunfei_config_dialog(self, scorer):
        """Legacy wrapper — kept for backward compat; delegates to generic dialog."""
        self._show_api_config_dialog(
            scorer,
            title="讯飞 ISE 密钥配置",
            hint=(
                "请输入讯飞开放平台的 ISE 服务密钥。\n"
                "语音评分功能需要联网，其余功能不受影响。"
            ),
        )

    def _show_scorer_credentials_dialog(self, scorer) -> None:
        """
        Dispatch to the right credentials dialog for the currently selected engine.
        Timer must already be paused before calling.
        """
        engine = self._get_scoring_cfg().engine
        _titles = {
            "xunfei":  ("讯飞 ISE 密钥配置",
                        "请输入讯飞开放平台的 ISE 服务密钥。\n"
                        "语音评分功能需要联网，其余功能不受影响。"),
            "tencent": ("腾讯云智聆 密钥配置",
                        "请输入腾讯云智聆口语评测服务密钥。\n"
                        "语音评分功能需要联网，其余功能不受影响。"),
            "chivox":  ("驰声 Chivox 密钥配置",
                        "请输入驰声 Chivox 语音评测服务密钥。\n"
                        "语音评分功能需要联网，其余功能不受影响。"),
        }
        title, hint = _titles.get(
            engine,
            ("API 密钥配置", "请填写完整的 App ID、API Key 和 API Secret。"),
        )
        self._show_api_config_dialog(scorer, title, hint)

    def _show_api_config_dialog(self, scorer, title: str, hint: str) -> None:
        """
        Generic API credentials dialog (App ID / API Key / API Secret).
        Saves via scorer.save_config() on success.
        Timer must already be paused before calling.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(f"""
            QDialog {{ background:{_BG}; }}
            QLabel  {{ font-size:13px; color:#333; }}
            QLineEdit {{
                font-size:13px; padding:4px 8px;
                border:1px solid {_BORDER}; border-radius:4px;
            }}
        """)
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(20, 16, 20, 12)
        vb.setSpacing(12)

        hint_lbl = QLabel(hint)
        hint_lbl.setStyleSheet("font-size:12px; color:#666;")
        hint_lbl.setWordWrap(True)
        vb.addWidget(hint_lbl)

        form = QFormLayout()
        form.setSpacing(8)

        app_id_edit = QLineEdit(scorer.app_id)
        app_id_edit.setPlaceholderText("App ID")
        form.addRow("App ID:", app_id_edit)

        api_key_edit = QLineEdit(scorer.api_key)
        api_key_edit.setPlaceholderText("API Key")
        form.addRow("API Key:", api_key_edit)

        api_secret_edit = QLineEdit(scorer.api_secret)
        api_secret_edit.setPlaceholderText("API Secret")
        api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Secret:", api_secret_edit)

        vb.addLayout(form)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        bb.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        bb.rejected.connect(dlg.reject)
        vb.addWidget(bb)

        def _on_save():
            aid = app_id_edit.text().strip()
            ak  = api_key_edit.text().strip()
            ase = api_secret_edit.text().strip()
            if not (aid and ak and ase):
                QMessageBox.warning(
                    dlg, "密钥配置无效",
                    "请填写完整的 App ID、API Key 和 API Secret。",
                )
                dlg.reject()
                return
            scorer.save_config(aid, ak, ase)
            dlg.accept()

        bb.button(QDialogButtonBox.StandardButton.Save).clicked.connect(_on_save)
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
        # Header label always stays hidden — trial info is in the settings dropdown only

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
            self._apply_activation_ui()
            QMessageBox.information(self, "成功", "开发者模式已启用。")
        elif ok:
            QMessageBox.warning(self, "错误", "口令不正确。")

    # ─────────────────────────────────────────────────────────────────────────
    # Activation / settings UI helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _apply_activation_ui(self):
        """
        Controls header gear / exit button visibility.
        Called once on init and again after activation or dev unlock.

        Rules:
          • No license manager          → hide both (native × suffices)
          • Permanently activated       → hide both (license file present)
          • Developer mode              → keep gear (settings shows engine + exit only)
          • Trial (active or expired)   → show gear (full settings menu)
        """
        if self._license is None:
            self._settings_btn.hide()
            self._exit_btn.hide()
            return

        if self._license.is_unlocked() and self._license._check_license_file():
            # Permanently activated → no settings menu needed
            self._settings_btn.hide()
            self._exit_btn.hide()
            self._trial_lbl.hide()
        else:
            # Dev mode OR trial (active/expired) → show gear settings button
            self._settings_btn.show()
            self._exit_btn.hide()

    def _startup_check(self):
        """
        Called ~150 ms after window is shown.
        If trial has expired and software is not activated, show blocking dialog.
        """
        if self._license is None:
            return
        if self._license.is_unlocked():
            return
        if self._license.trial_remaining_seconds() <= 0:
            self._show_expired_dialog()

    def _show_expired_dialog(self):
        """
        Blocking activation-only dialog shown when trial is expired.
        Only two actions available: enter invite code OR exit.
        Closing the dialog (Alt+F4 etc.) also exits the app.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle("试用期已到期")
        # Remove close button — only our buttons can dismiss
        dlg.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(f"""
            QDialog {{ background:{_BG}; }}
            QLabel  {{ font-size:14px; color:#333; }}
        """)
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(32, 28, 32, 24)
        vb.setSpacing(14)

        icon_lbl = QLabel("⏰")
        icon_lbl.setStyleSheet("font-size:40px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb.addWidget(icon_lbl)

        title = QLabel("软件试用期已结束")
        title.setStyleSheet(f"font-size:18px; font-weight:bold; color:{_BLUE};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb.addWidget(title)

        msg = QLabel(
            "请输入邀请码以激活正版，\n"
            "或退出程序。"
        )
        msg.setStyleSheet("font-size:14px; color:#555;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb.addWidget(msg)

        vb.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        btn_row.addStretch()

        activate_btn = QPushButton("输入邀请码")
        activate_btn.setStyleSheet(_BTN_SM)
        btn_row.addWidget(activate_btn)

        quit_btn = QPushButton("退出程序")
        quit_btn.setStyleSheet(_BTN_SM)
        btn_row.addWidget(quit_btn)

        btn_row.addStretch()
        vb.addLayout(btn_row)

        def _on_activate():
            code, ok = QInputDialog.getText(
                dlg, "激活软件", "请输入邀请码（格式 BASE-XXXXXXNNN）：",
            )
            if ok and code.strip():
                success, msg_txt = self._license.activate(code)
                if success:
                    dlg.accept()
                    self._on_activation_success()
                else:
                    QMessageBox.warning(dlg, "激活失败", msg_txt)

        activate_btn.clicked.connect(_on_activate)
        quit_btn.clicked.connect(self.close)
        # Any dialog rejection (Esc, etc.) also exits
        dlg.rejected.connect(self.close)

        dlg.exec()

    def _show_settings_dropdown(self):
        """
        Gear button handler — settings popup menu.

        Trial mode:  试用时间 (disabled) | 输入邀请码 | ── | 语音评分引擎 ▶ | ── | 退出
        Dev mode:    语音评分引擎 ▶ | ── | 退出      (no trial info / invite code)
        """
        from PyQt6.QtWidgets import QMenu

        is_dev = bool(self._license and self._license.is_dev_mode())

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background:#FFFFFF; border:1px solid {_BORDER};
                border-radius:6px; padding:4px 0;
                font-size:13px;
            }}
            QMenu::item {{ padding:7px 20px; color:#333; }}
            QMenu::item:selected {{ background:{_HI}; color:{_BLUE}; }}
            QMenu::item:disabled {{ color:#AAA; }}
            QMenu::separator {{ height:1px; background:{_BORDER}; margin:4px 8px; }}
        """)

        if not is_dev:
            # Trial countdown (display-only, disabled)
            secs = self._license.trial_remaining_seconds() if self._license else 0
            h, r = divmod(secs, 3600)
            m, s = divmod(r, 60)
            trial_text = (
                f"试用期剩余 {h:02d}:{m:02d}:{s:02d}" if secs > 0 else "试用期已到期"
            )
            trial_action = menu.addAction(trial_text)
            trial_action.setEnabled(False)

            menu.addSeparator()

            activate_action = menu.addAction("输入邀请码")
            activate_action.triggered.connect(self._show_activate_dialog)

            menu.addSeparator()

        # ── Voice scoring engine submenu ──────────────────────────────────────
        from scoring_engine_config import ENGINES
        current_engine = self._get_scoring_cfg().engine

        engine_menu = menu.addMenu("语音评分引擎")
        engine_menu.setStyleSheet(menu.styleSheet())

        for key, label in ENGINES:
            act = engine_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(key == current_engine)
            act.triggered.connect(
                lambda _checked=False, k=key: self._on_select_engine(k)
            )

        menu.addSeparator()

        exit_action = menu.addAction("退出程序")
        exit_action.triggered.connect(self.close)

        # Show just below the settings button
        pos = self._settings_btn.mapToGlobal(
            self._settings_btn.rect().bottomLeft()
        )
        menu.exec(pos)

    def _show_activate_dialog(self):
        """Invite-code input dialog (from settings dropdown)."""
        if self._license is None:
            return
        code, ok = QInputDialog.getText(
            self, "激活软件", "请输入邀请码（格式 BASE-XXXXXXNNN）：",
        )
        if ok and code.strip():
            success, msg_txt = self._license.activate(code)
            if success:
                self._on_activation_success()
            else:
                QMessageBox.warning(self, "激活失败", msg_txt)

    def _on_activation_success(self):
        """Called after successful activation — update UI to activated state."""
        self._trial_timer.stop()
        self._update_trial_label()
        self._apply_activation_ui()
        QMessageBox.information(
            self, "激活成功",
            "软件已永久激活！\n感谢您的支持。"
        )
