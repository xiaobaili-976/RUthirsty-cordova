"""EmployeeManager — CRUD for employees table."""
from db.database import DatabaseManager
from db.models import Employee
from datetime import datetime


class EmployeeManager:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def _row_to_emp(self, row) -> Employee:
        if not row:
            return None
        return Employee(
            employee_id=row["employee_id"],
            name=row["name"],
            gender=row["gender"] or "",
            dob=row["dob"] or "",
            id_number=row["id_number"] or "",
            phone=row["phone"] or "",
            email=row["email"] or "",
            bachelor_school=row["bachelor_school"] or "",
            bachelor_major=row["bachelor_major"] or "",
            bachelor_grad_year=row["bachelor_grad_year"] or "",
            master_school=row["master_school"] or "",
            master_major=row["master_major"] or "",
            master_grad_year=row["master_grad_year"] or "",
            education_level=row["education_level"] or "",
            dept_id=row["dept_id"],
            group_id=row["group_id"],
            job_title=row["job_title"] or "",
            job_level=row["job_level"] or "",
            job_grade=row["job_grade"] or "",
            qualification=row["qualification"] or "",
            perf_latest=row["perf_latest"] or "",
            perf_3y=row["perf_3y"] or "",
            perf_5times=row["perf_5times"] or "",
            perf_5y=row["perf_5y"] or "",
            status=row["status"] or "active",
            employee_type=row["employee_type"] if "employee_type" in row.keys() else "",
            avatar_path=row["avatar_path"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def list_employees(self, dept_id=None, group_id=None, status=None) -> list[Employee]:
        sql = "SELECT * FROM employees WHERE 1=1"
        params = []
        if dept_id is not None:
            sql += " AND dept_id=?"
            params.append(dept_id)
        if group_id is not None:
            sql += " AND group_id=?"
            params.append(group_id)
        if status is not None:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY name"
        rows = self._db.fetchall(sql, tuple(params))
        return [self._row_to_emp(r) for r in rows]

    def get_employee(self, employee_id: str) -> Employee | None:
        row = self._db.fetchone(
            "SELECT * FROM employees WHERE employee_id=?", (employee_id,)
        )
        return self._row_to_emp(row)

    def search(self, query: str) -> list[Employee]:
        q = f"%{query}%"
        rows = self._db.fetchall(
            "SELECT * FROM employees WHERE name LIKE ? OR employee_id LIKE ?"
            " OR job_title LIKE ? ORDER BY name",
            (q, q, q),
        )
        return [self._row_to_emp(r) for r in rows]

    def add_employee(self, emp: Employee) -> bool:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._db.execute(
                """INSERT INTO employees (
                    employee_id, name, gender, dob, id_number, phone, email,
                    bachelor_school, bachelor_major, bachelor_grad_year,
                    master_school, master_major, master_grad_year, education_level,
                    dept_id, group_id, job_title, job_level, job_grade, qualification,
                    perf_latest, perf_3y, perf_5times, perf_5y,
                    employee_type, status, avatar_path, notes, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    emp.employee_id, emp.name, emp.gender, emp.dob,
                    emp.id_number, emp.phone, emp.email,
                    emp.bachelor_school, emp.bachelor_major, emp.bachelor_grad_year,
                    emp.master_school, emp.master_major, emp.master_grad_year,
                    emp.education_level,
                    emp.dept_id, emp.group_id,
                    emp.job_title, emp.job_level, emp.job_grade, emp.qualification,
                    emp.perf_latest, emp.perf_3y, emp.perf_5times, emp.perf_5y,
                    emp.employee_type, emp.status, emp.avatar_path, emp.notes, now, now,
                ),
            )
            return True
        except Exception as e:
            print(f"[EmployeeManager] add error: {e}")
            return False

    def update_employee(self, emp: Employee) -> bool:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._db.execute(
                """UPDATE employees SET
                    name=?, gender=?, dob=?, id_number=?, phone=?, email=?,
                    bachelor_school=?, bachelor_major=?, bachelor_grad_year=?,
                    master_school=?, master_major=?, master_grad_year=?, education_level=?,
                    dept_id=?, group_id=?, job_title=?, job_level=?, job_grade=?,
                    qualification=?, perf_latest=?, perf_3y=?, perf_5times=?, perf_5y=?,
                    employee_type=?, status=?, avatar_path=?, notes=?, updated_at=?
                WHERE employee_id=?""",
                (
                    emp.name, emp.gender, emp.dob, emp.id_number, emp.phone, emp.email,
                    emp.bachelor_school, emp.bachelor_major, emp.bachelor_grad_year,
                    emp.master_school, emp.master_major, emp.master_grad_year,
                    emp.education_level,
                    emp.dept_id, emp.group_id,
                    emp.job_title, emp.job_level, emp.job_grade, emp.qualification,
                    emp.perf_latest, emp.perf_3y, emp.perf_5times, emp.perf_5y,
                    emp.employee_type, emp.status, emp.avatar_path, emp.notes, now,
                    emp.employee_id,
                ),
            )
            return True
        except Exception as e:
            print(f"[EmployeeManager] update error: {e}")
            return False

    def delete_employee(self, employee_id: str) -> bool:
        try:
            self._db.execute(
                "DELETE FROM employees WHERE employee_id=?", (employee_id,)
            )
            return True
        except Exception as e:
            print(f"[EmployeeManager] delete error: {e}")
            return False

    def count(self) -> int:
        row = self._db.fetchone("SELECT COUNT(*) as n FROM employees")
        return row["n"] if row else 0

    # ── Department & Group helpers ────────────────────────────────────────
    def list_departments(self):
        return self._db.fetchall("SELECT * FROM departments ORDER BY sort_order, dept_name")

    def list_groups(self, dept_id=None):
        if dept_id is not None:
            return self._db.fetchall(
                "SELECT * FROM groups WHERE dept_id=? ORDER BY sort_order, group_name",
                (dept_id,),
            )
        return self._db.fetchall("SELECT * FROM groups ORDER BY sort_order, group_name")

    def add_department(self, name: str, description: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO departments (dept_name, description) VALUES (?,?)",
            (name, description),
        )
        return cur.lastrowid

    def update_department(self, dept_id: int, name: str, description: str = "",
                          head_employee_id: str = "") -> None:
        self._db.execute(
            "UPDATE departments SET dept_name=?, description=?, head_employee_id=? WHERE dept_id=?",
            (name, description, head_employee_id, dept_id),
        )

    def delete_department(self, dept_id: int) -> None:
        self._db.execute("DELETE FROM departments WHERE dept_id=?", (dept_id,))

    def add_group(self, dept_id: int, name: str, description: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO groups (dept_id, group_name, description) VALUES (?,?,?)",
            (dept_id, name, description),
        )
        return cur.lastrowid

    def update_group(self, group_id: int, name: str, description: str = "",
                     lead_employee_id: str = "") -> None:
        self._db.execute(
            "UPDATE groups SET group_name=?, description=?, lead_employee_id=? WHERE group_id=?",
            (name, description, lead_employee_id, group_id),
        )

    def reassign_group_dept(self, group_id: int, new_dept_id: int) -> None:
        self._db.execute(
            "UPDATE groups SET dept_id=? WHERE group_id=?",
            (new_dept_id, group_id),
        )

    def delete_group(self, group_id: int) -> None:
        self._db.execute("DELETE FROM groups WHERE group_id=?", (group_id,))
