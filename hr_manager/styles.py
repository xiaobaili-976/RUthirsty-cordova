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

# ── Header / NavBar ───────────────────────────────────────────────────────────
NAV_HEIGHT  = 52
NAV_QSS = f"""
    QWidget#NavBar {{
        background: {_BLUE};
        border-bottom: 2px solid {_GOLD};
    }}
"""

NAV_TAB_QSS = f"""
    QPushButton {{
        color: rgba(255,255,255,0.75);
        background: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 0 16px;
        font-size: 13px;
        font-family: "Microsoft YaHei", sans-serif;
    }}
    QPushButton:hover {{
        color: white;
        background: rgba(255,255,255,0.08);
    }}
    QPushButton[active="true"] {{
        color: white;
        border-bottom: 3px solid {_GOLD};
        font-weight: bold;
    }}
"""

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
        border-radius: 8px;
    }}
"""

# ── Buttons ───────────────────────────────────────────────────────────────────
BTN_PRIMARY = f"""
    QPushButton {{
        background: {_BLUE};
        color: white;
        border: none;
        border-radius: 6px;
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
        border-radius: 6px;
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
        border-radius: 6px;
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
        border-radius: 6px;
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
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
        border: 1px solid {_BORDER};
        border-radius: 5px;
        padding: 6px 10px;
        background: white;
        font-size: 13px;
        color: {_TEXT};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {_BLUE};
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
