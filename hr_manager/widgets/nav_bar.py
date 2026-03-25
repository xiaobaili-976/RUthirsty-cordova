"""NavBar — top navigation with 8 module tabs, geometric icons + labels."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPointF, QTimer, QVariantAnimation
from PyQt6.QtGui import (
    QFont, QPainter, QColor, QPen, QBrush, QPainterPath, QPolygonF,
    QFontMetrics, QCursor
)

_NAV_HEIGHT = 80
_NAV_BG     = "#F7F8FA"
_INACTIVE   = "#86909C"
_HOVER_CLR  = "#4080FF"
_ACTIVE_CLR = "#165DFF"

_TABS = [
    ("home",       "首页"),
    ("employee",   "基础信息"),
    ("contract",   "合同管理"),
    ("salary",     "薪酬管理"),
    ("position",   "人岗管理"),
    ("esop",       "长期激励"),
    ("stability",  "晴雨表"),
    ("settings",   "设置"),
]


# ── Icon painters (24×24 logical canvas, drawn centered) ──────────────────────

def _icon_home(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """3-tier staircase + triangular roof."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    # Roof triangle
    roof = QPolygonF([QPointF(x0+12, y0+2), QPointF(x0+1, y0+11), QPointF(x0+23, y0+11)])
    if filled:
        p.setBrush(QBrush(clr))
    else:
        p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolygon(roof)
    # Steps (staircase below roof)
    p.setBrush(QBrush(clr) if filled else Qt.BrushStyle.NoBrush)
    # Step 3 (top/small): x=8,y=11,w=8,h=4
    p.drawRoundedRect(QRectF(x0+8, y0+11, 8, 4), 1, 1)
    # Step 2 (middle): x=5,y=15,w=14,h=4
    p.drawRoundedRect(QRectF(x0+5, y0+15, 14, 4), 1, 1)
    # Step 1 (bottom/wide): x=2,y=19,w=20,h=4
    p.drawRoundedRect(QRectF(x0+2, y0+19, 20, 4), 1, 1)


def _icon_employee(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Person head + shoulders + small file/archive."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    brush = QBrush(clr) if filled else Qt.BrushStyle.NoBrush
    p.setBrush(brush)
    # Head circle
    p.drawEllipse(QRectF(x0+5, y0+1, 8, 8))
    # Shoulders (arc/lines)
    path = QPainterPath()
    path.moveTo(x0+1, y0+20)
    path.cubicTo(QPointF(x0+1, y0+13), QPointF(x0+5, y0+11),
                 QPointF(x0+9, y0+11))
    path.cubicTo(QPointF(x0+13, y0+11), QPointF(x0+17, y0+13),
                 QPointF(x0+17, y0+20))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    # Small file icon to the right
    p.setBrush(brush)
    p.drawRoundedRect(QRectF(x0+16, y0+12, 7, 9), 1, 1)
    # Lines on file
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(x0+17.5, y0+15), QPointF(x0+21.5, y0+15))
    p.drawLine(QPointF(x0+17.5, y0+17.5), QPointF(x0+21.5, y0+17.5))


def _icon_contract(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Document with fold corner + circular seal."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    brush = QBrush(clr) if filled else Qt.BrushStyle.NoBrush
    p.setBrush(brush)
    # Document outline with top-right corner fold
    fold_size = 5
    doc = QPainterPath()
    doc.moveTo(x0+2, y0+1)
    doc.lineTo(x0+15, y0+1)
    doc.lineTo(x0+20, y0+fold_size+1)
    doc.lineTo(x0+20, y0+20)
    doc.lineTo(x0+2, y0+20)
    doc.closeSubpath()
    p.drawPath(doc)
    # Fold triangle
    p.setBrush(Qt.BrushStyle.NoBrush)
    fold = QPainterPath()
    fold.moveTo(x0+15, y0+1)
    fold.lineTo(x0+15, y0+fold_size+1)
    fold.lineTo(x0+20, y0+fold_size+1)
    p.drawPath(fold)
    # Lines on document
    p.drawLine(QPointF(x0+5, y0+8), QPointF(x0+14, y0+8))
    p.drawLine(QPointF(x0+5, y0+11), QPointF(x0+16, y0+11))
    p.drawLine(QPointF(x0+5, y0+14), QPointF(x0+16, y0+14))
    # Seal circle (bottom right, overlapping)
    p.setBrush(QBrush(clr) if filled else Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(x0+14, y0+15, 8, 8))
    # Cross in seal
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(x0+18, y0+17), QPointF(x0+18, y0+21))
    p.drawLine(QPointF(x0+16, y0+19), QPointF(x0+20, y0+19))


