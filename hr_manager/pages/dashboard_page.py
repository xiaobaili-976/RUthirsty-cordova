"""DashboardPage — 首页：三层组织架构拓扑图（部门→小组→组员）

Features:
- 员工类型自动着色（华为/OD/外包）
- 风险角标（高流失红点、合同到期黄色感叹号）
- 点击人员节点 → 可拖拽悬浮详情卡片
- 鼠标滚轮缩放 + 拖拽平移
- 全局搜索 + 节点高亮定位
- 部门/小组管理（右键菜单）
- 人员归属拖拽调整
"""
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem, QGraphicsObject,
    QMenu, QInputDialog, QMessageBox, QFrame, QScrollArea, QApplication,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QRectF, QPointF, QTimer, QPropertyAnimation,
    QEasingCurve, QRect, QEvent
)
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QFont, QWheelEvent, QPainter, QPainterPath,
    QCursor, QKeySequence
)

from styles import (
    _BLUE, _GREEN, _LIGHT, _BORDER, _TEXT, _RED, _YELLOW, _TEXT_SEC,
    _BG, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER,
    EMP_TYPE_BORDER, EMP_TYPE_BG, RISK_COLOR, RISK_BG
)

# ── Layout constants ──────────────────────────────────────────────────────────
_DEPT_W, _DEPT_H = 170, 52
_GRP_W,  _GRP_H  = 140, 42
_MBR_W,  _MBR_H  = 110, 56   # card-style member node
_X_GAP  = 24
_DEPT_Y = 20
_GRP_Y  = 110
_MBR_Y  = 200


# ── Floating detail card ───────────────────────────────────────────────────────

