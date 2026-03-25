"""
DatabaseManager — SQLite connection and schema initialization.
All managers receive a DatabaseManager instance; they call execute() directly.
"""
import sqlite3
import threading
import os
from typing import Optional


class DatabaseManager:
    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._local = threading.local()
        self.create_schema()

    def _conn(self) -> sqlite3.Connection:
        """Return a thread-local SQLite connection (auto-creates if needed)."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn = conn
        return self._local.conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._conn()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur

    def executemany(self, sql: str, params_list) -> None:
        conn = self._conn()
        conn.executemany(sql, params_list)
        conn.commit()

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn().execute(sql, params).fetchall()

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        return self._conn().execute(sql, params).fetchone()

    def create_schema(self) -> None:
        stmts = [
            # ── users ──────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'admin',
                created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── departments ────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS departments (
                dept_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_name        TEXT NOT NULL UNIQUE,
                description      TEXT DEFAULT '',
                head_employee_id TEXT DEFAULT '',
                sort_order       INTEGER DEFAULT 0,
                created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── groups ─────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS groups (
                group_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id          INTEGER NOT NULL
                                 REFERENCES departments(dept_id) ON DELETE CASCADE,
                group_name       TEXT NOT NULL,
                description      TEXT DEFAULT '',
                lead_employee_id TEXT DEFAULT '',
                sort_order       INTEGER DEFAULT 0,
                created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── employees ──────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS employees (
                employee_id        TEXT PRIMARY KEY,
                name               TEXT NOT NULL,
                gender             TEXT DEFAULT '',
                dob                TEXT DEFAULT '',
                id_number          TEXT DEFAULT '',
                phone              TEXT DEFAULT '',
                email              TEXT DEFAULT '',
                bachelor_school    TEXT DEFAULT '',
                bachelor_major     TEXT DEFAULT '',
                bachelor_grad_year TEXT DEFAULT '',
                master_school      TEXT DEFAULT '',
                master_major       TEXT DEFAULT '',
                master_grad_year   TEXT DEFAULT '',
                education_level    TEXT DEFAULT '',
                dept_id            INTEGER REFERENCES departments(dept_id) ON DELETE SET NULL,
                group_id           INTEGER REFERENCES groups(group_id) ON DELETE SET NULL,
                job_title          TEXT DEFAULT '',
                job_level          TEXT DEFAULT '',
                job_grade          TEXT DEFAULT '',
                qualification      TEXT DEFAULT '',
                perf_latest        TEXT DEFAULT '',
                perf_3y            TEXT DEFAULT '',
                perf_5times        TEXT DEFAULT '',
                perf_5y            TEXT DEFAULT '',
                employee_type      TEXT DEFAULT '',
                status             TEXT DEFAULT 'active',
                avatar_path        TEXT DEFAULT '',
                notes              TEXT DEFAULT '',
                created_at         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at         TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── contracts ──────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS contracts (
                contract_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id   TEXT NOT NULL
                              REFERENCES employees(employee_id) ON DELETE CASCADE,
                contract_type TEXT DEFAULT '',
                hire_date     TEXT NOT NULL,
                start_date    TEXT NOT NULL,
                end_date      TEXT DEFAULT '',
                renewal_date  TEXT DEFAULT '',
                probation_end TEXT DEFAULT '',
                status        TEXT DEFAULT 'active',
                notes         TEXT DEFAULT '',
                created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── salaries (sensitive fields encrypted) ──────────────────────
            """CREATE TABLE IF NOT EXISTS salaries (
                salary_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id          TEXT NOT NULL
                                     REFERENCES employees(employee_id) ON DELETE CASCADE,
                effective_date       TEXT NOT NULL,
                base_salary          TEXT NOT NULL DEFAULT '',
                performance_pay      TEXT NOT NULL DEFAULT '',
                total_salary         TEXT NOT NULL DEFAULT '',
                cr                   REAL DEFAULT 0.0,
                pay_band             TEXT DEFAULT '',
                band_min             REAL DEFAULT 0.0,
                band_mid             REAL DEFAULT 0.0,
                band_max             REAL DEFAULT 0.0,
                bonus_last           REAL DEFAULT 0.0,
                raise_source         TEXT DEFAULT '',
                raise_reason         TEXT DEFAULT '',
                planned_raise_date   TEXT DEFAULT '',
                planned_raise_amount REAL DEFAULT 0.0,
                approved_by          TEXT DEFAULT '',
                created_at           TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── positions ──────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS positions (
                position_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id     TEXT NOT NULL
                                REFERENCES employees(employee_id) ON DELETE CASCADE,
                effective_date  TEXT NOT NULL,
                level           TEXT DEFAULT '',
                grade           TEXT DEFAULT '',
                adjustment_type TEXT DEFAULT '',
                reason          TEXT DEFAULT '',
                approved_by     TEXT DEFAULT '',
                planned_date    TEXT DEFAULT '',
                planned_type    TEXT DEFAULT '',
                planned_source  TEXT DEFAULT '',
                created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── esop ───────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS esop (
                esop_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id      TEXT NOT NULL
                                 REFERENCES employees(employee_id) ON DELETE CASCADE,
                grant_date       TEXT NOT NULL,
                shares_granted   REAL DEFAULT 0.0,
                shares_vested    REAL DEFAULT 0.0,
                shares_unvested  REAL DEFAULT 0.0,
                annual_guideline REAL DEFAULT 0.0,
                grant_upper      REAL DEFAULT 0.0,
                grant_lower      REAL DEFAULT 0.0,
                talent_result    TEXT DEFAULT '',
                vest_schedule    TEXT DEFAULT '[]',
                plan_name        TEXT DEFAULT '',
                notes            TEXT DEFAULT '',
                created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
            # ── stability (sensitive fields encrypted) ─────────────────────
            """CREATE TABLE IF NOT EXISTS stability (
                stability_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id        TEXT NOT NULL
                                   REFERENCES employees(employee_id) ON DELETE CASCADE,
                assessment_date    TEXT NOT NULL,
                is_only_child      TEXT DEFAULT '',
                marital_status     TEXT DEFAULT '',
                children           TEXT DEFAULT '',
                family_jobs        TEXT DEFAULT '',
                address            TEXT DEFAULT '',
                commute_distance   TEXT DEFAULT '',
                housing            TEXT DEFAULT '',
                job_match          INTEGER DEFAULT 5,
                promotion_expectation TEXT DEFAULT '',
                growth_needs       TEXT DEFAULT '',
                transfer_willingness TEXT DEFAULT '',
                salary_level_expectation TEXT DEFAULT '',
                workload           INTEGER DEFAULT 5,
                daily_state        TEXT DEFAULT '',
                superior_cooperation INTEGER DEFAULT 5,
                team_integration   INTEGER DEFAULT 5,
                work_satisfaction  INTEGER DEFAULT 5,
                urgent_demand_type TEXT DEFAULT '',
                urgent_demand_detail TEXT DEFAULT '',
                family_harmony     INTEGER DEFAULT 5,
                major_family_events TEXT DEFAULT '',
                life_pressure      INTEGER DEFAULT 5,
                emotional_stability INTEGER DEFAULT 5,
                personality_type   TEXT DEFAULT '',
                hobbies            TEXT DEFAULT '',
                social_circle      TEXT DEFAULT '',
                value_alignment    INTEGER DEFAULT 5,
                family_score       TEXT NOT NULL DEFAULT '',
                career_score       TEXT NOT NULL DEFAULT '',
                work_score         TEXT NOT NULL DEFAULT '',
                overall_score      TEXT NOT NULL DEFAULT '',
                risk_level         TEXT NOT NULL DEFAULT 'green',
                risk_tags          TEXT DEFAULT '',
                comm_log           TEXT DEFAULT '',
                assessed_by        TEXT DEFAULT '',
                created_at         TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )""",
        ]
        conn = self._conn()
        for stmt in stmts:
            conn.execute(stmt)
        conn.commit()
        # ── Migrations for existing databases ──────────────────────────────
        self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Add columns that may not exist in older databases."""
        existing = {row[1] for row in conn.execute("PRAGMA table_info(employees)").fetchall()}
        if "employee_type" not in existing:
            conn.execute("ALTER TABLE employees ADD COLUMN employee_type TEXT DEFAULT ''")
            conn.commit()
