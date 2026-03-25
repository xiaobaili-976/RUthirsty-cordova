"""DashboardPage — 首页：三层组织架构拓扑图（部门→小组→组员）

连线规则：
  顶层→中层：横向主干 + 垂直分支
  中层→基层：垂直主干 + 纵向连接（单列员工，主干贯穿各员工顶部中心）

员工布局：单列垂直左对齐，与所属小组栏同宽居中对齐
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem,
    QMenu, QInputDialog, QMessageBox, QFrame, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QEvent
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QFont, QWheelEvent, QPainter, QCursor,
)

from styles import (
    _BLUE, _GREEN, _LIGHT, _BORDER, _TEXT, _RED, _YELLOW, _TEXT_SEC,
    _BG, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER,
    EMP_TYPE_BORDER, EMP_TYPE_BG, RISK_COLOR, RISK_BG,
)

# ── Layout constants ───────────────────────────────────────────────────────────
_DEPT_W,  _DEPT_H  = 180, 48    # dept node size
_GRP_W,   _GRP_H   = 160, 40    # group node size
_MBR_W,   _MBR_H   = 160, 36    # member node (same width → center-aligns with group)
_X_GAP             = 40         # horizontal gap between group columns
_DEPT_GAP          = 60         # extra gap between dept columns
_Y_DEPT            = 20         # dept top Y
_Y_DG_GAP          = 52         # dept-bottom → group-top vertical gap
_Y_GM_GAP          = 48         # group-bottom → first-member-top vertical gap
_MBR_VGAP          = 18         # gap between consecutive member nodes

# Pre-computed Y positions
_Y_GRP  = _Y_DEPT + _DEPT_H + _Y_DG_GAP          # group top Y
_Y_MBR0 = _Y_GRP  + _GRP_H  + _Y_GM_GAP          # first member top Y

# Connector pen: solid black 1pt
_CONN_PEN = QPen(QColor("#1a1a1a"), 1, Qt.PenStyle.SolidLine)
_CONN_PEN.setCapStyle(Qt.PenCapStyle.FlatCap)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_line(scene, x1, y1, x2, y2):
    line = QGraphicsLineItem(x1, y1, x2, y2)
    line.setPen(_CONN_PEN)
    scene.addItem(line)


_TYPE_ORDER = {"华为": 0, "OD": 1, "外包": 2}


def _member_sort_key(e):
    is_pl = "PL" in (e.job_title or "").upper()
    return (0 if is_pl else 1, _TYPE_ORDER.get(e.employee_type or "", 3), e.name or "")


def _draw_dept_to_groups(scene, dept_cx, dept_bot_y, grp_centers_x):
    """Horizontal trunk at mid-point + vertical drops to each group."""
    if not grp_centers_x:
        return
    trunk_y = dept_bot_y + _Y_DG_GAP / 2
    grp_top_y = _Y_GRP

    # Vertical stub: dept bottom → trunk
    _add_line(scene, dept_cx, dept_bot_y, dept_cx, trunk_y)

    if len(grp_centers_x) == 1:
        _add_line(scene, dept_cx, trunk_y, grp_centers_x[0], trunk_y)
        _add_line(scene, grp_centers_x[0], trunk_y, grp_centers_x[0], grp_top_y)
    else:
        first_cx, last_cx = grp_centers_x[0], grp_centers_x[-1]
        # Extend trunk to cover dept center too
        h_left  = min(dept_cx, first_cx)
        h_right = max(dept_cx, last_cx)
        _add_line(scene, h_left, trunk_y, h_right, trunk_y)
        for gcx in grp_centers_x:
            _add_line(scene, gcx, trunk_y, gcx, grp_top_y)


def _draw_group_to_members(scene, grp_cx, grp_bot_y, mbr_top_ys):
    """Chain connections: group bottom → first member top, then member bottom → next member top."""
    if not mbr_top_ys:
        return
    # Group bottom → first member top (center X aligned)
    _add_line(scene, grp_cx, grp_bot_y, grp_cx, mbr_top_ys[0])
    # Member[i] bottom → Member[i+1] top
    for i in range(len(mbr_top_ys) - 1):
        mbr_bot_i = mbr_top_ys[i] + _MBR_H
        _add_line(scene, grp_cx, mbr_bot_i, grp_cx, mbr_top_ys[i + 1])


# ── Right-side detail panel ────────────────────────────────────────────────────

class _DetailPanel(QFrame):
    """Employee detail panel on the right side of the splitter."""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPanel")
        self.setStyleSheet("""
            QFrame#DetailPanel {
                background: white;
                border-left: 1px solid #DDE3EE;
            }
        """)
        self.setMinimumWidth(220)
        self._build()
        self.hide()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Header ──
        self._hdr = QWidget()
        self._hdr.setStyleSheet("background:#003087;")
        self._hdr.setFixedHeight(48)
        hdr_lay = QHBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(16, 0, 12, 0)

        self._hdr_name = QLabel()
        self._hdr_name.setStyleSheet(
            "color:white; font-size:15px; font-weight:bold; background:transparent;"
        )
        hdr_lay.addWidget(self._hdr_name)
        hdr_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(
            "QPushButton { color: white; background: transparent; border: none;"
            " font-size: 18px; font-weight: bold; }"
            "QPushButton:hover { color: #FFD700; }"
        )
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self._close)
        hdr_lay.addWidget(close_btn)
        lay.addWidget(self._hdr)

        # ── Type badge ──
        self._type_badge = QLabel()
        self._type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._type_badge.setFixedHeight(28)
        lay.addWidget(self._type_badge)

        # ── Scrollable info area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        content.setStyleSheet("background:white;")
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        self._info_lay = QVBoxLayout(content)
        self._info_lay.setContentsMargins(16, 10, 16, 16)
        self._info_lay.setSpacing(4)

    # ── Content helpers ──

    def _clear(self):
        while self._info_lay.count():
            item = self._info_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _section(self, title: str):
        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color:#003087; font-size:12px; font-weight:bold;"
            " border-bottom:1px solid #DDE3EE; padding-bottom:3px; margin-top:8px;"
        )
        self._info_lay.addWidget(lbl)

    def _row(self, label: str, value: str, color: str = "#222222"):
        if not value:
            return
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#86909C; font-size:12px; min-width:72px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val = QLabel(value)
        val.setStyleSheet(f"color:{color}; font-size:12px;")
        val.setWordWrap(True)
        rl.addWidget(lbl)
        rl.addWidget(val, 1)
        self._info_lay.addWidget(row)

    # ── Public API ──

    def load(self, emp, dept_name: str, group_name: str,
             contract=None, stability=None):
        self._clear()

        self._hdr_name.setText(emp.name)
        etype = emp.employee_type or ""
        bg     = EMP_TYPE_BG.get(etype, "#F5F7FA")
        border = EMP_TYPE_BORDER.get(etype, "#AAB4C8")
        self._type_badge.setText(etype if etype else "未设置类型")
        self._type_badge.setStyleSheet(
            f"background:{bg}; color:{border}; font-size:12px; font-weight:bold;"
            f" border-top:1px solid {border}; border-bottom:1px solid {border};"
        )

        self._section("基本信息")
        self._row("工号",  emp.employee_id)
        self._row("姓名",  emp.name)
        self._row("性别",  emp.gender)
        age = emp.age
        self._row("年龄",  f"{age}岁" if age else "")
        self._row("手机",  emp.phone)
        self._row("邮箱",  emp.email)
        self._row("状态",  emp.display_status)

        self._section("岗位信息")
        self._row("部门",  dept_name)
        self._row("小组",  group_name)
        self._row("职位",  emp.job_title)
        self._row("职级",  emp.job_level)
        self._row("职等",  emp.job_grade)

        if contract:
            self._section("合同信息")
            self._row("合同类型", contract.contract_type)
            self._row("入职日期", contract.hire_date)
            tenure = contract.tenure_months
            self._row("在职时长", f"{tenure}个月" if tenure else "")
            d2e = contract.days_to_end
            if d2e is not None:
                if d2e <= 90:   clr = "#C0392B"
                elif d2e <= 180: clr = "#E67E22"
                elif d2e <= 270: clr = "#F39C12"
                else:           clr = "#222222"
                self._row("合同到期", f"{d2e}天后", color=clr)

        if stability:
            self._section("稳定性评估")
            risk_map = {"green": "稳定", "yellow": "需关注", "red": "高风险"}
            risk_clr = {"green": "#27AE60", "yellow": "#F39C12", "red": "#C0392B"}
            r = stability.risk_level
            self._row("风险等级", risk_map.get(r, r), color=risk_clr.get(r, "#222"))
            if stability.risk_tags:
                self._row("风险标签", stability.risk_tags.replace(",", "  "))

        self._info_lay.addStretch()
        self.show()

    def _close(self):
        self.hide()
        self.closed.emit()


# ── Member node (card style, single-column) ───────────────────────────────────

class MemberNode(QGraphicsRectItem):
    NODE_TYPE = "member"
    FLAG_NONE     = 0
    FLAG_RISK     = 1
    FLAG_CONTRACT = 2

    def __init__(self, employee_id, name, emp_type, flags, x, y, scene_owner):
        super().__init__(0, 0, _MBR_W, _MBR_H)
        self._id   = employee_id
        self._name = name
        self._emp_type   = emp_type
        self._flags      = flags
        self._scene_owner = scene_owner
        self._drag_start  = QPointF()
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

        # Name label (centered vertically)
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor(_TEXT))
        f = QFont("Microsoft YaHei", 9, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = min(lbl.boundingRect().width(), _MBR_W - 12)
        bh = lbl.boundingRect().height()
        lbl.setPos((_MBR_W - bw) / 2, (_MBR_H - bh) / 2)

        self._draw_flags()

    def _draw_flags(self):
        offset_x = _MBR_W - 6
        if self._flags & self.FLAG_CONTRACT:
            badge = QGraphicsEllipseItem(-5, -5, 10, 10, self)
            badge.setBrush(QBrush(QColor("#F39C12")))
            badge.setPen(QPen(Qt.PenStyle.NoPen))
            badge.setPos(offset_x, 2)
            badge.setToolTip("合同即将到期")
            txt = QGraphicsTextItem("!", badge)
            txt.setDefaultTextColor(QColor("white"))
            tf = QFont("Microsoft YaHei", 5, QFont.Weight.Bold)
            txt.setFont(tf)
            txt.setPos(-txt.boundingRect().width()/2 + 0.5,
                       -txt.boundingRect().height()/2)
            offset_x -= 14
        if self._flags & self.FLAG_RISK:
            dot = QGraphicsEllipseItem(-5, -5, 10, 10, self)
            dot.setBrush(QBrush(QColor("#C0392B")))
            dot.setPen(QPen(Qt.PenStyle.NoPen))
            dot.setPos(offset_x, 2)
            dot.setToolTip("高流失风险")

    def set_highlighted(self, on: bool):
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
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if (self.pos() - self._drag_start).manhattanLength() > 5:
                self._scene_owner.try_reassign_member(self)


# ── Dept / Group nodes ────────────────────────────────────────────────────────

class DeptNode(QGraphicsRectItem):
    NODE_TYPE = "dept"

    def __init__(self, dept_id, name, x, y, scene_owner):
        super().__init__(0, 0, _DEPT_W, _DEPT_H)
        self._id   = dept_id
        self._name = name
        self._scene_owner = scene_owner
        self._drag_start  = QPointF()
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#003087")))
        self.setPen(QPen(QColor("#001f5e"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"部门: {name}")

        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        bh = lbl.boundingRect().height()
        lbl.setPos((_DEPT_W - bw) / 2, (_DEPT_H - bh) / 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.pos()
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        super().hoverEnterEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { border-radius:8px; padding:4px; }"
            "QMenu::item { padding:6px 16px; border-radius:4px; }"
            "QMenu::item:selected { background:#E8F0FE; color:#003087; }"
        )
        menu.addAction("新增小组",  lambda: self._scene_owner.request_add_group(self._id, self._name))
        menu.addAction("编辑部门",  lambda: self._scene_owner.request_edit_dept(self._id, self._name))
        menu.addAction("删除部门",  lambda: self._scene_owner.request_delete_dept(self._id, self._name))
        menu.exec(event.screenPos())


class GroupNode(QGraphicsRectItem):
    NODE_TYPE = "group"

    def __init__(self, group_id, dept_id, name, x, y, scene_owner):
        super().__init__(0, 0, _GRP_W, _GRP_H)
        self._id          = group_id
        self._dept_id     = dept_id
        self._name        = name
        self._scene_owner = scene_owner
        self._drag_start  = QPointF()
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#005C99")))
        self.setPen(QPen(QColor("#003087"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"小组: {name}（可拖至其他部门调整归属）")

        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 9)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        bh = lbl.boundingRect().height()
        lbl.setPos((_GRP_W - bw) / 2, (_GRP_H - bh) / 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if (self.pos() - self._drag_start).manhattanLength() > 5:
                self._scene_owner.try_reassign_group(self)

    def hoverEnterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        super().hoverEnterEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { border-radius:8px; padding:4px; }"
            "QMenu::item { padding:6px 16px; border-radius:4px; }"
            "QMenu::item:selected { background:#E8F0FE; color:#003087; }"
        )
        menu.addAction("编辑小组", lambda: self._scene_owner.request_edit_group(self._id, self._name))
        menu.addAction("删除小组", lambda: self._scene_owner.request_delete_group(self._id, self._name))
        menu.exec(event.screenPos())


# ── OrgScene ──────────────────────────────────────────────────────────────────

class OrgScene(QGraphicsScene):
    employee_clicked = pyqtSignal(str)

    def __init__(self, managers: dict, parent_widget=None):
        super().__init__()
        self._mgr    = managers
        self._parent = parent_widget
        self._member_nodes: list[MemberNode] = []
        self._group_nodes:  list[GroupNode]  = []
        self._dept_nodes:   list[DeptNode]   = []

    def member_clicked(self, employee_id: str):
        self.employee_clicked.emit(employee_id)

    # ── Reassign helpers ──

    def try_reassign_member(self, mbr_node: MemberNode):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            if self._parent: self._parent.refresh()
            return
        mbr_rect = mbr_node.mapToScene(mbr_node.boundingRect()).boundingRect()
        best_grp, best_overlap = None, 0.0
        for grp in self._group_nodes:
            grp_rect = grp.mapToScene(grp.boundingRect()).boundingRect()
            inter = mbr_rect.intersected(grp_rect)
            area  = inter.width() * inter.height()
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

    def try_reassign_group(self, grp_node: GroupNode):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            if self._parent: self._parent.refresh()
            return
        grp_rect = grp_node.mapToScene(grp_node.boundingRect()).boundingRect()
        best_dept, best_overlap = None, 0.0
        for dept in self._dept_nodes:
            dept_rect = dept.mapToScene(dept.boundingRect()).boundingRect()
            inter = grp_rect.intersected(dept_rect)
            area  = inter.width() * inter.height()
            if area > best_overlap:
                best_overlap = area
                best_dept = dept
        if best_dept and best_overlap > 100 and best_dept._id != grp_node._dept_id:
            try:
                emp_mgr.reassign_group_dept(grp_node._id, best_dept._id)
            except Exception as e:
                print(f"[OrgScene] reassign_group_dept error: {e}")
        if self._parent:
            self._parent.refresh()

    # ── Context menu dispatchers ──

    def request_add_group(self, dept_id, dept_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr: return
        name, ok = QInputDialog.getText(
            self._parent, "新增小组", f"部门 [{dept_name}] 的新小组名称:"
        )
        if ok and name.strip():
            emp_mgr.add_group(dept_id, name.strip())
            if self._parent: self._parent.refresh()

    def request_edit_dept(self, dept_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr: return
        name, ok = QInputDialog.getText(
            self._parent, "编辑部门", "部门名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_department(dept_id, name.strip())
            if self._parent: self._parent.refresh()

    def request_delete_dept(self, dept_id, dept_name):
        if QMessageBox.question(
            self._parent, "确认删除",
            f"确定删除部门 [{dept_name}]？相关员工部门归属将被清空。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_department(dept_id)
                if self._parent: self._parent.refresh()

    def request_edit_group(self, group_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr: return
        name, ok = QInputDialog.getText(
            self._parent, "编辑小组", "小组名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_group(group_id, name.strip())
            if self._parent: self._parent.refresh()

    def request_delete_group(self, group_id, group_name):
        if QMessageBox.question(
            self._parent, "确认删除",
            f"确定删除小组 [{group_name}]？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_group(group_id)
                if self._parent: self._parent.refresh()


# ── OrgChartView ──────────────────────────────────────────────────────────────

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
            "background:#F5F7FA; border:1px solid #DDE3EE; border-radius:12px;"
        )
        self._panning  = False
        self._pan_start = QPointF()
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.viewport():
            t = event.type()
            if t == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.MiddleButton:
                self._panning  = True
                self._pan_start = event.position()
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                return True
            elif t == QEvent.Type.MouseMove and self._panning:
                delta = event.position() - self._pan_start
                self._pan_start = event.position()
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - int(delta.x()))
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - int(delta.y()))
                return True
            elif t == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.MiddleButton:
                self._panning = False
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                return True
        return super().eventFilter(obj, event)

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


# ── DashboardPage ─────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    employee_selected = pyqtSignal(str)

    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self._member_nodes: list[MemberNode] = []
        self.setStyleSheet("background:#F5F7FA;")
        self._scene = OrgScene(managers, parent_widget=self)
        self._scene.employee_clicked.connect(self._on_member_clicked)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("搜索姓名 / 工号...")
        self._search_box.setFixedHeight(32)
        self._search_box.setMaximumWidth(240)
        self._search_box.setStyleSheet(
            "QLineEdit { border:1px solid #DDE3EE; border-radius:16px;"
            " padding:0 12px; background:white; font-size:12px; }"
            "QLineEdit:focus { border-color:#165DFF; }"
        )
        self._search_box.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_box)
        toolbar.addStretch(1)

        for etype, border_clr in [("华为", "#2ECC71"), ("OD", "#3498DB"), ("外包", "#F39C12")]:
            bg = EMP_TYPE_BG.get(etype, "#F5F7FA")
            dot = QLabel(f"● {etype}")
            dot.setStyleSheet(
                f"color:{border_clr}; font-size:11px;"
                f" background:{bg}; border:1px solid {border_clr};"
                f" border-radius:10px; padding:2px 8px;"
            )
            toolbar.addWidget(dot)

        toolbar.addSpacing(12)
        for lbl, fn in [("放大",  lambda: self._view.scale(1.15, 1.15)),
                        ("缩小",  lambda: self._view.scale(1/1.15, 1/1.15)),
                        ("重置",  self._reset_view)]:
            btn = QPushButton(lbl)
            btn.setFixedHeight(30)
            btn.setStyleSheet(BTN_SECONDARY)
            btn.clicked.connect(fn)
            toolbar.addWidget(btn)

        add_dept_btn = QPushButton("+ 新增部门")
        add_dept_btn.setFixedHeight(30)
        add_dept_btn.setStyleSheet(BTN_PRIMARY)
        add_dept_btn.clicked.connect(self._add_dept)
        toolbar.addWidget(add_dept_btn)

        lay.addLayout(toolbar)

        hint = QLabel(
            "右键部门/小组节点管理 · 滚轮缩放 · 鼠标中键拖拽平移 · "
            "拖拽人员节点调整归属 · 拖拽小组节点至其他部门调整归属"
        )
        hint.setStyleSheet("color:#86909C; font-size:11px;")
        lay.addWidget(hint)

        # ── Splitter: chart | detail panel ──
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background:#DDE3EE; }"
        )

        self._view = OrgChartView(self._scene)
        self._splitter.addWidget(self._view)

        self._detail_panel = _DetailPanel()
        self._detail_panel.closed.connect(self._on_panel_closed)
        self._splitter.addWidget(self._detail_panel)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)

        lay.addWidget(self._splitter, 1)

        self._load_tree()

    # ── Tree loading ──

    def _load_tree(self):
        self._scene.clear()
        self._member_nodes.clear()
        self._scene._member_nodes.clear()
        self._scene._group_nodes.clear()
        self._scene._dept_nodes.clear()

        emp_mgr  = self._mgr.get("employee")
        cont_mgr = self._mgr.get("contract")
        stab_mgr = self._mgr.get("stability")
        if not emp_mgr:
            self._scene.addText("暂无数据（未连接员工管理器）").setDefaultTextColor(QColor("#999"))
            return

        depts        = emp_mgr.list_departments()
        groups_all   = emp_mgr.list_groups()
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

        # ── Horizontal layout pass ──
        # Each group column = _GRP_W wide.  Members same width → center-align.
        dept_x = _DEPT_GAP // 2

        for dept in depts:
            did = dept["dept_id"]
            gs  = groups_by_dept.get(did, [])

            # Compute column X positions for each group
            grp_cols = []   # (grp_left_x, members_list)
            cx = dept_x
            for g in gs:
                grp_cols.append((cx, emps_by_group.get(g["group_id"], [])))
                cx += _GRP_W + _X_GAP
            if gs:
                dept_col_w = cx - _X_GAP - dept_x
            else:
                direct_members = emps_by_dept.get(did, [])
                dept_col_w = max(_DEPT_W, len(direct_members) * (_MBR_W + _X_GAP) - _X_GAP)

            # Dept node: centered over its groups
            dept_cx  = dept_x + dept_col_w / 2
            dept_node_x = dept_cx - _DEPT_W / 2
            dept_node = DeptNode(did, dept["dept_name"], dept_node_x, _Y_DEPT, self._scene)
            self._scene.addItem(dept_node)
            self._scene._dept_nodes.append(dept_node)
            dept_bot_y = _Y_DEPT + _DEPT_H

            # ── Group nodes + members ──
            grp_centers_x = []
            for g, (grp_left_x, members) in zip(gs, grp_cols):
                gid = g["group_id"]
                grp_cx_abs = grp_left_x + _GRP_W / 2  # absolute center X

                grp_node = GroupNode(gid, did, g["group_name"],
                                     grp_left_x, _Y_GRP, self._scene)
                self._scene.addItem(grp_node)
                self._scene._group_nodes.append(grp_node)
                grp_centers_x.append(grp_cx_abs)

                # Sort members: PL first, then 华为→OD→外包, then by name
                members = sorted(members, key=_member_sort_key)

                # Member nodes (single vertical column, centered under group)
                mbr_top_ys = []
                for idx, e in enumerate(members):
                    flags = 0
                    if e.employee_id in high_risk_ids: flags |= MemberNode.FLAG_RISK
                    if e.employee_id in expiring_ids:  flags |= MemberNode.FLAG_CONTRACT

                    mbr_x = grp_left_x  # left-align member with group
                    mbr_y = _Y_MBR0 + idx * (_MBR_H + _MBR_VGAP)
                    mbr_top_ys.append(mbr_y)

                    mnode = MemberNode(
                        e.employee_id, e.name, e.employee_type or "",
                        flags, mbr_x, mbr_y, self._scene,
                    )
                    self._scene.addItem(mnode)
                    self._member_nodes.append(mnode)
                    self._scene._member_nodes.append(mnode)

                # Group → member connectors
                grp_bot_y = _Y_GRP + _GRP_H
                _draw_group_to_members(self._scene, grp_cx_abs, grp_bot_y, mbr_top_ys)

            # Dept → group connectors
            _draw_dept_to_groups(self._scene, dept_cx, dept_bot_y, grp_centers_x)

            # Direct members under dept (no group)
            direct = emps_by_dept.get(did, [])
            if direct:
                direct = sorted(direct, key=_member_sort_key)
                dm_x = dept_x
                dm_top_ys = []
                for idx, e in enumerate(direct):
                    flags = 0
                    if e.employee_id in high_risk_ids: flags |= MemberNode.FLAG_RISK
                    if e.employee_id in expiring_ids:  flags |= MemberNode.FLAG_CONTRACT
                    mbr_y = _Y_MBR0 + idx * (_MBR_H + _MBR_VGAP)
                    dm_top_ys.append(mbr_y)
                    mnode = MemberNode(
                        e.employee_id, e.name, e.employee_type or "",
                        flags, dm_x, mbr_y, self._scene,
                    )
                    self._scene.addItem(mnode)
                    self._member_nodes.append(mnode)
                    self._scene._member_nodes.append(mnode)
                _draw_group_to_members(self._scene, dept_cx, dept_bot_y, dm_top_ys)

            dept_x = dept_x + dept_col_w + _DEPT_GAP

        if not depts:
            ph = self._scene.addText("暂无部门数据，请先在基础信息中添加部门")
            ph.setDefaultTextColor(QColor("#999"))
            ph.setFont(QFont("Microsoft YaHei", 12))

    # ── Event handlers ──

    def _on_search(self, query: str):
        q = query.strip().lower()
        for node in self._member_nodes:
            match = bool(q and (q in node._name.lower() or q in node._id.lower()))
            node.set_highlighted(match)
            if match:
                self._view.centerOn(node)

    def _on_member_clicked(self, employee_id: str):
        emp_mgr  = self._mgr.get("employee")
        cont_mgr = self._mgr.get("contract")
        stab_mgr = self._mgr.get("stability")
        if not emp_mgr:
            return
        emp = emp_mgr.get_employee(employee_id)
        if not emp:
            return

        dept_name, group_name = "", ""
        if emp.dept_id:
            for d in emp_mgr.list_departments():
                if d["dept_id"] == emp.dept_id:
                    dept_name = d["dept_name"]; break
        if emp.group_id:
            for g in emp_mgr.list_groups():
                if g["group_id"] == emp.group_id:
                    group_name = g["group_name"]; break

        contract  = cont_mgr.get_active_contract(employee_id) if cont_mgr else None
        stability = stab_mgr.get_latest(employee_id)          if stab_mgr else None

        self._detail_panel.load(emp, dept_name, group_name, contract, stability)

        # Open detail panel if collapsed
        sizes = self._splitter.sizes()
        if sizes[1] < 50:
            total = sizes[0] + sizes[1]
            self._splitter.setSizes([max(400, total - 300), 300])

        self.employee_selected.emit(employee_id)

    def _on_panel_closed(self):
        total = sum(self._splitter.sizes())
        self._splitter.setSizes([total, 0])

    def _reset_view(self):
        self._view.resetTransform()
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(
                rect.adjusted(-20, -20, 20, 20),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

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
