"""
Main window — PyQt6 UI for TOEIC Speaking Test Simulator (v3).

Changes vs v2
─────────────
  • [OPT-1] Answer dialog: Calibri 14 pt, 1.5 × line-height, 10 px padding,
            dark-gray text (#333), light near-white background — no harsh borders.
  • [OPT-2] Header redundant timer removed; single canonical timer lives in the
            bottom timer-bar only.
  • [OPT-3] Home button (⌂) added to header, same size as "?" button, 8 px gap,
            tooltip "返回主页". Click: saves recording, aborts exam, returns to
            set-selection page.
  • [OPT-4] Answer "?" button now has consistent tooltip "参考答案" (was already
            present but now guaranteed visible via Qt.ToolTipRole).
  • [OPT-5] Skip button always enabled during exam (engine emits skip_available=True
            for both timer AND TTS steps; Method-2 interrupt logic in engine/tts).
"""
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QListWidget, QListWidgetItem,
    QDialog, QTextEdit, QMessageBox, QTabWidget, QLineEdit,
    QInputDialog, QFileDialog, QMenuBar,
)
from PyQt6.QtCore import Qt, pyqtSlot, QPoint, QSize, QTimer
from PyQt6.QtGui import (
    QFont, QPixmap, QResizeEvent,
    QPainter, QPen, QPolygon, QBrush, QColor, QIcon, QKeyEvent,
    QAction,
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
    def __init__(self, engine, recorder,
                 license_mgr=None, mistake_book=None,
                 score_analyzer=None, template_mgr=None):
        super().__init__()
        self._engine         = engine
        self._recorder       = recorder
        self._license        = license_mgr
        self._mistakes       = mistake_book
        self._scorer         = score_analyzer
        self._templates      = template_mgr
        self._current_answer = ""
        self._is_recording   = False

        # Tracking state for scoring / mistake book
        self._current_part   = ""     # "Part1" … "Part5"
        self._current_q_num  = 0      # 1-based question index within current part
        self._current_set_id = 0
        self._current_text   = ""     # question text for mistake book

        self.setWindowTitle("TOEIC Speaking Test Simulator")
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

        for page in (self._make_set_select_page(),
                     self._make_exam_page(),
                     self._make_end_page()):
            self._pages.addWidget(page)

        self._make_menu_bar()

    # ── Header ────────────────────────────────────────────────────────────────
    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(58)
        hdr.setStyleSheet(f"background:{_BLUE};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(28, 0, 16, 0)

        title = QLabel("TOEIC\u00ae Speaking Test Simulator")
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
        # [OPT-2] _hdr_timer REMOVED — canonical timer is in the bottom bar only.
        return hdr

    # ── Set-selection page ────────────────────────────────────────────────────
    def _make_set_select_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(80, 48, 80, 48)
        lay.setSpacing(16)

        t1 = QLabel("TOEIC\u00ae Speaking Test")
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

        btn_row.insertStretch(0)
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

        # Timer bar: phase label | stretch | countdown | 20px | skip button
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

        # [OPT-2] Sole canonical timer display lives here (header timer removed)
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

        tb.addSpacing(8)

        # Mark-mistake button — flags current question to mistake book
        self._mark_btn = QPushButton("★ 错题")
        self._mark_btn.setStyleSheet("""
            QPushButton {
                background: #7A3900; color: white;
                font-size: 12px; font-weight: bold;
                padding: 5px 12px; border-radius: 5px;
                min-width: 60px;
            }
            QPushButton:hover   { background: #A85000; }
            QPushButton:checked { background: #CC6600; }
            QPushButton:disabled{ background: #BBB; color: #888; }
        """)
        self._mark_btn.setCheckable(True)
        self._mark_btn.setEnabled(False)
        self._mark_btn.clicked.connect(self._on_mark_mistake)
        tb.addWidget(self._mark_btn)

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

        # Additional connections for scoring + mistake book
        e.update_display.connect(self._on_display_track)
        e.rec_start.connect(self._on_rec_start_score_track)
        e.rec_stop.connect(self._on_rec_stop_score_show)
        e.skip_available.connect(self._mark_btn.setEnabled)

        if self._recorder:
            self._recorder.transcription_ready.connect(self._on_transcription)

    # ─────────────────────────────────────────────────────────────────────────
    # Slots
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
        self._current_set_id = set_id
        self._engine.load_set(set_id)
        self._current_answer = ""
        self._mark_btn.setEnabled(False)
        self._mark_btn.setChecked(False)
        # [OPT-3] show both header buttons when entering exam
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
        if not self._require_license():
            return
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
        self._is_recording = True

    @pyqtSlot()
    def _on_rec_stop(self):
        if self._recorder:
            self._recorder.stop_recording()
        self._rec_dot.hide()
        self._is_recording = False

    @pyqtSlot(str, str)
    def _on_transcription(self, wav_path: str, text: str):
        print(f"[Window] Transcript ready for {os.path.basename(wav_path)}")

    # ─────────────────────────────────────────────────────────────────────────
    # Answer dialog  [OPT-1]
    # ─────────────────────────────────────────────────────────────────────────
    def _show_answer(self):
        """
        Answer popup — 800×360px, #F8F8F8 background, 12 px padding.
        Tab 1: 参考答案 (Calibri 14pt · 1.5× line-height · #333333)
        Tab 2: 高分模板 (TemplateManager content for current part)
        Popup / close logic unchanged.
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
            QTabWidget::pane { border: 1px solid #DDDDDD; }
            QTabBar::tab {
                background: #E8ECF5; color: #333;
                padding: 5px 16px; border-radius: 3px 3px 0 0;
                font-size: 12px;
            }
            QTabBar::tab:selected { background: #003087; color: white; }
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

        # Tab widget: Tab1=answer, Tab2=templates
        tabs = QTabWidget()
        vb.addWidget(tabs)

        # ── Tab 1: 参考答案 ───────────────────────────────────────────────────
        te = QTextEdit()
        te.setReadOnly(True)
        te.setMinimumHeight(80)
        te.document().setDocumentMargin(6)

        raw = self._current_answer.strip() if self._current_answer else ""
        if raw:
            import html as _html
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
        tabs.addTab(te, "参考答案")

        # ── Tab 2: 高分模板 ───────────────────────────────────────────────────
        tpl_widget = QWidget()
        tpl_layout = QVBoxLayout(tpl_widget)
        tpl_layout.setContentsMargins(4, 4, 4, 4)
        tpl_layout.setSpacing(4)

        part = self._current_part or "Part1"
        templates = self._templates.get_templates(part) if self._templates else []
        if templates:
            for tpl in templates:
                tpl_te = QTextEdit()
                tpl_te.setReadOnly(True)
                tpl_te.document().setDocumentMargin(6)
                import html as _html2
                tpl_content = _html2.escape(tpl.get("content", "")).replace("\n", "<br>")
                tpl_html = (
                    f'<p style="font-family: Calibri, Arial, sans-serif; '
                    f'font-size: 13pt; color: #222222; line-height: 1.5; margin: 0;">'
                    f'<b>{_html2.escape(tpl.get("title",""))}</b><br><br>'
                    f'{tpl_content}</p>'
                )
                tpl_te.setHtml(tpl_html)
                tpl_layout.addWidget(tpl_te)
        else:
            no_tpl = QTextEdit()
            no_tpl.setReadOnly(True)
            no_tpl.setPlainText("（暂无模板，可在 answer_templates.json 中添加）")
            tpl_layout.addWidget(no_tpl)

        tabs.addTab(tpl_widget, f"高分模板 · {part}")

        close = QPushButton("关闭")
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

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._content_stack.currentIndex() == 1 and self._current_image:
            self._load_image(self._current_image)

    def keyPressEvent(self, event: QKeyEvent):
        """Ctrl+Shift+T → developer unlock dialog."""
        if (event.modifiers() == (Qt.KeyboardModifier.ControlModifier
                                   | Qt.KeyboardModifier.ShiftModifier)
                and event.key() == Qt.Key.Key_T):
            self._on_dev_unlock()
        else:
            super().keyPressEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # License / trial helpers  (NEW)
    # ─────────────────────────────────────────────────────────────────────────
    def _require_license(self) -> bool:
        """Return True if user may proceed; False after showing purchase dialog."""
        if self._license is None:
            return True                          # no manager → open access
        if self._license.is_unlocked():
            return True
        self._show_purchase_dialog()
        return False

    def _update_trial_label(self):
        """Refresh the trial countdown label in the header."""
        if self._license is None:
            self._trial_lbl.hide()
            return
        if self._license.is_dev_mode():
            self._trial_lbl.setText("[ 开发者模式 ]")
            self._trial_lbl.show()
            return
        if self._license._unlocked:
            self._trial_lbl.setText("已激活 · 终身专业版")
            self._trial_lbl.show()
            self._trial_timer.stop()
            return
        secs = self._license.trial_remaining_seconds()
        if secs <= 0:
            self._trial_lbl.setText("试用已到期 — 请激活")
            self._trial_lbl.setStyleSheet(
                "color: #FF8888; font-size:11px; padding-left:16px;"
            )
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

    def _show_purchase_dialog(self):
        """Show purchase / activation dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle("软件激活 — TOEIC 终身专业版")
        dlg.setMinimumWidth(520)
        dlg.resize(520, 480)
        dlg.setStyleSheet("""
            QDialog    { background: #F8F8F8; }
            QLabel     { color: #333; font-size: 13px; }
            QLineEdit  { border: 1px solid #CCC; border-radius:4px;
                         padding: 5px; font-size:13px; }
            QPushButton {
                background:#003087; color:white;
                font-size:13px; font-weight:bold;
                padding:6px 20px; border-radius:5px;
            }
            QPushButton:hover { background:#0044B3; }
            QPushButton#cancel {
                background:#888;
            }
            QPushButton#cancel:hover { background:#666; }
        """)

        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(24, 20, 24, 16)
        vb.setSpacing(10)

        title_lbl = QLabel("🔒  TOEIC 终身专业版  —  永久解锁")
        title_lbl.setStyleSheet(
            f"color:{_BLUE}; font-size:16px; font-weight:bold;"
        )
        vb.addWidget(title_lbl)

        secs = self._license.trial_remaining_seconds() if self._license else 0
        if secs <= 0:
            status_txt = "试用期已到期，请购买并输入激活码以继续使用全部功能。"
        else:
            h, r = divmod(secs, 3600)
            m, _s = divmod(r, 60)
            status_txt = f"当前剩余试用时间：{h:02d}:{m:02d} — 激活后永久使用。"
        status_lbl = QLabel(status_txt)
        status_lbl.setWordWrap(True)
        vb.addWidget(status_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#DDD;")
        vb.addWidget(sep)

        # Payment QR images
        qr_row = QHBoxLayout()
        for fname, name in [("wechat_pay.png", "微信支付"),
                             ("alipay_pay.png", "支付宝")]:
            qr_col = QVBoxLayout()
            pm_path = os.path.join(self._license._base_dir, fname) \
                      if self._license else fname
            lbl_img = QLabel()
            lbl_img.setFixedSize(120, 120)
            lbl_img.setStyleSheet("border:1px solid #CCC; background:#FFF;")
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.isfile(pm_path):
                pm = QPixmap(pm_path).scaled(
                    118, 118,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                lbl_img.setPixmap(pm)
            else:
                lbl_img.setText(f"[{name}\n收款码]")
                lbl_img.setStyleSheet(
                    "border:1px solid #CCC; background:#FFF;"
                    "font-size:11px; color:#999;"
                )
            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_col.addWidget(lbl_img)
            qr_col.addWidget(name_lbl)
            qr_row.addLayout(qr_col)

        price_lbl = QLabel("¥19.9  永久解锁")
        price_lbl.setStyleSheet(
            "color:#CC3300; font-size:18px; font-weight:bold;"
        )
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_row.addWidget(price_lbl)
        vb.addLayout(qr_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#DDD;")
        vb.addWidget(sep2)

        # Machine code display
        mc_lbl = QLabel("您的机器码（付款备注给开发者）：")
        vb.addWidget(mc_lbl)
        mc_code = self._license.machine_code if self._license else "N/A"
        mc_edit = QLineEdit(mc_code)
        mc_edit.setReadOnly(True)
        mc_edit.setStyleSheet(
            "background:#EEF; border:1px solid #AAA;"
            "font-family:Consolas,monospace; font-size:12px; padding:4px;"
        )
        vb.addWidget(mc_edit)

        # Activation code input
        ac_lbl = QLabel("激活码（格式：BASE-XXXXXX000）：")
        vb.addWidget(ac_lbl)
        ac_edit = QLineEdit()
        ac_edit.setPlaceholderText("BASE-XXXXXX000")
        vb.addWidget(ac_edit)

        # Buttons
        btn_row = QHBoxLayout()
        activate_btn = QPushButton("立即激活")
        cancel_btn   = QPushButton("取消")
        cancel_btn.setObjectName("cancel")
        btn_row.addStretch()
        btn_row.addWidget(activate_btn)
        btn_row.addWidget(cancel_btn)
        vb.addLayout(btn_row)

        cancel_btn.clicked.connect(dlg.reject)

        def _do_activate():
            code = ac_edit.text().strip()
            if not code:
                QMessageBox.warning(dlg, "提示", "请输入激活码。")
                return
            ok, msg = self._license.activate(code)
            if ok:
                self._update_trial_label()
                QMessageBox.information(dlg, "激活成功", msg)
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "激活失败", msg)

        activate_btn.clicked.connect(_do_activate)
        ac_edit.returnPressed.connect(_do_activate)
        dlg.exec()

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
            self._update_trial_label()
            QMessageBox.information(self, "成功", "开发者模式已启用。")
        elif ok:
            QMessageBox.warning(self, "错误", "口令不正确。")

    # ─────────────────────────────────────────────────────────────────────────
    # Tracking slots  (NEW — additive, no existing slots modified)
    # ─────────────────────────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def _on_display_track(self, data: dict):
        """
        Shadow slot for update_display — extracts part/q_num/text for scoring
        and updates the mark button's checked state.
        """
        title = data.get("title", "")
        # Parse question number from title like "Question 2 of 11"
        import re
        m = re.search(r"Question\s+(\d+)\s+of\s+11", title, re.IGNORECASE)
        if m:
            q_num = int(m.group(1))
            self._current_q_num = q_num
            # Map question number to part
            if   q_num <= 2:  self._current_part = "Part1"
            elif q_num <= 4:  self._current_part = "Part2"
            elif q_num <= 7:  self._current_part = "Part3"
            elif q_num <= 10: self._current_part = "Part4"
            else:             self._current_part = "Part5"
        self._current_text = data.get("content", "") or data.get("secondary", "")

        # Update mark button
        if self._mistakes and self._current_q_num:
            marked = self._mistakes.is_marked(
                self._current_set_id, self._current_part, self._current_q_num
            )
            self._mark_btn.setChecked(marked)

        # Begin scoring session
        if self._scorer and self._current_q_num and self._current_part:
            key = f"p{self._current_part[-1]}_q{self._current_q_num}"
            prep_map  = {"Part1": 45, "Part2": 45, "Part3": 3,
                          "Part4": 3,  "Part5": 45}
            resp_map  = {"Part1": 45, "Part2": 30, "Part3": 15,
                          "Part4": 15, "Part5": 60}
            # Q7 and Q10 have longer response time
            if self._current_q_num == 7:
                resp_map["Part3"] = 30
            if self._current_q_num == 10:
                resp_map["Part4"] = 30
            self._scorer.begin_question(
                key, self._current_part,
                prep_map.get(self._current_part, 30),
                resp_map.get(self._current_part, 30),
            )
            self._scorer.on_prep_start()

    @pyqtSlot(str, str)
    def _on_rec_start_score_track(self, subdir: str, hint: str):
        """Shadow slot for rec_start — marks response start for scoring."""
        if self._scorer:
            key = f"p{self._current_part[-1] if self._current_part else '1'}_q{self._current_q_num}"
            self._scorer.on_resp_start(key)
        self._mark_btn.setEnabled(bool(self._current_q_num))

    @pyqtSlot()
    def _on_rec_stop_score_show(self):
        """Shadow slot for rec_stop — computes score and shows popup."""
        if not self._scorer or not self._current_q_num:
            return
        key = f"p{self._current_part[-1] if self._current_part else '1'}_q{self._current_q_num}"
        self._scorer.on_resp_end(key)
        score = self._scorer.get_score(key)
        if score:
            self._show_score_popup(score)

    def _show_score_popup(self, score: dict):
        """Non-blocking score result popup."""
        dlg = QDialog(self)
        dlg.setWindowTitle("本题评分")
        dlg.setFixedWidth(420)
        dlg.setWindowFlags(
            dlg.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        dlg.setStyleSheet("""
            QDialog { background:#F8F8F8; }
            QLabel  { color:#333; font-size:13px; }
        """)
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(18, 16, 18, 12)
        vb.setSpacing(8)

        final   = score.get("final", 0)
        band    = score.get("band", "")
        ref_rng = score.get("ref_range", "")
        wpm     = score.get("wpm", 0)

        score_lbl = QLabel(
            f'<span style="font-size:32px; font-weight:bold; color:{_BLUE};">'
            f'{final}</span>'
            f'<span style="font-size:14px; color:#555;"> / 100 &nbsp;&nbsp;'
            f'{band} &nbsp; {ref_rng}</span>'
        )
        score_lbl.setTextFormat(Qt.TextFormat.RichText)
        vb.addWidget(score_lbl)

        detail_lbl = QLabel(
            f"准备使用: {score.get('prep_score',0)}  ·  "
            f"作答时长: {score.get('resp_score',0)}  ·  "
            f"流利度: {score.get('fluency_score',0)}"
            + (f"  ·  {wpm} WPM" if wpm else "")
        )
        detail_lbl.setStyleSheet("color:#666; font-size:12px;")
        vb.addWidget(detail_lbl)

        suggestions = score.get("suggestions", [])
        if suggestions:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color:#DDD;")
            vb.addWidget(sep)
            for tip in suggestions:
                tip_lbl = QLabel(f"• {tip}")
                tip_lbl.setWordWrap(True)
                tip_lbl.setStyleSheet("color:#444; font-size:12px;")
                vb.addWidget(tip_lbl)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(
            "background:#003087; color:white; font-size:12px;"
            "padding:4px 16px; border-radius:4px;"
        )
        close_btn.clicked.connect(dlg.accept)
        vb.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

        # Non-blocking: use show() + auto-close after 8 s
        dlg.show()
        QTimer.singleShot(8000, dlg.accept)

    def _on_mark_mistake(self):
        """Toggle current question in/out of mistake book."""
        if not self._mistakes or not self._current_q_num:
            return
        marked = self._mistakes.toggle(
            self._current_set_id,
            self._current_part,
            self._current_q_num,
            self._current_text,
            self._current_answer,
        )
        self._mark_btn.setChecked(marked)

    def _show_mistake_book_dialog(self):
        """Show all mistakes in a dialog with optional Excel export."""
        if not self._require_license():
            return
        if self._mistakes is None:
            QMessageBox.information(self, "错题本", "错题本功能不可用。")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("错题本")
        dlg.resize(740, 480)
        dlg.setStyleSheet("""
            QDialog { background:#F8F8F8; }
            QLabel  { color:#333; font-size:13px; }
            QPushButton {
                background:#003087; color:white;
                font-size:13px; font-weight:bold;
                padding:5px 18px; border-radius:5px;
            }
            QPushButton:hover { background:#0044B3; }
            QPushButton#close_btn { background:#888; }
            QPushButton#close_btn:hover { background:#666; }
        """)

        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(16, 14, 16, 12)
        vb.setSpacing(8)

        hdr = QLabel(
            f"错题本  —  共 {self._mistakes.count()} 题"
        )
        hdr.setStyleSheet(f"color:{_BLUE}; font-size:15px; font-weight:bold;")
        vb.addWidget(hdr)

        entries = self._mistakes.all_entries()
        te = QTextEdit()
        te.setReadOnly(True)
        te.document().setDocumentMargin(8)
        import html as _html
        rows_html = ""
        for e in entries:
            rows_html += (
                f'<p style="margin:0 0 10px 0;">'
                f'<b style="color:{_BLUE};">'
                f'套题{e["set_id"]} · {e["part"]} · Q{e["q_num"]}</b><br>'
                f'{_html.escape(e.get("text","") or "")}' + (
                    f'<br><i style="color:#555;">'
                    f'答：{_html.escape(e.get("answer","") or "")}</i>'
                    if e.get("answer") else ""
                ) +
                f'</p>'
            )
        if not rows_html:
            rows_html = '<p style="color:#888; font-style:italic;">暂无错题记录</p>'
        te.setHtml(
            f'<div style="font-family:Calibri,Arial,sans-serif; font-size:13pt;">'
            f'{rows_html}</div>'
        )
        vb.addWidget(te)

        btn_row = QHBoxLayout()
        export_btn = QPushButton("导出 Excel")
        close_btn  = QPushButton("关闭")
        close_btn.setObjectName("close_btn")
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        vb.addLayout(btn_row)

        close_btn.clicked.connect(dlg.accept)

        def _export():
            path, _ = QFileDialog.getSaveFileName(
                dlg, "导出错题本", "mistake_book_export.xlsx",
                "Excel Files (*.xlsx)",
            )
            if path:
                try:
                    self._mistakes.export_xlsx(path)
                    QMessageBox.information(dlg, "导出成功", f"已保存至:\n{path}")
                except Exception as exc:
                    QMessageBox.critical(dlg, "导出失败", str(exc))

        export_btn.clicked.connect(_export)
        dlg.exec()

    # ─────────────────────────────────────────────────────────────────────────
    # Menu bar  (NEW)
    # ─────────────────────────────────────────────────────────────────────────
    def _make_menu_bar(self):
        """Add menu bar with premium feature shortcuts."""
        mb = self.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background:{_BLUE}; color:white; font-size:13px;
                padding: 2px 8px;
            }}
            QMenuBar::item:selected {{ background: rgba(255,255,255,0.2); }}
            QMenu {{
                background:#F8F8F8; color:#333;
                border:1px solid #CCC; font-size:13px;
            }}
            QMenu::item:selected {{ background:{_BLUE}; color:white; }}
        """)

        tools_menu = mb.addMenu("功能")

        act_mistakes = QAction("错题本", self)
        act_mistakes.setShortcut("Ctrl+M")
        act_mistakes.triggered.connect(self._show_mistake_book_dialog)
        tools_menu.addAction(act_mistakes)

        tools_menu.addSeparator()

        act_update = QAction("题库一键更新…", self)
        act_update.triggered.connect(self._stub_bank_update)
        tools_menu.addAction(act_update)

        act_sync = QAction("多设备数据同步…", self)
        act_sync.triggered.connect(self._stub_device_sync)
        tools_menu.addAction(act_sync)

        tools_menu.addSeparator()

        act_activate = QAction("软件激活 / 购买…", self)
        act_activate.triggered.connect(self._show_purchase_dialog)
        tools_menu.addAction(act_activate)

    def _stub_bank_update(self):
        QMessageBox.information(
            self, "题库一键更新",
            "该功能需要连接更新服务器。\n\n"
            "敬请期待后续版本。如有需要请联系开发者获取最新题库文件。",
        )

    def _stub_device_sync(self):
        QMessageBox.information(
            self, "多设备数据同步",
            "该功能需要云端账号系统。\n\n"
            "敬请期待后续版本。当前可通过手动复制以下文件在设备间同步：\n"
            "• mistake_book.json（错题本）\n"
            "• toeic_license.dat（授权文件）",
        )