class _DetailCard(QFrame):
    """Draggable floating card showing full employee info."""

    closed = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("DetailCard")
        self.setStyleSheet("""
            QFrame#DetailCard {
                background: white;
                border: 1px solid #DDE3EE;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        self.setFixedWidth(320)
        self._drag_pos = None
        self.hide()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        self._hdr = QWidget()
        self._hdr.setStyleSheet(
            "background: #003087; border-radius: 12px 12px 0 0;"
        )
        self._hdr.setFixedHeight(48)
        hdr_lay = QHBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(16, 0, 12, 0)
        self._hdr_name = QLabel()
        self._hdr_name.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; background: transparent;"
        )
        hdr_lay.addWidget(self._hdr_name)
        hdr_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(
            "QPushButton { color: white; background: transparent; border: none;"
            " font-size: 14px; } QPushButton:hover { color: #FFD700; }"
        )
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close_card)
        hdr_lay.addWidget(close_btn)
        lay.addWidget(self._hdr)

        # Type badge
        self._type_badge = QLabel()
        self._type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._type_badge.setFixedHeight(28)
        lay.addWidget(self._type_badge)

        # Scroll area for info
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setMaximumHeight(380)
        content = QWidget()
        content.setStyleSheet("background: white;")
        scroll.setWidget(content)
        lay.addWidget(scroll)

        self._info_lay = QVBoxLayout(content)
        self._info_lay.setContentsMargins(16, 10, 16, 16)
        self._info_lay.setSpacing(4)

    def _clear_info(self):
        while self._info_lay.count():
            item = self._info_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _section(self, title: str):
        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color: #003087; font-size: 12px; font-weight: bold;"
            " border-bottom: 1px solid #DDE3EE; padding-bottom: 3px; margin-top: 8px;"
        )
        self._info_lay.addWidget(lbl)

    def _row(self, label: str, value: str):
        if not value:
            return
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #86909C; font-size: 12px; min-width: 72px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val = QLabel(value)
        val.setStyleSheet("color: #222222; font-size: 12px;")
        val.setWordWrap(True)
        rl.addWidget(lbl)
        rl.addWidget(val, 1)
        self._info_lay.addWidget(row)

    def load(self, emp, dept_name: str, group_name: str,
             contract=None, stability=None):
        self._clear_info()

        # Header name + type badge
        self._hdr_name.setText(emp.name)
        etype = emp.employee_type or ""
        bg = EMP_TYPE_BG.get(etype, "#F5F7FA")
        border = EMP_TYPE_BORDER.get(etype, "#AAB4C8")
        self._type_badge.setStyleSheet(
            f"background: {bg}; color: {border}; font-size: 12px; font-weight: bold;"
            f" border-top: 1px solid {border}; border-bottom: 1px solid {border};"
        )
        self._type_badge.setText(etype if etype else "未设置类型")

        # Basic info
        self._section("基本信息")
        self._row("工号", emp.employee_id)
        self._row("姓名", emp.name)
        self._row("性别", emp.gender)
        age = emp.age
        self._row("年龄", f"{age}岁" if age else "")
        self._row("手机", emp.phone)
        self._row("邮箱", emp.email)
        self._row("状态", emp.display_status)

        # Org info
        self._section("岗位信息")
        self._row("部门", dept_name)
        self._row("小组", group_name)
        self._row("职位", emp.job_title)
        self._row("职级", emp.job_level)
        self._row("职等", emp.job_grade)

        # Contract
        if contract:
            self._section("合同信息")
            self._row("合同类型", contract.contract_type)
            self._row("入职日期", contract.hire_date)
            tenure = contract.tenure_months
            self._row("在职时长", f"{tenure}个月" if tenure else "")
            d2e = contract.days_to_end
            if d2e is not None:
                if d2e <= 90:
                    clr = "#C0392B"
                elif d2e <= 180:
                    clr = "#E67E22"
                elif d2e <= 270:
                    clr = "#F39C12"
                else:
                    clr = "#222222"
                row_w = QWidget()
                rl = QHBoxLayout(row_w)
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(8)
                lbl = QLabel("合同到期")
                lbl.setStyleSheet("color: #86909C; font-size: 12px; min-width: 72px;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                val = QLabel(f"{d2e}天后")
                val.setStyleSheet(f"color: {clr}; font-size: 12px; font-weight: bold;")
                rl.addWidget(lbl)
                rl.addWidget(val, 1)
                self._info_lay.addWidget(row_w)

        # Stability
        if stability:
            self._section("稳定性评估")
            risk_map = {"green": "稳定", "yellow": "需关注", "red": "高风险"}
            risk_clr = {"green": "#27AE60", "yellow": "#F39C12", "red": "#C0392B"}
            r = stability.risk_level
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)
            lbl = QLabel("风险等级")
            lbl.setStyleSheet("color: #86909C; font-size: 12px; min-width: 72px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val = QLabel(risk_map.get(r, r))
            val.setStyleSheet(
                f"color: {risk_clr.get(r,'#222')}; font-size: 12px; font-weight: bold;"
            )
            rl.addWidget(lbl)
            rl.addWidget(val, 1)
            self._info_lay.addWidget(row_w)
            if stability.risk_tags:
                self._row("风险标签", stability.risk_tags.replace(",", "  "))

        self._info_lay.addStretch()
        self.adjustSize()
        self.raise_()
        self.show()

    def close_card(self):
        self.hide()
        self.closed.emit()

    # ── Drag ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            # Keep inside parent
            par = self.parent()
            if par:
                new_pos.setX(max(0, min(new_pos.x(), par.width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), par.height() - self.height())))
            self.move(new_pos)
        super().mouseMoveEvent(event)


# ── Member node (card style) ──────────────────────────────────────────────────

class MemberNode(QGraphicsRectItem):
    NODE_TYPE = "member"

    # Risk flag constants
    FLAG_NONE     = 0
    FLAG_RISK     = 1   # high churn risk → red dot
    FLAG_CONTRACT = 2   # contract expiring → yellow !
    FLAG_BOTH     = 3

    def __init__(self, employee_id: str, name: str, emp_type: str,
                 flags: int, x: float, y: float, scene_owner):
        super().__init__(0, 0, _MBR_W, _MBR_H)
        self._id = employee_id
        self._name = name
        self._emp_type = emp_type
        self._flags = flags
        self._scene_owner = scene_owner
        self._highlighted = False
        self.setPos(x, y)

        border_clr = EMP_TYPE_BORDER.get(emp_type, "#AAB4C8")
        bg_clr     = EMP_TYPE_BG.get(emp_type, "#F5F7FA")
        self.setBrush(QBrush(QColor(bg_clr)))
        self.setPen(QPen(QColor(border_clr), 2))
        self.setToolTip(f"{name}\n工号: {employee_id}")
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Name label
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor(_TEXT))
        f = QFont("Microsoft YaHei", 9, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = min(lbl.boundingRect().width(), _MBR_W - 8)
        lbl.setPos((_MBR_W - bw) / 2, 8)

        # Employee type label
        type_lbl = QGraphicsTextItem(emp_type or "未知类型", self)
        type_clr = border_clr
        type_lbl.setDefaultTextColor(QColor(type_clr))
        ft = QFont("Microsoft YaHei", 7)
        type_lbl.setFont(ft)
        tw = type_lbl.boundingRect().width()
        type_lbl.setPos((_MBR_W - tw) / 2, 26)

        # Risk indicator dots (top-right)
        self._draw_flags()

    def _draw_flags(self):
        """Draw risk/contract indicator badges."""
        offset_x = _MBR_W - 8
        if self._flags & self.FLAG_CONTRACT:
            # Yellow ! badge
            badge = QGraphicsEllipseItem(-5, -5, 10, 10, self)
            badge.setBrush(QBrush(QColor("#F39C12")))
            badge.setPen(QPen(Qt.PenStyle.NoPen))
            badge.setPos(offset_x, 0)
            badge.setToolTip("合同即将到期")
            txt = QGraphicsTextItem("!", badge)
            txt.setDefaultTextColor(QColor("white"))
            tf = QFont("Microsoft YaHei", 5, QFont.Weight.Bold)
            txt.setFont(tf)
            tw = txt.boundingRect().width()
            th = txt.boundingRect().height()
            txt.setPos(-tw/2 + 0.5, -th/2)
            offset_x -= 14

        if self._flags & self.FLAG_RISK:
            # Red dot badge
            dot = QGraphicsEllipseItem(-5, -5, 10, 10, self)
            dot.setBrush(QBrush(QColor("#C0392B")))
            dot.setPen(QPen(Qt.PenStyle.NoPen))
            dot.setPos(offset_x, 0)
            dot.setToolTip("高流失风险")

    def set_highlighted(self, on: bool):
        self._highlighted = on
        if on:
            self.setPen(QPen(QColor("#165DFF"), 3))
            self.setBrush(QBrush(QColor("#E8F0FE")))
        else:
            border_clr = EMP_TYPE_BORDER.get(self._emp_type, "#AAB4C8")
            bg_clr     = EMP_TYPE_BG.get(self._emp_type, "#F5F7FA")
            self.setPen(QPen(QColor(border_clr), 2))
            self.setBrush(QBrush(QColor(bg_clr)))

    def hoverEnterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        super().hoverEnterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.pos()
            self._scene_owner.member_clicked(self._id)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """On drop: check if overlapping a group/dept node and reassign."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            moved = (self.pos() - self._drag_start).manhattanLength() > 5
            if moved:
                self._scene_owner.try_reassign_member(self)
            else:
                # snap back to original position if just a click
                pass


# ── Dept / Group nodes ────────────────────────────────────────────────────────

class DeptNode(QGraphicsRectItem):
    NODE_TYPE = "dept"

    def __init__(self, dept_id: int, name: str, x: float, y: float, scene_owner):
        super().__init__(0, 0, _DEPT_W, _DEPT_H)
        self._id = dept_id
        self._name = name
        self._scene_owner = scene_owner
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#003087")))
        self.setPen(QPen(QColor("#001f5e"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"部门: {name}")
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        bh = lbl.boundingRect().height()
        lbl.setPos((_DEPT_W - bw) / 2, (_DEPT_H - bh) / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { border-radius: 8px; padding: 4px; }"
            "QMenu::item { padding: 6px 16px; border-radius: 4px; }"
            "QMenu::item:selected { background: #E8F0FE; color: #003087; }"
        )
        menu.addAction("新增小组", lambda: self._scene_owner.request_add_group(self._id, self._name))
        menu.addAction("编辑部门", lambda: self._scene_owner.request_edit_dept(self._id, self._name))
        menu.addAction("删除部门", lambda: self._scene_owner.request_delete_dept(self._id, self._name))
        menu.exec(event.screenPos())


class GroupNode(QGraphicsRectItem):
    NODE_TYPE = "group"

    def __init__(self, group_id: int, dept_id: int, name: str,
                 x: float, y: float, scene_owner):
        super().__init__(0, 0, _GRP_W, _GRP_H)
        self._id = group_id
        self._dept_id = dept_id
        self._name = name
        self._scene_owner = scene_owner
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#005C99")))
        self.setPen(QPen(QColor("#003087"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"小组: {name}")
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 9)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        bh = lbl.boundingRect().height()
        lbl.setPos((_GRP_W - bw) / 2, (_GRP_H - bh) / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { border-radius: 8px; padding: 4px; }"
            "QMenu::item { padding: 6px 16px; border-radius: 4px; }"
            "QMenu::item:selected { background: #E8F0FE; color: #003087; }"
        )
        menu.addAction("编辑小组", lambda: self._scene_owner.request_edit_group(self._id, self._name))
        menu.addAction("删除小组", lambda: self._scene_owner.request_delete_group(self._id, self._name))
        menu.exec(event.screenPos())


# ── OrgScene ─────────────────────────────────────────────────────────────────

class OrgScene(QGraphicsScene):
    employee_clicked = pyqtSignal(str)

    def __init__(self, managers: dict, parent_widget=None):
        super().__init__()
        self._mgr = managers
        self._parent = parent_widget
        self._member_nodes: list[MemberNode] = []
        self._group_nodes: list[GroupNode]   = []

    def member_clicked(self, employee_id: str):
        self.employee_clicked.emit(employee_id)

    def try_reassign_member(self, mbr_node: MemberNode):
        """Check if member was dropped on a group node; if so, reassign."""
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        mbr_rect = mbr_node.mapToScene(mbr_node.boundingRect()).boundingRect()
        best_grp: GroupNode | None = None
        best_overlap = 0.0
        for grp in self._group_nodes:
            grp_rect = grp.mapToScene(grp.boundingRect()).boundingRect()
            intersection = mbr_rect.intersected(grp_rect)
            area = intersection.width() * intersection.height()
            if area > best_overlap:
                best_overlap = area
                best_grp = grp
        if best_grp and best_overlap > 100:
            emp = emp_mgr.get_employee(mbr_node._id)
            if emp:
                emp.group_id = best_grp._id
                emp.dept_id  = best_grp._dept_id
                emp_mgr.update_employee(emp)
                if self._parent:
                    self._parent.refresh()
        else:
            # Snap back
            if self._parent:
                self._parent.refresh()

    def request_add_group(self, dept_id, dept_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent, "新增小组", f"部门 [{dept_name}] 的新小组名称:"
        )
        if ok and name.strip():
            emp_mgr.add_group(dept_id, name.strip())
            if self._parent:
                self._parent.refresh()

    def request_edit_dept(self, dept_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent, "编辑部门", "部门名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_department(dept_id, name.strip())
            if self._parent:
                self._parent.refresh()

    def request_delete_dept(self, dept_id, dept_name):
        if QMessageBox.question(
            self._parent, "确认删除",
            f"确定删除部门 [{dept_name}]？相关员工部门归属将被清空。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_department(dept_id)
                if self._parent:
                    self._parent.refresh()

    def request_edit_group(self, group_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent, "编辑小组", "小组名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_group(group_id, name.strip())
            if self._parent:
                self._parent.refresh()

    def request_delete_group(self, group_id, group_name):
        if QMessageBox.question(
            self._parent, "确认删除",
            f"确定删除小组 [{group_name}]？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_group(group_id)
                if self._parent:
                    self._parent.refresh()


# ── OrgChartView ─────────────────────────────────────────────────────────────

class OrgChartView(QGraphicsView):
    def __init__(self, scene: OrgScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet(
            "background: #F5F7FA; border: 1px solid #DDE3EE; border-radius: 12px;"
        )
        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ── DashboardPage ─────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    employee_selected = pyqtSignal(str)

    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._member_nodes: list[MemberNode] = []
        self.setStyleSheet("background: #F5F7FA;")
        self._scene = OrgScene(managers, parent_widget=self)
        self._scene.employee_clicked.connect(self._on_member_clicked)
        self._detail_card = _DetailCard(self)
        self._build()
        # Close card on click outside
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.MouseButtonPress and
                obj is self and self._detail_card.isVisible()):
            if not self._detail_card.geometry().contains(
                    self.mapFromGlobal(QCursor.pos())):
                self._detail_card.close_card()
        return super().eventFilter(obj, event)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # ── Toolbar row ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("搜索姓名 / 工号...")
        self._search_box.setFixedHeight(32)
        self._search_box.setMaximumWidth(240)
        self._search_box.setStyleSheet(
            "QLineEdit { border: 1px solid #DDE3EE; border-radius: 16px;"
            " padding: 0 12px; background: white; font-size: 12px; }"
            "QLineEdit:focus { border-color: #165DFF; }"
        )
        self._search_box.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_box)

        toolbar.addStretch(1)

        # Legend
        for etype, border_clr in [("华为", "#2ECC71"), ("OD", "#3498DB"), ("外包", "#F39C12")]:
            bg = EMP_TYPE_BG.get(etype, "#F5F7FA")
            dot = QLabel(f"● {etype}")
            dot.setStyleSheet(
                f"color: {border_clr}; font-size: 11px;"
                f" background: {bg}; border: 1px solid {border_clr};"
                f" border-radius: 10px; padding: 2px 8px;"
            )
            toolbar.addWidget(dot)

        toolbar.addSpacing(12)

        # Zoom / reset buttons
        for lbl, fn in [("放大", lambda: self._view.scale(1.15, 1.15)),
                         ("缩小", lambda: self._view.scale(1/1.15, 1/1.15)),
                         ("重置", self._reset_view)]:
            btn = QPushButton(lbl)
            btn.setFixedHeight(30)
            btn.setStyleSheet(BTN_SECONDARY)
            btn.clicked.connect(fn)
            toolbar.addWidget(btn)

        # Add dept button
        add_dept_btn = QPushButton("+ 新增部门")
        add_dept_btn.setFixedHeight(30)
        add_dept_btn.setStyleSheet(BTN_PRIMARY)
        add_dept_btn.clicked.connect(self._add_dept)
        toolbar.addWidget(add_dept_btn)

        lay.addLayout(toolbar)

        # ── Hint label ──
        hint = QLabel("右键部门/小组节点管理 · 滚轮缩放 · 中键拖拽平移 · 拖拽人员节点调整归属")
        hint.setStyleSheet("color: #86909C; font-size: 11px;")
        lay.addWidget(hint)

        # ── Graphics view ──
        self._view = OrgChartView(self._scene)
        lay.addWidget(self._view, 1)

        self._load_tree()

    def _load_tree(self):
        self._scene.clear()
        self._member_nodes.clear()
        self._scene._member_nodes.clear()
        self._scene._group_nodes.clear()

        emp_mgr   = self._mgr.get("employee")
        cont_mgr  = self._mgr.get("contract")
        stab_mgr  = self._mgr.get("stability")
        if not emp_mgr:
            self._scene.addText("暂无数据（未连接员工管理器）").setDefaultTextColor(QColor("#999"))
            return

        depts = emp_mgr.list_departments()
        groups_all = emp_mgr.list_groups()
        employees_all = emp_mgr.list_employees()

        # Risk lookups
        high_risk_ids = set()
        if stab_mgr:
            for r in stab_mgr.get_high_risk_employees():
                high_risk_ids.add(r["employee_id"])
        expiring_ids = set()
        if cont_mgr:
            for r in cont_mgr.get_expiring_soon(270):
                expiring_ids.add(r["employee_id"])

        groups_by_dept: dict[int, list] = {}
        for g in groups_all:
            groups_by_dept.setdefault(g["dept_id"], []).append(g)

        emps_by_group: dict[int, list] = {}
        emps_by_dept:  dict[int, list] = {}
        for e in employees_all:
            if e.group_id:
                emps_by_group.setdefault(e.group_id, []).append(e)
            elif e.dept_id:
                emps_by_dept.setdefault(e.dept_id, []).append(e)

        connector_pen = QPen(QColor("#C5CAD6"), 1.5, Qt.PenStyle.DashLine)

        dept_x = _X_GAP
        for dept in depts:
            did = dept["dept_id"]
            gs  = groups_by_dept.get(did, [])

            # Calculate column width
            mbr_count_per_grp = [len(emps_by_group.get(g["group_id"], [])) for g in gs]
            direct_count = len(emps_by_dept.get(did, []))
            if gs:
                total_w = sum(
                    max(_GRP_W, max(1, mc) * (_MBR_W + _X_GAP) - _X_GAP)
                    for mc in mbr_count_per_grp
                )
                col_w = max(_DEPT_W, total_w + (len(gs)-1) * _X_GAP)
            else:
                col_w = max(_DEPT_W, direct_count * (_MBR_W + _X_GAP) + _X_GAP)

            # Dept node (centered over its column)
            dept_cx = dept_x + (col_w - _DEPT_W) / 2
            dept_node = DeptNode(did, dept["dept_name"], dept_cx, _DEPT_Y, self._scene)
            self._scene.addItem(dept_node)
            dept_mid_x = dept_cx + _DEPT_W / 2
            dept_bot_y = _DEPT_Y + _DEPT_H

            # Groups
            grp_x = dept_x
            for g, mbr_c in zip(gs, mbr_count_per_grp):
                gid = g["group_id"]
                grp_w = max(_GRP_W, mbr_c * (_MBR_W + _X_GAP) - _X_GAP + _X_GAP)
                grp_cx = grp_x + (grp_w - _GRP_W) / 2
                grp_node = GroupNode(gid, did, g["group_name"], grp_cx, _GRP_Y, self._scene)
                self._scene.addItem(grp_node)
                self._scene._group_nodes.append(grp_node)

                # Connector dept→group
                line = QGraphicsLineItem(dept_mid_x, dept_bot_y,
                                         grp_cx + _GRP_W/2, _GRP_Y)
                line.setPen(connector_pen)
                self._scene.addItem(line)

                # Member nodes under group
                members = emps_by_group.get(gid, [])
                mbr_x = grp_x
                for e in members:
                    flags = 0
                    if e.employee_id in high_risk_ids:
                        flags |= MemberNode.FLAG_RISK
                    if e.employee_id in expiring_ids:
                        flags |= MemberNode.FLAG_CONTRACT
                    mnode = MemberNode(
                        e.employee_id, e.name, e.employee_type or "",
                        flags, mbr_x, _MBR_Y, self._scene
                    )
                    self._scene.addItem(mnode)
                    self._member_nodes.append(mnode)
                    self._scene._member_nodes.append(mnode)
                    mline = QGraphicsLineItem(
                        grp_cx + _GRP_W/2, _GRP_Y + _GRP_H,
                        mbr_x + _MBR_W/2, _MBR_Y
                    )
                    mline.setPen(connector_pen)
                    self._scene.addItem(mline)
                    mbr_x += _MBR_W + _X_GAP

                grp_x += grp_w + _X_GAP

            # Direct members under dept
            dm_x = dept_x
            for e in emps_by_dept.get(did, []):
                flags = 0
                if e.employee_id in high_risk_ids:
                    flags |= MemberNode.FLAG_RISK
                if e.employee_id in expiring_ids:
                    flags |= MemberNode.FLAG_CONTRACT
                mnode = MemberNode(
                    e.employee_id, e.name, e.employee_type or "",
                    flags, dm_x, _MBR_Y, self._scene
                )
                self._scene.addItem(mnode)
                self._member_nodes.append(mnode)
                self._scene._member_nodes.append(mnode)
                dline = QGraphicsLineItem(
                    dept_mid_x, dept_bot_y,
                    dm_x + _MBR_W/2, _MBR_Y
                )
                dline.setPen(connector_pen)
                self._scene.addItem(dline)
                dm_x += _MBR_W + _X_GAP

            dept_x += col_w + _X_GAP * 2

        if not depts:
            ph = self._scene.addText("暂无部门数据，请先在基础信息中添加部门")
            ph.setDefaultTextColor(QColor("#999"))
            ph.setFont(QFont("Microsoft YaHei", 12))

    def _on_search(self, query: str):
        q = query.strip().lower()
        for node in self._member_nodes:
            match = (q and (q in node._name.lower() or q in node._id.lower()))
            node.set_highlighted(match)
            if match:
                self._view.centerOn(node)

    def _on_member_clicked(self, employee_id: str):
        """Show floating detail card for clicked employee."""
        emp_mgr  = self._mgr.get("employee")
        cont_mgr = self._mgr.get("contract")
        stab_mgr = self._mgr.get("stability")
        if not emp_mgr:
            return
        emp = emp_mgr.get_employee(employee_id)
        if not emp:
            return

        # Resolve dept/group names
        dept_name  = ""
        group_name = ""
        if emp.dept_id:
            for d in emp_mgr.list_departments():
                if d["dept_id"] == emp.dept_id:
                    dept_name = d["dept_name"]
                    break
        if emp.group_id:
            for g in emp_mgr.list_groups():
                if g["group_id"] == emp.group_id:
                    group_name = g["group_name"]
                    break

        contract  = cont_mgr.get_active_contract(employee_id) if cont_mgr else None
        stability = stab_mgr.get_latest(employee_id) if stab_mgr else None

        self._detail_card.load(emp, dept_name, group_name, contract, stability)

        # Position card near the clicked node — find scene pos → viewport pos
        for node in self._member_nodes:
            if node._id == employee_id:
                scene_pos = node.mapToScene(QPointF(node.boundingRect().width() + 8, 0))
                vp_pos = self._view.mapFromScene(scene_pos)
                # Map viewport pos to this widget
                card_pos = self._view.mapTo(self, vp_pos)
                # Clamp to widget bounds
                card_x = min(card_pos.x(), self.width() - self._detail_card.width() - 8)
                card_y = min(card_pos.y(), self.height() - 420)
                card_y = max(card_y, 0)
                self._detail_card.move(max(card_x, 0), card_y)
                break

        # Also emit for sidebar
        self.employee_selected.emit(employee_id)

    def _reset_view(self):
        self._view.resetTransform()
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(rect.adjusted(-20, -20, 20, 20),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def _add_dept(self):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(self, "新增部门", "部门名称:")
        if ok and name.strip():
            emp_mgr.add_department(name.strip())
            self.refresh()

    def refresh(self):
        self._load_tree()
        self._reset_view()
