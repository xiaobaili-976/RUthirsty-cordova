"""BackupManager — database backup/restore and Excel import/export."""
import shutil
import os
from datetime import datetime


class BackupManager:
    def __init__(self, db_path: str, key_path: str, data_dir: str):
        self._db_path = db_path
        self._key_path = key_path
        self._data_dir = data_dir

    def backup_to_file(self, dest_dir: str) -> str:
        """Backup db + key to dest_dir. Returns backup folder path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(dest_dir, f"hr_backup_{ts}")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(self._db_path, os.path.join(backup_dir, "hr_manager.db"))
        if os.path.isfile(self._key_path):
            shutil.copy2(self._key_path, os.path.join(backup_dir, "hr_crypto.key"))
        return backup_dir

    def restore_from_dir(self, src_dir: str) -> bool:
        """Restore db + key from a backup directory."""
        try:
            db_src = os.path.join(src_dir, "hr_manager.db")
            key_src = os.path.join(src_dir, "hr_crypto.key")
            if not os.path.isfile(db_src):
                return False
            shutil.copy2(db_src, self._db_path)
            if os.path.isfile(key_src):
                shutil.copy2(key_src, self._key_path)
            return True
        except Exception as e:
            print(f"[BackupManager] restore error: {e}")
            return False

    def export_to_excel(self, dest_path: str, managers: dict) -> bool:
        """Export all data to a multi-sheet Excel file."""
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            wb.remove(wb.active)  # remove default sheet

            emp_mgr = managers.get("employee")
            if emp_mgr:
                ws = wb.create_sheet("员工基础信息")
                headers = ["工号", "姓名", "性别", "出生日期", "年龄", "电话", "邮箱",
                           "部门", "小组", "职位", "职级", "职等", "学历", "状态", "备注"]
                ws.append(headers)
                depts = {r["dept_id"]: r["dept_name"]
                         for r in emp_mgr.list_departments()}
                groups = {r["group_id"]: r["group_name"]
                          for r in emp_mgr.list_groups()}
                for e in emp_mgr.list_employees():
                    ws.append([
                        e.employee_id, e.name, e.gender, e.dob, e.age,
                        e.phone, e.email,
                        depts.get(e.dept_id, ""),
                        groups.get(e.group_id, ""),
                        e.job_title, e.job_level, e.job_grade,
                        e.education_level, e.display_status, e.notes,
                    ])

            cont_mgr = managers.get("contract")
            if cont_mgr:
                ws2 = wb.create_sheet("合同信息")
                ws2.append(["工号", "姓名", "合同类型", "入职日期", "合同开始", "合同结束",
                             "续签日期", "续签倒计时(天)", "状态"])
                for c in cont_mgr.get_all_contracts():
                    ws2.append([
                        c.employee_id, c.employee_name, c.contract_type,
                        c.hire_date, c.start_date, c.end_date,
                        c.renewal_date, c.days_to_renewal, c.status,
                    ])

            wb.save(dest_path)
            return True
        except Exception as e:
            print(f"[BackupManager] export error: {e}")
            return False
