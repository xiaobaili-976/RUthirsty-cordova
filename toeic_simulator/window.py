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
    QDialog, QTextEdit, QMessageBox, QLineEdit, QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSlot, QPoint, QSize
from PyQt6.QtGui import (
    QFont, QPixmap, QResizeEvent, QKeyEvent,
    QPainter, QPen, QPolygon, QBrush, QColor, QIcon,
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
    def __init__(self, engine, recorder, license_manager=None):
        super().__init__()
        self._engine         = engine
        self._recorder       = recorder
        self._license        = license_manager
        self._base_dir       = engine._base_dir
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
    # License guard
    # ─────────────────────────────────────────────────────────────────────────
    def _require_license(self) -> bool:
        """Return True if activated (or no manager). Otherwise show purchase dialog."""
        if self._license is None or self._license.is_activated:
            return True
        self._show_purchase_dialog()
        return False

    def _show_purchase_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("购买解锁 — 基础版")
        dlg.setMinimumWidth(450)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setStyleSheet("""
            QDialog  { background: #F8F8F8; border-radius: 8px; }
            QLabel   { color: #333333; font-size: 13px; }
            QLineEdit {
                border: 1px solid #CCCCCC; border-radius: 4px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
            QPushButton {
                background: #003087; color: white;
                font-size: 13px; font-weight: bold;
                padding: 5px 20px; border-radius: 5px;
            }
            QPushButton:hover { background: #0044B3; }
            QPushButton#btn_close {
                background: #777777;
            }
            QPushButton#btn_close:hover { background: #555555; }
        """)

        vb = QVBoxLayout(dlg)
        vb.setContentsMargins(16, 14, 16, 12)
        vb.setSpacing(10)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QLabel("🔒  基础解锁版（永久授权）— ¥19.9")
        hdr.setStyleSheet(f"color:{_BLUE}; font-size:15px; font-weight:bold;")
        vb.addWidget(hdr)

        desc = QLabel(
            "解锁题库练习、录音、参考答案查看、返回首页全部基础功能。\n"
            "付款后将机器码发给开发者，收到激活码后在下方输入即可永久解锁。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "font-family: 'Microsoft YaHei', 微软雅黑, sans-serif;"
            "font-size: 13px; line-height: 1.5; color: #444;"
        )
        vb.addWidget(desc)

        # ── QR codes ──────────────────────────────────────────────────────────
        qr_row = QHBoxLayout()
        qr_row.setSpacing(24)
        qr_row.addStretch()
        for fname, pay_name in [("wechat_pay.png", "微信支付"), ("alipay_pay.png", "支付宝")]:
            col = QVBoxLayout()
            col.setSpacing(4)
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pm = QPixmap(os.path.join(self._base_dir, fname))
            if not pm.isNull():
                img_lbl.setPixmap(
                    pm.scaled(120, 120,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
                )
            else:
                img_lbl.setText(f"[ {pay_name}收款码 ]")
                img_lbl.setStyleSheet(
                    "color:#999; font-size:12px;"
                    "border:1px dashed #BBBBBB; padding:18px 10px;"
                )
            col.addWidget(img_lbl)
            name_lbl = QLabel(pay_name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet("font-size:12px; color:#555;")
            col.addWidget(name_lbl)
            qr_row.addLayout(col)
        qr_row.addStretch()
        vb.addLayout(qr_row)

        # ── Machine code ──────────────────────────────────────────────────────
        mc = self._license.machine_code if self._license else "N/A"
        mc_lbl = QLabel(f"付款备注：【机器码】{mc}")
        mc_lbl.setStyleSheet(
            "color:#CC0000; font-size:13px; font-weight:bold;"
        )
        mc_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        vb.addWidget(mc_lbl)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#DDDDDD;")
        vb.addWidget(sep)

        # ── Activation input ──────────────────────────────────────────────────
        act_row = QHBoxLayout()
        act_row.addWidget(QLabel("激活码："))
        act_input = QLineEdit()
        act_input.setPlaceholderText("BASE-XXXXXX000")
        act_input.setMaxLength(14)
        act_row.addWidget(act_input, 1)
        vb.addLayout(act_row)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        unlock_btn = QPushButton("解锁")
        unlock_btn.clicked.connect(lambda: self._do_activate(dlg, act_input))
        btn_row.addWidget(unlock_btn)
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("btn_close")
        close_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(close_btn)
        vb.addLayout(btn_row)

        dlg.exec()

    def _do_activate(self, dlg: QDialog, act_input: QLineEdit):
        code = act_input.text().strip().upper()
        if self._license and self._license.activate(code):
            QMessageBox.information(
                dlg, "解锁成功",
                "基础版已永久解锁！\n请重新点击功能按钮开始使用。"
            )
            dlg.accept()
        else:
            QMessageBox.warning(
                dlg, "激活失败",
                "激活码无效，请检查后重新输入。\n"
                f"格式：BASE-{(self._license.machine_code[-6:] if self._license else 'XXXXXX')}NNN  （NNN为3位数字）"
            )

    # ── Developer shortcut: Ctrl+Shift+T ──────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() == Qt.Key.Key_T
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
                and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self._prompt_dev_unlock()
        super().keyPressEvent(event)

    def _prompt_dev_unlock(self):
        pwd, ok = QInputDialog.getText(
            self, "开发者模式", "请输入口令：",
            QLineEdit.EchoMode.Password
        )
        if ok and self._license and self._license.enable_dev_mode(pwd):
            QMessageBox.information(self, "开发者模式", "已启用开发者模式，所有基础功能已永久解锁。")
        elif ok:
            pass   # wrong password — silent

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
        self._engine.load_set(set_id)
        self._current_answer = ""
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
        Answer popup — 450 px wide × ~180 px tall, #F8F8F8 background, 12 px padding.
        Calibri 14 pt · 1.5× line-height · #333333 text. No logic changes.
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
        vb.setContentsMargins(12, 12, 12, 10)   # 12 px inner padding
        vb.setSpacing(8)

        # Title label
        title_lbl = QLabel("参考答案 / Reference Answer")
        title_lbl.setStyleSheet(
            f"color:{_BLUE}; font-size:14px; font-weight:bold;"
        )
        vb.addWidget(title_lbl)

        # Answer text area — Calibri 14 pt, 1.5× line height via HTML
        te = QTextEdit()
        te.setReadOnly(True)
        te.setMinimumHeight(80)         # compact; scroll for long answers
        te.document().setDocumentMargin(6)

        # Build HTML with Calibri font, 1.5 line-height, dark-gray color
        raw = self._current_answer.strip() if self._current_answer else ""
        if raw:
            # Escape HTML entities and preserve newlines
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

        vb.addWidget(te)

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