def _icon_salary(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Pay slip rectangle + ¥ symbol."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    brush = QBrush(clr) if filled else Qt.BrushStyle.NoBrush
    p.setBrush(brush)
    # Outer slip rect
    p.drawRoundedRect(QRectF(x0+1, y0+2, 22, 20), 2, 2)
    # Header band
    if not filled:
        p.setBrush(QBrush(clr))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(x0+1, y0+2, 22, 6), 2, 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
    # ¥ symbol (simplified): V shape + 2 horizontal bars + vertical stem
    vx = x0 + 12
    # V top-left to bottom, V top-right to bottom
    p.drawLine(QPointF(vx-4, y0+10), QPointF(vx, y0+14))
    p.drawLine(QPointF(vx+4, y0+10), QPointF(vx, y0+14))
    # Two horizontal bars
    p.drawLine(QPointF(vx-3.5, y0+14), QPointF(vx+3.5, y0+14))
    p.drawLine(QPointF(vx-3.5, y0+16), QPointF(vx+3.5, y0+16))
    # Vertical stem down
    p.drawLine(QPointF(vx, y0+16), QPointF(vx, y0+20))


def _icon_position(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Person ↔ position: two person silhouettes + bidirectional arrow."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    brush = QBrush(clr) if filled else Qt.BrushStyle.NoBrush
    # Left person (smaller)
    p.setBrush(brush)
    p.drawEllipse(QRectF(x0+0, y0+1, 6, 6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(x0-2, y0+8, 10, 8), 0, 180*16)
    # Right person (smaller)
    p.setBrush(brush)
    p.drawEllipse(QRectF(x0+18, y0+1, 6, 6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(x0+16, y0+8, 10, 8), 0, 180*16)
    # Bidirectional arrow in middle
    mid_y = y0 + 12
    # Right arrow
    p.drawLine(QPointF(x0+8, mid_y-2), QPointF(x0+16, mid_y-2))
    p.drawLine(QPointF(x0+13, mid_y-4.5), QPointF(x0+16, mid_y-2))
    p.drawLine(QPointF(x0+13, mid_y+0.5), QPointF(x0+16, mid_y-2))
    # Left arrow
    p.drawLine(QPointF(x0+8, mid_y+2), QPointF(x0+16, mid_y+2))
    p.drawLine(QPointF(x0+11, mid_y-0.5), QPointF(x0+8, mid_y+2))
    p.drawLine(QPointF(x0+11, mid_y+4.5), QPointF(x0+8, mid_y+2))


def _icon_esop(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Geometric trophy: cup + stem + base."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    brush = QBrush(clr) if filled else Qt.BrushStyle.NoBrush
    p.setBrush(brush)
    # Cup body (trapezoid top-heavy → cup shape)
    cup = QPainterPath()
    cup.moveTo(x0+4, y0+2)
    cup.lineTo(x0+20, y0+2)
    cup.lineTo(x0+17, y0+11)
    cup.cubicTo(QPointF(x0+17, y0+13), QPointF(x0+13, y0+14),
                QPointF(x0+12, y0+14))
    cup.cubicTo(QPointF(x0+11, y0+14), QPointF(x0+7, y0+13),
                QPointF(x0+7, y0+11))
    cup.closeSubpath()
    p.drawPath(cup)
    # Left handle
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(x0+1, y0+3, 6, 7), 90*16, 180*16)
    # Right handle
    p.drawArc(QRectF(x0+17, y0+3, 6, 7), 270*16, 180*16)
    # Stem
    p.setBrush(brush)
    p.drawRoundedRect(QRectF(x0+10, y0+14, 4, 4), 1, 1)
    # Base
    p.drawRoundedRect(QRectF(x0+6, y0+18, 12, 4), 1, 1)


def _icon_stability(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """Sun (circle + rays) + cloud."""
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    # Sun center left, cloud overlapping right
    sun_cx, sun_cy, sun_r = x0+8, y0+10, 4
    p.setBrush(QBrush(clr) if filled else Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(sun_cx-sun_r, sun_cy-sun_r, sun_r*2, sun_r*2))
    # Sun rays (8 directions)
    import math
    p.setBrush(Qt.BrushStyle.NoBrush)
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        x1 = sun_cx + (sun_r+1.5) * math.cos(rad)
        y1 = sun_cy + (sun_r+1.5) * math.sin(rad)
        x2 = sun_cx + (sun_r+4) * math.cos(rad)
        y2 = sun_cy + (sun_r+4) * math.sin(rad)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    # Cloud (3 overlapping circles)
    p.setBrush(QBrush(clr) if filled else Qt.BrushStyle.NoBrush)
    cloud_path = QPainterPath()
    cloud_path.addEllipse(QRectF(x0+13, y0+11, 7, 7))
    cloud_path.addEllipse(QRectF(x0+16, y0+9, 7, 7))
    cloud_path.addEllipse(QRectF(x0+19, y0+11, 7, 7))
    p.drawPath(cloud_path)
    # Cloud base line
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(x0+13, y0+18), QPointF(x0+26, y0+18))


def _icon_settings(p: QPainter, cx: float, cy: float, filled: bool, clr: QColor, pw: float):
    """8-tooth gear."""
    import math
    pen = QPen(clr, pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x0, y0 = cx - 12, cy
    gcx, gcy = x0+12, y0+12  # gear center
    outer_r, inner_r, hole_r = 10, 7.5, 4
    tooth_w = 2.5
    n_teeth = 8
    path = QPainterPath()
    for i in range(n_teeth):
        angle_start = math.radians(i * 360 / n_teeth - 11)
        angle_mid   = math.radians(i * 360 / n_teeth)
        angle_end   = math.radians(i * 360 / n_teeth + 11)
        angle_nxt   = math.radians((i+1) * 360 / n_teeth - 11)
        if i == 0:
            path.moveTo(gcx + inner_r * math.cos(angle_start),
                        gcy + inner_r * math.sin(angle_start))
        else:
            path.lineTo(gcx + inner_r * math.cos(angle_start),
                        gcy + inner_r * math.sin(angle_start))
        path.lineTo(gcx + outer_r * math.cos(angle_start),
                    gcy + outer_r * math.sin(angle_start))
        path.lineTo(gcx + outer_r * math.cos(angle_end),
                    gcy + outer_r * math.sin(angle_end))
        path.lineTo(gcx + inner_r * math.cos(angle_end),
                    gcy + inner_r * math.sin(angle_end))
        path.arcTo(QRectF(gcx-inner_r, gcy-inner_r, inner_r*2, inner_r*2),
                   -math.degrees(angle_end), -(math.degrees(angle_nxt) - math.degrees(angle_end)))
    path.closeSubpath()
    if filled:
        p.setBrush(QBrush(clr))
    else:
        p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    # Center hole
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(clr, pw))
    p.drawEllipse(QRectF(gcx-hole_r, gcy-hole_r, hole_r*2, hole_r*2))


_ICON_FN = {
    "home":      _icon_home,
    "employee":  _icon_employee,
    "contract":  _icon_contract,
    "salary":    _icon_salary,
    "position":  _icon_position,
    "esop":      _icon_esop,
    "stability": _icon_stability,
    "settings":  _icon_settings,
}


# ── NavItemWidget ─────────────────────────────────────────────────────────────

class NavItemWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, icon_type: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._label = label
        self._active = False
        self._hover = False
        self._float_offset = 0.0          # 0 → -2 when hovering (float up)
        self._anim: QVariantAnimation | None = None
        self.setFixedHeight(_NAV_HEIGHT)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    # ── State ──

    def set_active(self, active: bool):
        self._active = active
        self.update()

    # ── Hover animation ──

    def _start_anim(self, target: float):
        if self._anim:
            self._anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(float(self._float_offset))
        anim.setEndValue(target)
        anim.setDuration(200)
        anim.valueChanged.connect(self._on_anim_value)
        anim.start()
        self._anim = anim

    def _on_anim_value(self, v):
        self._float_offset = float(v)
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self._start_anim(-2.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._start_anim(0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # ── Paint ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(_NAV_BG))

        if self._active:
            icon_clr = QColor(_ACTIVE_CLR)
            pen_w    = 2.0
            filled   = True
        elif self._hover:
            icon_clr = QColor(_HOVER_CLR)
            pen_w    = 2.5
            filled   = False
        else:
            icon_clr = QColor(_INACTIVE)
            pen_w    = 2.0
            filled   = False

        w = self.width()
        # Icon top: 16px from top + float offset
        icon_top_y = 14.0 + self._float_offset
        # Draw icon (24×24, centered horizontally)
        cx = w / 2
        fn = _ICON_FN.get(self._icon_type)
        if fn:
            fn(painter, cx, icon_top_y, filled, icon_clr, pen_w)

        # Label (12px, Microsoft YaHei)
        font = QFont("Microsoft YaHei", 1)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(icon_clr)
        label_y = int(icon_top_y + 24 + 8)
        painter.drawText(QRect(0, label_y, w, 16),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         self._label)

        # Active underline
        if self._active:
            painter.setPen(QPen(QColor(_ACTIVE_CLR), 2))
            painter.drawLine(0, _NAV_HEIGHT - 1, w, _NAV_HEIGHT - 1)

        painter.end()


# ── NavBar ────────────────────────────────────────────────────────────────────

class NavBar(QWidget):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(_NAV_HEIGHT)
        self.setStyleSheet(f"QWidget#NavBar {{ background: {_NAV_BG}; "
                           f"border-bottom: 1px solid #E0E4EA; }}")
        self._active = 0
        self._items: list[NavItemWidget] = []
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        for i, (icon_type, label) in enumerate(_TABS):
            item = NavItemWidget(icon_type, label, self)
            item.clicked.connect(lambda idx=i: self._on_tab(idx))
            item.setToolTip(label)
            self._items.append(item)
            lay.addWidget(item, 1)   # equal stretch for all tabs

        self._set_active(0)

    def _on_tab(self, idx: int):
        self._set_active(idx)
        self.tab_changed.emit(idx)

    def _set_active(self, idx: int):
        self._active = idx
        for i, item in enumerate(self._items):
            item.set_active(i == idx)

    # Kept for backward-compat (settings_button no longer separate)
    @property
    def settings_button(self):
        return None
