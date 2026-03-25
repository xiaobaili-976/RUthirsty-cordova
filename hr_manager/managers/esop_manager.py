"""EsopManager — CRUD for ESOP/long-term incentive table."""
from db.database import DatabaseManager
from db.models import Esop


class EsopManager:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def _row_to_esop(self, row) -> Esop:
        if not row:
            return None
        e = Esop(
            esop_id=row["esop_id"],
            employee_id=row["employee_id"],
            employee_name=row["name"] if "name" in row.keys() else "",
            grant_date=row["grant_date"] or "",
            shares_granted=row["shares_granted"] or 0.0,
            shares_vested=row["shares_vested"] or 0.0,
            shares_unvested=row["shares_unvested"] or 0.0,
            annual_guideline=row["annual_guideline"] or 0.0,
            grant_upper=row["grant_upper"] or 0.0,
            grant_lower=row["grant_lower"] or 0.0,
            talent_result=row["talent_result"] or "",
            vest_schedule=row["vest_schedule"] or "[]",
            plan_name=row["plan_name"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
        )
        e.saturation = e.compute_saturation()
        return e

    def get_records(self, employee_id: str) -> list[Esop]:
        rows = self._db.fetchall(
            "SELECT s.*, e.name FROM esop s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.grant_date DESC",
            (employee_id,),
        )
        return [self._row_to_esop(r) for r in rows]

    def get_current(self, employee_id: str) -> Esop | None:
        row = self._db.fetchone(
            "SELECT s.*, e.name FROM esop s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.grant_date DESC LIMIT 1",
            (employee_id,),
        )
        return self._row_to_esop(row)

    def add_record(self, s: Esop) -> bool:
        try:
            self._db.execute(
                """INSERT INTO esop
                   (employee_id, grant_date, shares_granted, shares_vested, shares_unvested,
                    annual_guideline, grant_upper, grant_lower, talent_result,
                    vest_schedule, plan_name, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (s.employee_id, s.grant_date, s.shares_granted, s.shares_vested,
                 s.shares_unvested, s.annual_guideline, s.grant_upper, s.grant_lower,
                 s.talent_result, s.vest_schedule, s.plan_name, s.notes),
            )
            return True
        except Exception as e:
            print(f"[EsopManager] add error: {e}")
            return False

    def update_record(self, s: Esop) -> bool:
        try:
            self._db.execute(
                """UPDATE esop SET
                   grant_date=?, shares_granted=?, shares_vested=?, shares_unvested=?,
                   annual_guideline=?, grant_upper=?, grant_lower=?, talent_result=?,
                   vest_schedule=?, plan_name=?, notes=?
                WHERE esop_id=?""",
                (s.grant_date, s.shares_granted, s.shares_vested, s.shares_unvested,
                 s.annual_guideline, s.grant_upper, s.grant_lower, s.talent_result,
                 s.vest_schedule, s.plan_name, s.notes, s.esop_id),
            )
            return True
        except Exception as e:
            return False

    def delete_record(self, esop_id: int) -> bool:
        try:
            self._db.execute("DELETE FROM esop WHERE esop_id=?", (esop_id,))
            return True
        except Exception:
            return False
