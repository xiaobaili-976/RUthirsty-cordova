"""ContractManager — CRUD for contracts + auto countdown."""
from db.database import DatabaseManager
from db.models import Contract
from datetime import date, datetime


class ContractManager:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def _row_to_contract(self, row) -> Contract:
        if not row:
            return None
        return Contract(
            contract_id=row["contract_id"],
            employee_id=row["employee_id"],
            employee_name=row["name"] if "name" in row.keys() else "",
            contract_type=row["contract_type"] or "",
            hire_date=row["hire_date"] or "",
            start_date=row["start_date"] or "",
            end_date=row["end_date"] or "",
            renewal_date=row["renewal_date"] or "",
            probation_end=row["probation_end"] or "",
            status=row["status"] or "active",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
        )

    def get_contracts(self, employee_id: str) -> list[Contract]:
        rows = self._db.fetchall(
            "SELECT c.*, e.name FROM contracts c "
            "JOIN employees e ON c.employee_id=e.employee_id "
            "WHERE c.employee_id=? ORDER BY c.start_date DESC",
            (employee_id,),
        )
        return [self._row_to_contract(r) for r in rows]

    def get_active_contract(self, employee_id: str) -> Contract | None:
        row = self._db.fetchone(
            "SELECT c.*, e.name FROM contracts c "
            "JOIN employees e ON c.employee_id=e.employee_id "
            "WHERE c.employee_id=? AND c.status='active' "
            "ORDER BY c.start_date DESC LIMIT 1",
            (employee_id,),
        )
        return self._row_to_contract(row)

    def add_contract(self, c: Contract) -> bool:
        try:
            self._db.execute(
                """INSERT INTO contracts
                   (employee_id, contract_type, hire_date, start_date,
                    end_date, renewal_date, probation_end, status, notes)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (c.employee_id, c.contract_type, c.hire_date, c.start_date,
                 c.end_date, c.renewal_date, c.probation_end, c.status, c.notes),
            )
            return True
        except Exception as e:
            print(f"[ContractManager] add error: {e}")
            return False

    def update_contract(self, c: Contract) -> bool:
        try:
            self._db.execute(
                """UPDATE contracts SET
                   contract_type=?, hire_date=?, start_date=?, end_date=?,
                   renewal_date=?, probation_end=?, status=?, notes=?
                WHERE contract_id=?""",
                (c.contract_type, c.hire_date, c.start_date, c.end_date,
                 c.renewal_date, c.probation_end, c.status, c.notes,
                 c.contract_id),
            )
            return True
        except Exception as e:
            print(f"[ContractManager] update error: {e}")
            return False

    def delete_contract(self, contract_id: int) -> bool:
        try:
            self._db.execute("DELETE FROM contracts WHERE contract_id=?", (contract_id,))
            return True
        except Exception as e:
            return False

    def get_expiring_soon(self, days: int = 270) -> list[dict]:
        """Return contracts whose renewal_date is within `days` days from today."""
        rows = self._db.fetchall(
            "SELECT c.*, e.name FROM contracts c "
            "JOIN employees e ON c.employee_id=e.employee_id "
            "WHERE c.status='active' AND c.renewal_date != ''",
        )
        today = date.today()
        result = []
        for r in rows:
            try:
                rd = date.fromisoformat(r["renewal_date"])
                d = (rd - today).days
                if 0 <= d <= days:
                    result.append({
                        "employee_id": r["employee_id"],
                        "name": r["name"],
                        "renewal_date": r["renewal_date"],
                        "days_left": d,
                        "contract_type": r["contract_type"],
                    })
            except ValueError:
                pass
        return sorted(result, key=lambda x: x["days_left"])

    def get_all_contracts(self) -> list[Contract]:
        rows = self._db.fetchall(
            "SELECT c.*, e.name FROM contracts c "
            "JOIN employees e ON c.employee_id=e.employee_id "
            "ORDER BY c.renewal_date"
        )
        return [self._row_to_contract(r) for r in rows]
