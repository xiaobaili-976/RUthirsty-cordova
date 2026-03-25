"""OrgChartPage — org chart with departments, groups, and member nodes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem, QMenu, QInputDialog,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QFont, QTransform, QWheelEvent, QAction
)

from styles import (
    _BLUE, _GREEN, _LIGHT, _BORDER, _TEXT, _RED,
    BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER
)

_BLUE_LIGHT = "#E8F0FE"
_DEPT_W, _DEPT_H = 160, 56
_GRP_W, _GRP_H = 130, 44
_MBR_R = 24   # radius for member ellipse
_X_GAP = 20
_DEPT_Y = 20
_GRP_Y = 160
_MBR_Y = 310


# ── Node classes ─────────────────────────────────────────────────────────────

class DeptNode(QGraphicsRectItem):
    NODE_TYPE = "dept"

    def __init__(self, dept_id, name, x, y, scene_owner):
        super().__init__(0, 0, _DEPT_W, _DEPT_H)
        self._id = dept_id
        self._name = name
        self._scene_owner = scene_owner
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(_BLUE)))
        self.setPen(QPen(QColor("#001f5e"), 1.5))
        self.setToolTip(f"部门: {name}")
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        # label
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        lbl.setPos((_DEPT_W - bw) / 2, (_DEPT_H - lbl.boundingRect().height()) / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("新增小组", lambda: self._scene_owner.request_add_group(self._id, self._name))
        menu.addAction("编辑部门", lambda: self._scene_owner.request_edit_dept(self._id, self._name))
        act_del = menu.addAction("删除部门", lambda: self._scene_owner.request_delete_dept(self._id, self._name))
        act_del.setForeground(QColor(_RED))
        menu.exec(event.screenPos())


class GroupNode(QGraphicsRectItem):
    NODE_TYPE = "group"

    def __init__(self, group_id, name, x, y, scene_owner):
        super().__init__(0, 0, _GRP_W, _GRP_H)
        self._id = group_id
        self._name = name
        self._scene_owner = scene_owner
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(_GREEN)))
        self.setPen(QPen(QColor("#1a7a43"), 1.5))
        self.setToolTip(f"小组: {name}")
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        lbl = QGraphicsTextItem(name, self)
        lbl.setDefaultTextColor(QColor("white"))
        f = QFont("Microsoft YaHei", 9)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        lbl.setPos((_GRP_W - bw) / 2, (_GRP_H - lbl.boundingRect().height()) / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("编辑小组", lambda: self._scene_owner.request_edit_group(self._id, self._name))
        act_del = menu.addAction("删除小组", lambda: self._scene_owner.request_delete_group(self._id, self._name))
        act_del.setForeground(QColor(_RED))
        menu.exec(event.screenPos())


class MemberNode(QGraphicsEllipseItem):
    NODE_TYPE = "member"

    def __init__(self, employee_id, name, x, y, scene_owner):
        d = _MBR_R * 2
        super().__init__(0, 0, d, d)
        self._id = employee_id
        self._name = name
        self._scene_owner = scene_owner
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(_BLUE_LIGHT)))
        self.setPen(QPen(QColor(_BLUE), 1.5))
        self.setToolTip(f"{name} ({employee_id})")
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        # initials label
        initials = name[:1] if name else "?"
        lbl = QGraphicsTextItem(initials, self)
        lbl.setDefaultTextColor(QColor(_BLUE))
        f = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
        lbl.setFont(f)
        bw = lbl.boundingRect().width()
        bh = lbl.boundingRect().height()
        lbl.setPos((d - bw) / 2, (d - bh) / 2)
        # name below
        name_lbl = QGraphicsTextItem(name, self)
        name_lbl.setDefaultTextColor(QColor(_TEXT))
        fn = QFont("Microsoft YaHei", 8)
        name_lbl.setFont(fn)
        nw = name_lbl.boundingRect().width()
        name_lbl.setPos((d - nw) / 2, d + 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._scene_owner.member_clicked(self._id)
        super().mousePressEvent(event)


# ── OrgScene ─────────────────────────────────────────────────────────────────

class OrgScene(QGraphicsScene):
    employee_selected = pyqtSignal(str)

    def __init__(self, managers: dict, parent_widget=None):
        super().__init__()
        self._mgr = managers
        self._parent_widget = parent_widget

    def member_clicked(self, employee_id: str):
        self.employee_selected.emit(employee_id)

    def request_add_group(self, dept_id, dept_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent_widget, "新增小组", f"部门 [{dept_name}] 的新小组名称:"
        )
        if ok and name.strip():
            emp_mgr.add_group(dept_id, name.strip())
            if self._parent_widget:
                self._parent_widget.refresh()

    def request_edit_dept(self, dept_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent_widget, "编辑部门", "部门名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_department(dept_id, name.strip())
            if self._parent_widget:
                self._parent_widget.refresh()

    def request_delete_dept(self, dept_id, dept_name):
        if QMessageBox.question(
            self._parent_widget, "确认删除",
            f"确定删除部门 [{dept_name}]？相关员工部门归属将被清空。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_department(dept_id)
                if self._parent_widget:
                    self._parent_widget.refresh()

    def request_edit_group(self, group_id, current_name):
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            return
        name, ok = QInputDialog.getText(
            self._parent_widget, "编辑小组", "小组名称:", text=current_name
        )
        if ok and name.strip():
            emp_mgr.update_group(group_id, name.strip())
            if self._parent_widget:
                self._parent_widget.refresh()

    def request_delete_group(self, group_id, group_name):
        if QMessageBox.question(
            self._parent_widget, "确认删除",
            f"确定删除小组 [{group_name}]？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            emp_mgr = self._mgr.get("employee")
            if emp_mgr:
                emp_mgr.delete_group(group_id)
                if self._parent_widget:
                    self._parent_widget.refresh()


# ── OrgChartView ─────────────────────────────────────────────────────────────

class OrgChartView(QGraphicsView):
    def __init__(self, scene: OrgScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(
            self.renderHints() |
            self.renderHints().__class__.Antialiasing |
            self.renderHints().__class__.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet(f"background: {_LIGHT}; border: 1px solid {_BORDER}; border-radius: 6px;")

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


# ── OrgChartPage ─────────────────────────────────────────────────────────────

class OrgChartPage(QWidget):
    employee_selected = pyqtSignal(str)

    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        self._mgr = managers
        self.setStyleSheet("background:#F5F7FA;")
        self._scene = OrgScene(managers, parent_widget=self)
        self._scene.employee_selected.connect(self.employee_selected)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("组织架构图")
        title.setStyleSheet(f"color:{_BLUE}; font-size:18px; font-weight:bold;")
        title_row.addWidget(title)
        title_row.addStretch(1)

        # Zoom + refresh buttons
        zoom_in_btn = QPushButton("放大 +")
        zoom_in_btn.setStyleSheet(BTN_SECONDARY)
        zoom_in_btn.setFixedHeight(30)
        zoom_in_btn.clicked.connect(lambda: self._view.scale(1.15, 1.15))
        title_row.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("缩小 -")
        zoom_out_btn.setStyleSheet(BTN_SECONDARY)
        zoom_out_btn.setFixedHeight(30)
        zoom_out_btn.clicked.connect(lambda: self._view.scale(1 / 1.15, 1 / 1.15))
        title_row.addWidget(zoom_out_btn)

        reset_btn = QPushButton("重置视图")
        reset_btn.setStyleSheet(BTN_SECONDARY)
        reset_btn.setFixedHeight(30)
        reset_btn.clicked.connect(self._reset_view)
        title_row.addWidget(reset_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(BTN_PRIMARY)
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(refresh_btn)

        lay.addLayout(title_row)

        # Info label
        self._info_lbl = QLabel("右键部门/小组节点可进行操作；滚轮缩放；拖拽平移")
        self._info_lbl.setStyleSheet(f"color:#888; font-size:11px;")
        lay.addWidget(self._info_lbl)

        # Graphics view
        self._view = OrgChartView(self._scene)
        lay.addWidget(self._view, 1)

        self._load_tree()

    def _load_tree(self):
        self._scene.clear()
        emp_mgr = self._mgr.get("employee")
        if not emp_mgr:
            placeholder = self._scene.addText("暂无数据（未连接员工管理器）")
            placeholder.setDefaultTextColor(QColor("#999"))
            return

        depts = emp_mgr.list_departments()
        groups_all = emp_mgr.list_groups()
        employees_all = emp_mgr.list_employees()

        # Build lookup maps
        groups_by_dept = {}
        for g in groups_all:
            groups_by_dept.setdefault(g["dept_id"], []).append(g)

        emps_by_group = {}
        emps_no_group = {}
        for e in employees_all:
            if e.group_id:
                emps_by_group.setdefault(e.group_id, []).append(e)
            elif e.dept_id:
                emps_no_group.setdefault(e.dept_id, []).append(e)

        # Layout: place depts horizontally, groups below each dept, members below groups
        dept_x = _X_GAP
        connector_pen = QPen(QColor("#AAB4C8"), 1.5, Qt.PenStyle.DashLine)

        for dept in depts:
            did = dept["dept_id"]
            dept_name = dept["dept_name"]

            # Determine column width for this dept
            gs = groups_by_dept.get(did, [])
            # Count total member columns in this dept
            member_count = sum(len(emps_by_group.get(g["group_id"], [])) for g in gs)
            member_count += len(emps_no_group.get(did, []))
            if not gs:
                col_w = max(_DEPT_W, member_count * (_MBR_R * 2 + _X_GAP) + _X_GAP)
            else:
                col_w = max(_DEPT_W, len(gs) * (_GRP_W + _X_GAP) + _X_GAP)

            dept_cx = dept_x + col_w / 2 - _DEPT_W / 2
            dept_node = DeptNode(did, dept_name, dept_cx, _DEPT_Y, self._scene)
            self._scene.addItem(dept_node)

            dept_bottom_x = dept_cx + _DEPT_W / 2
            dept_bottom_y = _DEPT_Y + _DEPT_H

            # Groups under this dept
            grp_x = dept_x
            for g in gs:
                gid = g["group_id"]
                gname = g["group_name"]
                grp_cx = grp_x + (_GRP_W / 2)
                grp_node = GroupNode(gid, gname, grp_x, _GRP_Y, self._scene)
                self._scene.addItem(grp_node)

                # Connector dept -> group
                line = QGraphicsLineItem(
                    dept_bottom_x, dept_bottom_y,
                    grp_x + _GRP_W / 2, _GRP_Y
                )
                line.setPen(connector_pen)
                self._scene.addItem(line)

                # Members under this group
                grp_members = emps_by_group.get(gid, [])
                mbr_start_x = grp_x - (len(grp_members) - 1) * (_MBR_R * 2 + _X_GAP) / 2
                for i, e in enumerate(grp_members):
                    mx = mbr_start_x + i * (_MBR_R * 2 + _X_GAP)
                    my = _MBR_Y
                    mbr_node = MemberNode(e.employee_id, e.name, mx, my, self._scene)
                    self._scene.addItem(mbr_node)
                    # Connector group -> member
                    mline = QGraphicsLineItem(
                        grp_x + _GRP_W / 2, _GRP_Y + _GRP_H,
                        mx + _MBR_R, my
                    )
                    mline.setPen(connector_pen)
                    self._scene.addItem(mline)

                grp_x += _GRP_W + _X_GAP

            # Members directly under dept (no group)
            direct_members = emps_no_group.get(did, [])
            dm_x = dept_x
            for e in direct_members:
                my = _MBR_Y
                mbr_node = MemberNode(e.employee_id, e.name, dm_x, my, self._scene)
                self._scene.addItem(mbr_node)
                dline = QGraphicsLineItem(
                    dept_bottom_x, dept_bottom_y,
                    dm_x + _MBR_R, my
                )
                dline.setPen(connector_pen)
                self._scene.addItem(dline)
                dm_x += _MBR_R * 2 + _X_GAP

            dept_x += col_w + _X_GAP * 2

        if not depts:
            placeholder = self._scene.addText("暂无部门数据，请先在员工管理中添加部门")
            placeholder.setDefaultTextColor(QColor("#999"))
            f = QFont("Microsoft YaHei", 12)
            placeholder.setFont(f)

    def _reset_view(self):
        self._view.resetTransform()
        self._view.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def refresh(self):
        self._load_tree()
        self._view.resetTransform()
