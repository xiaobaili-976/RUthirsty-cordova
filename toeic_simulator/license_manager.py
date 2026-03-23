"""
license_manager.py — Local license / activation for TOEIC Simulator Basic Edition.

Machine code  : MD5(CPU-ProcessorId + Disk-SerialNumber)[:12].upper()
Activation key: "BASE-" + machine_code[-6:] + any 3 digits   (14 chars total)
License store : toeic_license.json  (XOR-obfuscated base64 payload)
Dev bypass    : place dev_mode.txt next to the EXE
              OR  Ctrl+Shift+T → enter "TOEIC_DEV_2024"

Developer workflow (to issue a key for a customer):
  1. Customer shows their machine code from the purchase dialog.
  2. Developer computes: "BASE-" + machine_code[-6:] + "NNN"  (NNN = any 3 digits)
  3. Developer sends the 14-char code to the customer.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys

# Simple obfuscation key (not true encryption — client-side only)
_XOR_KEY = b"TOEIC_SIM_BASE_LICENSE_KEY_2024!"


class LicenseManager:
    LICENSE_FILE = "toeic_license.json"
    DEV_FILE     = "dev_mode.txt"
    DEV_PASSWORD = "TOEIC_DEV_2024"
    EDITION      = "BASE"
    PRICE        = "¥19.9"

    def __init__(self, base_dir: str):
        self._base_dir    = base_dir
        self._activated   = False
        self._dev_mode    = False
        self._machine_code = self._build_machine_code()
        self._load()

    # ── public API ────────────────────────────────────────────────────────────
    @property
    def machine_code(self) -> str:
        """12-char uppercase hex string unique to this machine."""
        return self._machine_code

    @property
    def is_activated(self) -> bool:
        return self._activated or self._dev_mode

    def activate(self, code: str) -> bool:
        """Validate and persist an activation code. Returns True on success."""
        code = code.strip().upper()
        if not self._valid_code(code):
            return False
        self._save(code)
        self._activated = True
        return True

    def enable_dev_mode(self, password: str) -> bool:
        """Unlock via developer password. Returns True if password correct."""
        if password == self.DEV_PASSWORD:
            self._dev_mode = True
            return True
        return False

    # ── machine code ─────────────────────────────────────────────────────────
    def _build_machine_code(self) -> str:
        raw = self._win_hw_string() if sys.platform == "win32" else ""
        if not raw:
            import uuid
            raw = str(uuid.getnode())
        return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest().upper()[:12]

    @staticmethod
    def _win_hw_string() -> str:
        """Collect CPU ProcessorId + first Disk SerialNumber via wmic."""
        parts = []
        try:
            for cmd, key in [
                ("wmic cpu get ProcessorId /value",          "ProcessorId"),
                ("wmic diskdrive get SerialNumber /value",   "SerialNumber"),
            ]:
                out = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5
                ).decode(errors="ignore")
                for line in out.splitlines():
                    if f"{key}=" in line:
                        val = line.split("=", 1)[-1].strip()
                        if val:
                            parts.append(val)
                            break
        except Exception:
            pass
        return "".join(parts)

    # ── validation ────────────────────────────────────────────────────────────
    def _valid_code(self, code: str) -> bool:
        """
        Valid format: BASE-{machine_code[-6:]}{NNN}
        Total length: 5 + 6 + 3 = 14 chars.
        """
        if not code.startswith("BASE-"):
            return False
        body = code[5:]           # 9 chars expected
        if len(body) != 9:
            return False
        if body[:6] != self._machine_code[-6:]:
            return False
        return body[6:].isdigit()

    # ── persistence ───────────────────────────────────────────────────────────
    def _load(self):
        # 1. Dev-mode file bypass
        if os.path.isfile(os.path.join(self._base_dir, self.DEV_FILE)):
            self._dev_mode = True
            return

        # 2. License file
        path = os.path.join(self._base_dir, self.LICENSE_FILE)
        if not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                outer = json.load(f)
            payload = self._decode(outer.get("_", ""))
            data    = json.loads(payload)
            if (data.get("machine_code") == self._machine_code
                    and self._valid_code(data.get("code", ""))):
                self._activated = True
        except Exception:
            pass   # corrupted file → stay locked

    def _save(self, code: str):
        payload = json.dumps({
            "machine_code": self._machine_code,
            "code":         code,
            "edition":      self.EDITION,
        }, ensure_ascii=False)
        path = os.path.join(self._base_dir, self.LICENSE_FILE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"_": self._encode(payload)}, f)

    # ── XOR + base64 obfuscation ──────────────────────────────────────────────
    @staticmethod
    def _encode(text: str) -> str:
        data  = text.encode("utf-8")
        key   = _XOR_KEY
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return base64.b64encode(xored).decode()

    @staticmethod
    def _decode(encoded: str) -> str:
        xored = base64.b64decode(encoded.encode())
        key   = _XOR_KEY
        data  = bytes(b ^ key[i % len(key)] for i, b in enumerate(xored))
        return data.decode("utf-8")
