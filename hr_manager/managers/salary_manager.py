"""SalaryManager — CRUD with field-level AES encryption on sensitive amounts."""
from db.database import DatabaseManager
from db.crypto import FieldCrypto
from db.models import Salary


class SalaryManager:
    def __init__(self, db: DatabaseManager, crypto: FieldCrypto):
        self._db = db
        self._crypto = crypto

    def _decrypt_row(self, row) -> Salary:
        if not row:
            return None
        def _f(v): return float(self._crypto.decrypt(v) or "0") if v else 0.0
        return Salary(
            salary_id=row["salary_id"],
            employee_id=row["employee_id"],
            employee_name=row["name"] if "name" in row.keys() else "",
            effective_date=row["effective_date"] or "",
            base_salary=_f(row["base_salary"]),
            performance_pay=_f(row["performance_pay"]),
            total_salary=_f(row["total_salary"]),
            cr=row["cr"] or 0.0,
            pay_band=row["pay_band"] or "",
            band_min=row["band_min"] or 0.0,
            band_mid=row["band_mid"] or 0.0,
            band_max=row["band_max"] or 0.0,
            bonus_last=row["bonus_last"] or 0.0,
            raise_source=row["raise_source"] or "",
            raise_reason=row["raise_reason"] or "",
            planned_raise_date=row["planned_raise_date"] or "",
            planned_raise_amount=row["planned_raise_amount"] or 0.0,
            approved_by=row["approved_by"] or "",
            created_at=row["created_at"] or "",
        )

    def get_history(self, employee_id: str) -> list[Salary]:
        rows = self._db.fetchall(
            "SELECT s.*, e.name FROM salaries s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.effective_date DESC",
            (employee_id,),
        )
        return [self._decrypt_row(r) for r in rows]

    def get_current(self, employee_id: str) -> Salary | None:
        row = self._db.fetchone(
            "SELECT s.*, e.name FROM salaries s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.effective_date DESC LIMIT 1",
            (employee_id,),
        )
        return self._decrypt_row(row)

    def add_record(self, s: Salary) -> bool:
        try:
            self._db.execute(
                """INSERT INTO salaries
                   (employee_id, effective_date, base_salary, performance_pay, total_salary,
                    cr, pay_band, band_min, band_mid, band_max, bonus_last,
                    raise_source, raise_reason, planned_raise_date, planned_raise_amount, approved_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    s.employee_id, s.effective_date,
                    self._crypto.encrypt(str(s.base_salary)),
                    self._crypto.encrypt(str(s.performance_pay)),
                    self._crypto.encrypt(str(s.total_salary)),
                    s.cr, s.pay_band, s.band_min, s.band_mid, s.band_max,
                    s.bonus_last, s.raise_source, s.raise_reason,
                    s.planned_raise_date, s.planned_raise_amount, s.approved_by,
                ),
            )
            return True
        except Exception as e:
            print(f"[SalaryManager] add error: {e}")
            return False

    def update_record(self, s: Salary) -> bool:
        try:
            self._db.execute(
                """UPDATE salaries SET
                   effective_date=?, base_salary=?, performance_pay=?, total_salary=?,
                   cr=?, pay_band=?, band_min=?, band_mid=?, band_max=?,
                   bonus_last=?, raise_source=?, raise_reason=?,
                   planned_raise_date=?, planned_raise_amount=?, approved_by=?
                WHERE salary_id=?""",
                (
                    s.effective_date,
                    self._crypto.encrypt(str(s.base_salary)),
                    self._crypto.encrypt(str(s.performance_pay)),
                    self._crypto.encrypt(str(s.total_salary)),
                    s.cr, s.pay_band, s.band_min, s.band_mid, s.band_max,
                    s.bonus_last, s.raise_source, s.raise_reason,
                    s.planned_raise_date, s.planned_raise_amount, s.approved_by,
                    s.salary_id,
                ),
            )
            return True
        except Exception as e:
            print(f"[SalaryManager] update error: {e}")
            return False

    def delete_record(self, salary_id: int) -> bool:
        try:
            self._db.execute("DELETE FROM salaries WHERE salary_id=?", (salary_id,))
            return True
        except Exception:
            return False
