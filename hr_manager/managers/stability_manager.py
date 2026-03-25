"""StabilityManager — CRUD for stability barometer with encrypted scores."""
import json
from db.database import DatabaseManager
from db.crypto import FieldCrypto
from db.models import Stability, CommLogEntry
from datetime import datetime


class StabilityManager:
    def __init__(self, db: DatabaseManager, crypto: FieldCrypto):
        self._db = db
        self._crypto = crypto

    def compute_risk_level(self, family: float, career: float, work: float) -> str:
        avg = (family + career + work) / 3.0
        if avg >= 7:
            return "green"
        elif avg >= 4:
            return "yellow"
        return "red"

    def _decode(self, row) -> Stability:
        if not row:
            return None
        def _sf(v): return float(self._crypto.decrypt(v) or "5") if v else 5.0

        comm_raw = self._crypto.decrypt(row["comm_log"]) if row["comm_log"] else "[]"
        try:
            comm_entries_raw = json.loads(comm_raw)
            comm_log = [CommLogEntry(**e) for e in comm_entries_raw]
        except Exception:
            comm_log = []

        return Stability(
            stability_id=row["stability_id"],
            employee_id=row["employee_id"],
            employee_name=row["name"] if "name" in row.keys() else "",
            assessment_date=row["assessment_date"] or "",
            is_only_child=row["is_only_child"] or "",
            marital_status=row["marital_status"] or "",
            children=row["children"] or "",
            family_jobs=row["family_jobs"] or "",
            address=row["address"] or "",
            commute_distance=row["commute_distance"] or "",
            housing=row["housing"] or "",
            job_match=row["job_match"] or 5,
            promotion_expectation=row["promotion_expectation"] or "",
            growth_needs=row["growth_needs"] or "",
            transfer_willingness=row["transfer_willingness"] or "",
            salary_level_expectation=row["salary_level_expectation"] or "",
            workload=row["workload"] or 5,
            daily_state=row["daily_state"] or "",
            superior_cooperation=row["superior_cooperation"] or 5,
            team_integration=row["team_integration"] or 5,
            work_satisfaction=row["work_satisfaction"] or 5,
            urgent_demand_type=row["urgent_demand_type"] or "",
            urgent_demand_detail=row["urgent_demand_detail"] or "",
            family_harmony=row["family_harmony"] or 5,
            major_family_events=row["major_family_events"] or "",
            life_pressure=row["life_pressure"] or 5,
            emotional_stability=row["emotional_stability"] or 5,
            personality_type=row["personality_type"] or "",
            hobbies=row["hobbies"] or "",
            social_circle=row["social_circle"] or "",
            value_alignment=row["value_alignment"] or 5,
            family_score=_sf(row["family_score"]),
            career_score=_sf(row["career_score"]),
            work_score=_sf(row["work_score"]),
            overall_score=_sf(row["overall_score"]),
            risk_level=row["risk_level"] or "green",
            risk_tags=row["risk_tags"] or "",
            comm_log=comm_log,
            assessed_by=row["assessed_by"] or "",
            created_at=row["created_at"] or "",
        )

    def get_assessments(self, employee_id: str) -> list[Stability]:
        rows = self._db.fetchall(
            "SELECT s.*, e.name FROM stability s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.assessment_date DESC",
            (employee_id,),
        )
        return [self._decode(r) for r in rows]

    def get_latest(self, employee_id: str) -> Stability | None:
        row = self._db.fetchone(
            "SELECT s.*, e.name FROM stability s "
            "JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.employee_id=? ORDER BY s.assessment_date DESC LIMIT 1",
            (employee_id,),
        )
        return self._decode(row)

    def get_high_risk_employees(self) -> list[dict]:
        rows = self._db.fetchall(
            "SELECT s.employee_id, s.risk_level, s.risk_tags, s.assessment_date, e.name "
            "FROM stability s JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.risk_level='red' "
            "GROUP BY s.employee_id ORDER BY s.assessment_date DESC"
        )
        return [dict(r) for r in rows]

    def get_at_risk_employees(self) -> list[dict]:
        """Returns both red and yellow risk employees."""
        rows = self._db.fetchall(
            "SELECT s.employee_id, s.risk_level, s.risk_tags, s.assessment_date, e.name "
            "FROM stability s JOIN employees e ON s.employee_id=e.employee_id "
            "WHERE s.risk_level IN ('red','yellow') "
            "GROUP BY s.employee_id ORDER BY s.risk_level, s.assessment_date DESC"
        )
        return [dict(r) for r in rows]

    def add_assessment(self, s: Stability) -> bool:
        try:
            enc = self._crypto.encrypt
            comm_json = json.dumps(
                [vars(e) for e in s.comm_log], ensure_ascii=False
            )
            self._db.execute(
                """INSERT INTO stability (
                    employee_id, assessment_date,
                    is_only_child, marital_status, children, family_jobs,
                    address, commute_distance, housing,
                    job_match, promotion_expectation, growth_needs,
                    transfer_willingness, salary_level_expectation,
                    workload, daily_state, superior_cooperation,
                    team_integration, work_satisfaction,
                    urgent_demand_type, urgent_demand_detail,
                    family_harmony, major_family_events, life_pressure, emotional_stability,
                    personality_type, hobbies, social_circle, value_alignment,
                    family_score, career_score, work_score, overall_score,
                    risk_level, risk_tags, comm_log, assessed_by
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    s.employee_id, s.assessment_date,
                    s.is_only_child, s.marital_status, s.children, s.family_jobs,
                    s.address, s.commute_distance, s.housing,
                    s.job_match, s.promotion_expectation, s.growth_needs,
                    s.transfer_willingness, s.salary_level_expectation,
                    s.workload, s.daily_state, s.superior_cooperation,
                    s.team_integration, s.work_satisfaction,
                    s.urgent_demand_type, s.urgent_demand_detail,
                    s.family_harmony, s.major_family_events, s.life_pressure,
                    s.emotional_stability,
                    s.personality_type, s.hobbies, s.social_circle, s.value_alignment,
                    enc(str(s.family_score)), enc(str(s.career_score)),
                    enc(str(s.work_score)), enc(str(s.overall_score)),
                    s.risk_level, s.risk_tags,
                    enc(comm_json), s.assessed_by,
                ),
            )
            return True
        except Exception as e:
            print(f"[StabilityManager] add error: {e}")
            return False

    def add_comm_log_entry(self, stability_id: int, entry: CommLogEntry) -> bool:
        """Append a communication log entry to an existing assessment."""
        try:
            row = self._db.fetchone(
                "SELECT comm_log FROM stability WHERE stability_id=?", (stability_id,)
            )
            if not row:
                return False
            existing_json = self._crypto.decrypt(row["comm_log"]) if row["comm_log"] else "[]"
            entries = json.loads(existing_json)
            entries.insert(0, vars(entry))   # newest first
            new_enc = self._crypto.encrypt(json.dumps(entries, ensure_ascii=False))
            self._db.execute(
                "UPDATE stability SET comm_log=? WHERE stability_id=?",
                (new_enc, stability_id),
            )
            return True
        except Exception as e:
            print(f"[StabilityManager] comm_log error: {e}")
            return False

    def update_assessment(self, s: Stability) -> bool:
        try:
            enc = self._crypto.encrypt
            comm_json = json.dumps(
                [vars(e) for e in s.comm_log], ensure_ascii=False
            )
            self._db.execute(
                """UPDATE stability SET
                   assessment_date=?,
                   is_only_child=?, marital_status=?, children=?, family_jobs=?,
                   address=?, commute_distance=?, housing=?,
                   job_match=?, promotion_expectation=?, growth_needs=?,
                   transfer_willingness=?, salary_level_expectation=?,
                   workload=?, daily_state=?, superior_cooperation=?,
                   team_integration=?, work_satisfaction=?,
                   urgent_demand_type=?, urgent_demand_detail=?,
                   family_harmony=?, major_family_events=?, life_pressure=?,
                   emotional_stability=?, personality_type=?, hobbies=?,
                   social_circle=?, value_alignment=?,
                   family_score=?, career_score=?, work_score=?, overall_score=?,
                   risk_level=?, risk_tags=?, comm_log=?, assessed_by=?
                WHERE stability_id=?""",
                (
                    s.assessment_date,
                    s.is_only_child, s.marital_status, s.children, s.family_jobs,
                    s.address, s.commute_distance, s.housing,
                    s.job_match, s.promotion_expectation, s.growth_needs,
                    s.transfer_willingness, s.salary_level_expectation,
                    s.workload, s.daily_state, s.superior_cooperation,
                    s.team_integration, s.work_satisfaction,
                    s.urgent_demand_type, s.urgent_demand_detail,
                    s.family_harmony, s.major_family_events, s.life_pressure,
                    s.emotional_stability, s.personality_type, s.hobbies,
                    s.social_circle, s.value_alignment,
                    enc(str(s.family_score)), enc(str(s.career_score)),
                    enc(str(s.work_score)), enc(str(s.overall_score)),
                    s.risk_level, s.risk_tags,
                    enc(json.dumps([vars(e) for e in s.comm_log], ensure_ascii=False)),
                    s.assessed_by,
                    s.stability_id,
                ),
            )
            return True
        except Exception as e:
            print(f"[StabilityManager] update error: {e}")
            return False
