"""
AuthManager — user login and password management using bcrypt.
Seeds default admin/admin123 on first run.
"""
import bcrypt
from db.database import DatabaseManager


class AuthManager:
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin123"

    def __init__(self, db: DatabaseManager):
        self._db = db
        self._current_user: str = ""
        self._ensure_default_admin()

    def _ensure_default_admin(self) -> None:
        row = self._db.fetchone("SELECT id FROM users WHERE username=?",
                                (self.DEFAULT_USERNAME,))
        if not row:
            pw_hash = bcrypt.hashpw(
                self.DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            self._db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (self.DEFAULT_USERNAME, pw_hash, "admin"),
            )

    def login(self, username: str, password: str) -> bool:
        row = self._db.fetchone(
            "SELECT password_hash FROM users WHERE username=?", (username,)
        )
        if not row:
            return False
        ok = bcrypt.checkpw(password.encode("utf-8"),
                            row["password_hash"].encode("utf-8"))
        if ok:
            self._current_user = username
        return ok

    def change_password(self, username: str, old_pw: str, new_pw: str) -> bool:
        if not self.login(username, old_pw):
            return False
        pw_hash = bcrypt.hashpw(
            new_pw.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        self._db.execute(
            "UPDATE users SET password_hash=? WHERE username=?",
            (pw_hash, username),
        )
        return True

    @property
    def current_user(self) -> str:
        return self._current_user
