"""
Main window — PyQt6 UI for TOEIC Speaking Test Simulator (v2).

Pages (QStackedWidget)
──────────────────────
  0 — Set-selection page    (choose which question set to practice)
  1 — Exam page             (PART 1-5, with Skip + Answer buttons)
  2 — End page              (completion summary + restart)

New exam-page elements
──────────────────────
  • Skip button  — timer bar right side; enabled only when timer is active
  • Answer button — small "?" in header bar; shows current question's answer
  • REC indicator — pulsing red dot in header while microphone is recording
  • Answer dialog  — semi-transparent overlay panel (QDialog-less)
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QListWidget, QListWidgetItem,
    QDialog, QTextEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QResizeEvent

# ── Palette ───────────────────────────────────────────────────────────────────
_BLUE   = "#003087"
_GOLD   = "#FFD700"
_RED    = "#CC0000"
_BG     = "#FFFFFF"
_LIGHT  = "#F5F7FA"
_BORDER = "#DDE3EE"
_HI     = "#EEF3FF"

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
_ANS_BTN = """
QPushButton {
    background:transparent; color:#BBDDFF;
    font-size:13px; font-weight:bold;
    padding:2px 6px; border-radius:4px;
    border: 1px solid #4477AA;
    min-width:26px; max-width:30px;
}
QPushButton:hover { background:#0044B3; color:white; }
"""


class MainWindow(QMainWindow):
    def __init__(self, engine, recorder):
        super().__init__()
        self._engine   = engine
        self._recorder = recorder
        self._current_answer = ""
        self._is_recording   = False

        self.setWindowTitle("TOEIC Speaking Test Simulator")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 820)
        self.setStyleSheet(f"QMainWindow{{background:{_BG};}}")

        self._build_ui()
        self._connect_signals()
        self._populate_sets()

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
        lay.addStretch()

        # REC indicator
        self._rec_dot = QLabel("● REC")
        self._rec_dot.setStyleSheet("color:#FF4444; font-size:13px; font-weight:bold;")
        self._rec_dot.hide()
        lay.addWidget(self._rec_dot)
        lay.addSpacing(10)

        # Answer button (subtle "?")
        self._ans_btn = QPushButton("?")
        self._ans_btn.setStyleSheet(_ANS_BTN)
        self._ans_btn.setToolTip("查看参考答案")
        self._ans_btn.clicked.connect(self._show_answer)
        self._ans_btn.hide()
        lay.addWidget(self._ans_btn)
        lay.addSpacing(12)

        # Timer display
        self._hdr_timer = QLabel("")
        self._hdr_timer.setStyleSheet(
            f"color:{_GOLD}; font-size:22px; font-weight:bold; min-width:110px;"
        )
        self._hdr_timer.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        lay.addWidget(self._hdr_timer)
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
                font-size:17px; padding:6px;
                background:white;
            }}
            QListWidget::item {{
                padding:12px 20px; border-radius:6px;
            }}
            QListWidget::item:selected {{
                background:{_BLUE}; color:white;
            }}
            QListWidget::item:hover:!selected {{
                background:{_HI};
            }}
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

        # Question title line
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
        tp    = QWidget()
        tp_l  = QVBoxLayout(tp)
        tp_l.setContentsMargins(0, 0, 0, 0)
        self._text_lbl = QLabel("")
        self._text_lbl.setStyleSheet("font-size:19px; color:#111; line-height:1.8;")
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._text_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        self._img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._img_lbl.setStyleSheet(f"border:1px solid {_BORDER}; background:#fafafa;")
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
        self._sec_lbl.setStyleSheet("font-size:17px; color:#333; font-style:italic;")
        self._sec_lbl.setWordWrap(True)
        si.addWidget(self._sec_lbl)
        self._sec_frame.hide()
        lay.addWidget(self._sec_frame)

        # Timer bar (phase label + countdown + skip button)
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

        self._countdown_lbl = QLabel("")
        self._countdown_lbl.setStyleSheet(
            f"font-size:34px; font-weight:bold; color:{_BLUE};"
        )
        tb.addWidget(self._countdown_lbl)

        tb.addSpacing(20)

        # Skip button
        self._skip_btn = QPushButton("跳过 ▶▶")
        self._skip_btn.setStyleSheet(_SKIP_BTN)
        self._skip_btn.setEnabled(False)
        self._skip_btn.clicked.connect(self._engine.skip)
        tb.addWidget(self._skip_btn)

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
        e.skip_available.connect(self._skip_btn.setEnabled)
        e.rec_start.connect(self._on_rec_start)
        e.rec_stop.connect(self._on_rec_stop)

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
        items = self._set_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先选择一套题目再开始考试。")
            return
        set_id = items[0].data(Qt.ItemDataRole.UserRole)
        self._engine.load_set(set_id)
        self._current_answer = ""
        self._pages.setCurrentIndex(1)   # exam page
        self._ans_btn.show()
        self._engine.start_exam()

    def _on_restart(self):
        self._hdr_timer.setText("")
        self._ans_btn.hide()
        self._rec_dot.hide()
        self._pages.setCurrentIndex(0)   # set-selection

    def _on_end(self):
        self._rec_dot.hide()
        self._ans_btn.hide()
        self._hdr_timer.setText("")
        # Build summary message
        set_name = ""
        items = self._set_list.selectedItems()
        if items:
            set_name = items[0].text().strip()
        msg = (f"您已完成「{set_name}」的全部题目练习。\n\n"
               "录音文件已保存至 records/ 文件夹。")
        if self._recorder and self._recorder.available and self._recorder._model:
            msg += "\n语音转写文本已同步保存（.txt 文件）。"
        elif self._recorder and self._recorder.available:
            msg += "\n（提示：将 vosk 模型放入 model/ 文件夹可启用语音转文字功能）"
        self._end_msg.setText(msg)
        self._pages.setCurrentIndex(2)   # end page

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
        if seconds < 0:
            self._countdown_lbl.setText("")
            self._phase_lbl.setText("")
            self._hdr_timer.setText("")
            return

        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}"

        danger = seconds <= 10
        self._countdown_lbl.setText(ts)
        self._countdown_lbl.setStyleSheet(
            f"font-size:34px; font-weight:bold; color:{'#CC0000' if danger else _BLUE};"
        )
        self._hdr_timer.setText(ts)
        self._hdr_timer.setStyleSheet(
            f"color:{'#FF6060' if danger else _GOLD}; font-size:22px; font-weight:bold;"
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
        # Silent — just printed to console; could optionally show notification
        print(f"[Window] Transcript ready for {os.path.basename(wav_path)}")

    # ─────────────────────────────────────────────────────────────────────────
    # Answer overlay
    # ─────────────────────────────────────────────────────────────────────────
    def _show_answer(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("参考答案")
        dlg.setMinimumWidth(540)
        dlg.setWindowFlags(
            dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        dlg.setStyleSheet(f"""
            QDialog {{ background:rgba(10,20,60,0.92); border-radius:10px; }}
            QLabel  {{ color:#DDEEFF; font-size:15px; }}
            QTextEdit {{ background:#0A1440; color:#DDEEFF; font-size:15px;
                         border:1px solid #334477; border-radius:5px; }}
        """)
        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(24, 20, 24, 16)
        vb.setSpacing(12)

        lbl = QLabel("参考答案 / Reference Answer")
        lbl.setStyleSheet(
            f"color:{_GOLD}; font-size:16px; font-weight:bold;"
        )
        vb.addWidget(lbl)

        te = QTextEdit()
        te.setReadOnly(True)
        te.setMinimumHeight(160)
        te.setText(self._current_answer if self._current_answer
                   else "（本题暂无参考答案）")
        vb.addWidget(te)

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
            pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
        )

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._content_stack.currentIndex() == 1 and self._current_image:
            self._load_image(self._current_image)


import os   # noqa: E402  (needed for _on_transcription)
