"""RingChart — QPainter donut/ring chart for ESOP saturation visualization."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from PyQt6.QtWidgets import QWidget, QSizePolicy, QApplication
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QConicalGradient
)

# Color thresholds
_GREEN  = "#27AE60"
_YELLOW = "#F39C12"
_RED    = "#C0392B"
_GREY   = "#E0E0E0"
_TEXT   = "#222222"
_BLUE   = "#003087"


def _saturation_color(pct: float) -> str:
    if pct >= 80:
        return _GREEN
    elif pct >= 60:
        return _YELLOW
    return _RED


class RingChart(QWidget):
    """Donut ring chart showing vested vs total ESOP shares saturation."""

    def __init__(self, vested: float = 0.0, total: float = 1.0, parent=None):
        super().__init__(parent)
        self._vested = vested
        self._total = total
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    def set_data(self, vested: float, total: float):
        """Update chart data and trigger repaint."""
        self._vested = vested
        self._total = max(total, 0.001)  # avoid division by zero
        self.update()

    def _saturation_pct(self) -> float:
        if self._total <= 0:
            return 0.0
        return min(100.0, max(0.0, self._vested / self._total * 100.0))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        margin = 8
        outer_r = (size - margin * 2) / 2
        ring_w = outer_r * 0.28   # ring thickness
        inner_r = outer_r - ring_w

        cx = self.width() / 2
        cy = self.height() / 2

        # Background ring (grey)
        rect_outer = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        rect_inner = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        # Draw background arc (full circle)
        bg_path = QPainterPath()
        bg_path.addEllipse(rect_outer)
        hole = QPainterPath()
        hole.addEllipse(rect_inner)
        ring_bg = bg_path.subtracted(hole)
        painter.fillPath(ring_bg, QBrush(QColor(_GREY)))

        # Compute saturation angle
        pct = self._saturation_pct()
        color = QColor(_saturation_color(pct))

        if pct > 0:
            # Draw colored arc (starts from top = 90 degrees, goes clockwise)
            span_deg = pct / 100.0 * 360.0

            # We draw arc using path with pie-minus-inner-circle trick
            fg_path = QPainterPath()
            # Qt arc: startAngle in 1/16th degrees, CCW → use negative span for CW
            fg_path.moveTo(cx, cy)
            fg_path.arcTo(rect_outer, 90.0, -span_deg)
            fg_path.closeSubpath()

            inner_cut = QPainterPath()
            inner_cut.addEllipse(rect_inner)
            # Also cut center
            center_cut = QPainterPath()
            center_cut.addEllipse(QRectF(cx - 2, cy - 2, 4, 4))

            colored_ring = fg_path.subtracted(inner_cut)
            painter.fillPath(colored_ring, QBrush(color))

        # Center text
        painter.setPen(QPen(QColor(_TEXT)))
        pct_font = QFont("Microsoft YaHei", max(8, int(inner_r * 0.42)), QFont.Weight.Bold)
        painter.setFont(pct_font)
        pct_text = f"{pct:.0f}%"
        text_rect = QRectF(cx - inner_r, cy - inner_r * 0.6, inner_r * 2, inner_r * 0.8)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, pct_text)

        # Sub-label
        sub_font = QFont("Microsoft YaHei", max(6, int(inner_r * 0.22)))
        painter.setFont(sub_font)
        painter.setPen(QPen(QColor("#888")))
        sub_rect = QRectF(cx - inner_r, cy + inner_r * 0.1, inner_r * 2, inner_r * 0.5)
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, "饱和度")

        painter.end()


if __name__ == "__main__":
    # Quick preview test
    app = QApplication(sys.argv)
    from PyQt6.QtWidgets import QHBoxLayout
    win = QWidget()
    win.setWindowTitle("RingChart Preview")
    win.setStyleSheet("background:white;")
    win.resize(400, 150)
    lay = QHBoxLayout(win)
    for vested, total, label in [
        (30, 100, "低 30%"),
        (65, 100, "中 65%"),
        (88, 100, "高 88%"),
    ]:
        from PyQt6.QtWidgets import QVBoxLayout, QLabel
        box = QWidget()
        bl = QVBoxLayout(box)
        chart = RingChart(vested, total)
        chart.setFixedSize(110, 110)
        bl.addWidget(chart)
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(lbl)
        lay.addWidget(box)
    win.show()
    sys.exit(app.exec())
