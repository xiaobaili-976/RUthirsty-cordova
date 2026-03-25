"""
Palette and QSS constants for HR Manager.
All UI files import from here to ensure a single source of truth.
"""

# ── Colour palette ────────────────────────────────────────────────────────────
_BLUE      = "#003087"
_BLUE_MID  = "#005C99"
_BLUE_LIGHT = "#E8F0FE"
_GOLD      = "#FFD700"
_BG        = "#FFFFFF"
_LIGHT     = "#F5F7FA"
_BORDER    = "#DDE3EE"
_TEXT      = "#222222"
_TEXT_SEC  = "#555555"

_RED       = "#C0392B"
_RED_LIGHT = "#FDECEA"
_GREEN     = "#27AE60"
_GREEN_LIGHT = "#E9F7EF"
_YELLOW    = "#F39C12"
_YELLOW_LIGHT = "#FEF9E7"

RISK_COLOR = {
    "green":  _GREEN,
    "yellow": _YELLOW,
    "red":    _RED,
}
RISK_BG = {
    "green":  _GREEN_LIGHT,
    "yellow": _YELLOW_LIGHT,
    "red":    _RED_LIGHT,
}

# ── Employee type colors ───────────────────────────────────────────────────────
EMP_TYPE_BORDER = {
    "华为": "#2ECC71",
    "OD":   "#3498DB",
    "外包": "#F39C12",
    "":     "#AAB4C8",
}
EMP_TYPE_BG = {
    "华为": "#E8F5E9",
    "OD":   "#E3F2FD",
    "外包": "#FFF3E0",
    "":     "#F5F7FA",
}

# ── Navigation bar (new design) ───────────────────────────────────────────────
NAV_HEIGHT  = 80
NAV_BG      = "#F7F8FA"
NAV_ACTIVE  = "#165DFF"
NAV_INACTIVE = "#86909C"
NAV_HOVER   = "#4080FF"

NAV_QSS = f"""
    QWidget#NavBar {{
        background: {NAV_BG};
        border-bottom: 1px solid #E0E4EA;
    }}
"""
NAV_TAB_QSS = ""   # kept for backward compat

# ── Sidebar ───────────────────────────────────────────────────────────────────
SIDEBAR_QSS = f"""
    QWidget#Sidebar {{
        background: {_LIGHT};
        border-right: 1px solid {_BORDER};
    }}
    QLineEdit#SearchBox {{
        border: 1px solid {_BORDER};
        border-radius: 14px;
        padding: 5px 12px;
        background: white;
        font-size: 12px;
    }}
"""

# ── Cards ─────────────────────────────────────────────────────────────────────
CARD_QSS = f"""
    QFrame.card {{
        background: white;
        border: 1px solid {_BORDER};
        border-radius: 12px;
    }}
"""

# ── Buttons ───────────────────────────────────────────────────────────────────
BTN_PRIMARY = f"""
    QPushButton {{
        background: {_BLUE};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 7px 18px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: #004bb5; }}
    QPushButton:pressed {{ background: #002060; }}
    QPushButton:disabled {{ background: #aab4c8; }}
"""

BTN_SECONDARY = f"""
    QPushButton {{
        background: white;
        color: {_BLUE};
        border: 1px solid {_BLUE};
        border-radius: 12px;
        padding: 6px 16px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: {_BLUE_LIGHT}; }}
    QPushButton:pressed {{ background: #d0dcf5; }}
"""

BTN_DANGER = f"""
    QPushButton {{
        background: white;
        color: {_RED};
        border: 1px solid {_RED};
        border-radius: 12px;
        padding: 6px 16px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: {_RED_LIGHT}; }}
"""

# ── Table ─────────────────────────────────────────────────────────────────────
TABLE_QSS = f"""
    QTableWidget {{
        background: white;
        border: 1px solid {_BORDER};
        border-radius: 12px;
        gridline-color: {_BORDER};
        font-size: 12px;
    }}
    QTableWidget::item {{ padding: 6px 10px; }}
    QTableWidget::item:selected {{
        background: {_BLUE_LIGHT};
        color: {_BLUE};
    }}
    QHeaderView::section {{
        background: {_LIGHT};
        color: {_TEXT_SEC};
        border: none;
        border-right: 1px solid {_BORDER};
        border-bottom: 1px solid {_BORDER};
        padding: 7px 10px;
        font-weight: bold;
        font-size: 12px;
    }}
"""

# ── Form inputs ───────────────────────────────────────────────────────────────
INPUT_QSS = f"""
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        border: 1px solid {_BORDER};
        border-radius: 5px;
        padding: 6px 10px;
        background: white;
        font-size: 13px;
        color: {_TEXT};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {_BLUE};
    }}
    QDateEdit {{
        border: 1px solid {_BORDER};
        border-radius: 5px;
        padding: 4px 28px 4px 10px;
        background: white;
        font-size: 13px;
        color: {_TEXT};
        min-height: 24px;
    }}
    QDateEdit:focus {{
        border-color: {_BLUE};
    }}
    QDateEdit::drop-down {{
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 24px;
        border-left: 1px solid {_BORDER};
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
        background: {_LIGHT};
    }}
    QDateEdit::drop-down:hover {{
        background: {_BLUE_LIGHT};
    }}
    QDateEdit::down-arrow {{
        width: 10px;
        height: 10px;
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background: {_BLUE};
        border-radius: 6px 6px 0 0;
    }}
    QCalendarWidget QToolButton {{
        color: white;
        background: transparent;
        border: none;
        font-size: 13px;
        padding: 4px 8px;
    }}
    QCalendarWidget QToolButton:hover {{
        background: rgba(255,255,255,0.15);
        border-radius: 4px;
    }}
    QCalendarWidget QSpinBox {{
        color: white;
        background: transparent;
        border: none;
        font-size: 13px;
    }}
    QCalendarWidget QAbstractItemView:enabled {{
        font-size: 12px;
        color: {_TEXT};
        background: white;
        selection-background-color: {_BLUE};
        selection-color: white;
    }}
    QCalendarWidget QAbstractItemView:disabled {{
        color: #aaa;
    }}
"""

# ── Status bar ────────────────────────────────────────────────────────────────
STATUS_QSS = f"""
    QStatusBar {{
        background: {_LIGHT};
        border-top: 1px solid {_BORDER};
        font-size: 11px;
        color: {_TEXT_SEC};
    }}
    QStatusBar::item {{ border: none; }}
"""
