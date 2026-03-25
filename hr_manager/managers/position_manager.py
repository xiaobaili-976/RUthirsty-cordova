"""PositionManager — CRUD for positions table."""
from db.database import DatabaseManager
from db.models import Position


class PositionManager:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def _row_to_pos(self, row) -> Position:
        if not row:
            return None
        return Position(
            position_id=row["position_id"],
            employee_id=row["employee_id"],
            employee_name=row["name"] if "name" in row.keys() else "",
            effective_date=row["effective_date"] or "",
            level=row["level"] or "",
            grade=row["grade"] or "",
            adjustment_type=row["adjustment_type"] or "",
            reason=row["reason"] or "",
            approved_by=row["approved_by"] or "",
            planned_date=row["planned_date"] or "",
            planned_type=row["planned_type"] or "",
            planned_source=row["planned_source"] or "",
            created_at=row["created_at"] or "",
        )

    def get_history(self, employee_id: str) -> list[Position]:
        rows = self._db.fetchall(
            "SELECT p.*, e.name FROM positions p "
            "JOIN employees e ON p.employee_id=e.employee_id "
            "WHERE p.employee_id=? ORDER BY p.effective_date DESC",
            (employee_id,),
        )
        return [self._row_to_pos(r) for r in rows]

    def get_current(self, employee_id: str) -> Position | None:
        row = self._db.fetchone(
            "SELECT p.*, e.name FROM positions p "
            "JOIN employees e ON p.employee_id=e.employee_id "
            "WHERE p.employee_id=? ORDER BY p.effective_date DESC LIMIT 1",
            (employee_id,),
        )
        return self._row_to_pos(row)

    def add_record(self, p: Position) -> bool:
        try:
            self._db.execute(
                """INSERT INTO positions
                   (employee_id, effective_date, level, grade, adjustment_type,
                    reason, approved_by, planned_date, planned_type, planned_source)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (p.employee_id, p.effective_date, p.level, p.grade,
                 p.adjustment_type, p.reason, p.approved_by,
                 p.planned_date, p.planned_type, p.planned_source),
            )
            return True
        except Exception as e:
            print(f"[PositionManager] add error: {e}")
            return False

    def update_record(self, p: Position) -> bool:
        try:
            self._db.execute(
                """UPDATE positions SET
                   effective_date=?, level=?, grade=?, adjustment_type=?,
                   reason=?, approved_by=?, planned_date=?, planned_type=?, planned_source=?
                WHERE position_id=?""",
                (p.effective_date, p.level, p.grade, p.adjustment_type,
                 p.reason, p.approved_by, p.planned_date, p.planned_type,
                 p.planned_source, p.position_id),
            )
            return True
        except Exception as e:
            return False

    def delete_record(self, position_id: int) -> bool:
        try:
            self._db.execute("DELETE FROM positions WHERE position_id=?", (position_id,))
            return True
        except Exception:
            return False
