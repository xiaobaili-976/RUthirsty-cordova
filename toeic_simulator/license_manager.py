"""
license_manager.py
──────────────────
Trial / activation system for TOEIC Speaking Test Simulator (Professional Edition).

Trial period  : 3 days (72 hours) from first launch.
                Persists across restarts via encrypted toeic_trial.dat.
Activation    : Code format  BASE-XXXXXX000
                              └──6 hex from machine_code (last 6)──┘└─3 digits─┘
Machine code  : MD5(CPU_serial + disk_serial), upper-case hex, 32 chars.
Dev mode      : Ctrl+Shift+T → password "TOEIC_DEV_2024"
                OR  dev_mode.txt present in BASE_DIR
License file  : toeic_license.dat (XOR + base64 obfuscation)
"""
import base64
import hashlib
import os
import subprocess
import time
from typing import Optional

# Simple obfuscation key (symmetric XOR — not crypto-grade by design)
_XOR_KEY = b"T0EIC_S1MULATOR_K3Y_2024_SECURE_"


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encode(text: str) -> str:
    return base64.b64encode(_xor(text.encode("utf-8"), _XOR_KEY)).decode("ascii")


def _decode(encoded: str) -> str:
    try:
        return _xor(base64.b64decode(encoded.encode("ascii")), _XOR_KEY).decode("utf-8")
    except Exception:
        return ""


def _get_machine_code() -> str:
    """Return 32-char upper-case MD5 hex of CPU+disk serial (Windows only)."""
    cpu_serial = ""
    disk_serial = ""
    try:
        r = subprocess.run(
            ["wmic", "cpu", "get", "ProcessorId"],
            capture_output=True, text=True, timeout=5,
        )
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        if len(lines) >= 2:
            cpu_serial = lines[1]
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["wmic", "diskdrive", "get", "SerialNumber"],
            capture_output=True, text=True, timeout=5,
        )
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        if len(lines) >= 2:
            disk_serial = lines[1]
    except Exception:
        pass
    raw = (cpu_serial + disk_serial) or "FALLBACK_MACHINE_ID"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


class LicenseManager:
    """
    Manages trial period and permanent activation state.

    Usage:
        lm = LicenseManager(base_dir)
        if lm.is_unlocked():
            ...  # proceed
        remaining = lm.trial_remaining_seconds()  # 0 = expired
        ok, msg = lm.activate("BASE-XXXXXX000")
        ok = lm.unlock_dev("TOEIC_DEV_2024")
    """

    TRIAL_DAYS = 3
    DEV_PASSWORD = "TOEIC_DEV_2024"

    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        self._machine_code = _get_machine_code()
        self._unlocked = False
        self._dev_mode = False

        # ── 1. dev_mode.txt bypass ────────────────────────────────────────────
        if os.path.isfile(os.path.join(base_dir, "dev_mode.txt")):
            self._dev_mode = True
            self._unlocked = True
            return

        # ── 2. Check saved license ────────────────────────────────────────────
        if self._check_license_file():
            self._unlocked = True
            return

        # ── 3. Start / resume trial ───────────────────────────────────────────
        self._ensure_trial_started()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def machine_code(self) -> str:
        """32-char machine fingerprint shown to users for activation."""
        return self._machine_code

    def is_unlocked(self) -> bool:
        """True when dev mode, valid license, OR trial still active."""
        if self._unlocked:
            return True
        return self.trial_remaining_seconds() > 0

    def is_dev_mode(self) -> bool:
        return self._dev_mode

    def trial_remaining_seconds(self) -> int:
        """Seconds left in trial. Returns 0 when expired or never started."""
        start = self._read_trial_start()
        if start <= 0:
            return 0
        elapsed = time.time() - start
        remaining = int(self.TRIAL_DAYS * 86400 - elapsed)
        return max(remaining, 0)

    def activate(self, code: str) -> tuple:
        """
        Validate and permanently save an activation code.
        Returns (success: bool, message: str).
        """
        code = code.strip().upper()
        if not self._validate_code(code):
            return (False,
                    "激活码无效。\n\n"
                    "请检查：\n"
                    "  • 格式是否为 BASE-XXXXXX000\n"
                    "  • 激活码是否与本机机器码匹配")
        self._save_license(code)
        self._unlocked = True
        return (True, "激活成功！感谢您购买终身专业版。\n软件已永久解锁。")

    def unlock_dev(self, password: str) -> bool:
        """Unlock via developer password. Returns True on success."""
        if password == self.DEV_PASSWORD:
            self._dev_mode = True
            self._unlocked = True
            return True
        return False

    # ── Private ───────────────────────────────────────────────────────────────

    def _validate_code(self, code: str) -> bool:
        """
        Pattern: BASE-[last 6 of machine_code][3 digits]
        Example: machine "A1B2C3D4E5F6..." → code "BASE-E5F6AB123"
        """
        if not code.startswith("BASE-"):
            return False
        suffix = code[5:]
        if len(suffix) != 9:
            return False
        if suffix[:6].upper() != self._machine_code[-6:].upper():
            return False
        if not suffix[6:].isdigit():
            return False
        return True

    def _license_path(self) -> str:
        return os.path.join(self._base_dir, "toeic_license.dat")

    def _trial_path(self) -> str:
        return os.path.join(self._base_dir, "toeic_trial.dat")

    def _save_license(self, code: str) -> None:
        try:
            payload = (f"code={code}|machine={self._machine_code}"
                       f"|ts={int(time.time())}")
            with open(self._license_path(), "w", encoding="ascii") as f:
                f.write(_encode(payload))
        except Exception as exc:
            print(f"[License] Failed to save: {exc}")

    def _check_license_file(self) -> bool:
        path = self._license_path()
        if not os.path.isfile(path):
            return False
        try:
            with open(path, encoding="ascii") as f:
                payload = _decode(f.read().strip())
            parts = dict(
                kv.split("=", 1) for kv in payload.split("|") if "=" in kv
            )
            return self._validate_code(parts.get("code", ""))
        except Exception:
            return False

    def _ensure_trial_started(self) -> None:
        """Write trial start timestamp only if not already written."""
        if self._read_trial_start() > 0:
            return
        try:
            encoded = _encode(str(int(time.time())))
            with open(self._trial_path(), "w", encoding="ascii") as f:
                f.write(encoded)
        except Exception as exc:
            print(f"[License] Failed to write trial start: {exc}")

    def _read_trial_start(self) -> float:
        path = self._trial_path()
        if not os.path.isfile(path):
            return -1.0
        try:
            with open(path, encoding="ascii") as f:
                return float(_decode(f.read().strip()))
        except Exception:
            return -1.0
