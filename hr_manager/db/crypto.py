"""
FieldCrypto — AES field-level encryption via cryptography.Fernet.

Key is auto-generated on first run and stored in data/hr_crypto.key.
IMPORTANT: Back up this key file together with hr_manager.db.
Losing the key = losing access to all encrypted fields.
"""
import os
from cryptography.fernet import Fernet


class FieldCrypto:
    def __init__(self, key_path: str):
        self._key_path = key_path
        self._fernet = Fernet(self._load_or_generate_key())

    def _load_or_generate_key(self) -> bytes:
        if os.path.isfile(self._key_path):
            with open(self._key_path, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(self._key_path), exist_ok=True)
        with open(self._key_path, "wb") as f:
            f.write(key)
        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string → base64 ciphertext string."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string → original plaintext string."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except Exception:
            return ""   # corrupted or wrong key — return empty rather than crash
