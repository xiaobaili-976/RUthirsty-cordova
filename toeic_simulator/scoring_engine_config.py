"""
Scoring engine selection config — persists the active voice scoring engine choice.

Supported engines (display order matches settings menu):
  "local"   — 本地开源 (Whisper + SpeechScore), no API key required
  "xunfei"  — 讯飞 ISE  (existing implementation)
  "tencent" — 腾讯云智聆
  "chivox"  — 驰声 Chivox

Config is stored in  <base_dir>/scoring_engine.json  as {"engine": "<key>"}.
"""
import json
import os

# Ordered list of (key, display_label) pairs shown in the settings menu.
ENGINES: list[tuple[str, str]] = [
    ("local",   "本地开源 (Whisper+SpeechScore)"),
    ("xunfei",  "讯飞 ISE"),
    ("tencent", "腾讯云智聆"),
    ("chivox",  "驰声 Chivox"),
]

_VALID_KEYS: set[str] = {k for k, _ in ENGINES}
_DEFAULT:    str       = "xunfei"
_FILE:       str       = "scoring_engine.json"


class ScoringEngineConfig:
    """Lightweight config object — load once, save on change."""

    def __init__(self, base_dir: str):
        self._path  = os.path.join(base_dir, _FILE)
        self.engine = _DEFAULT
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, engine: str) -> None:
        """Persist a new engine selection and update the in-memory value."""
        if engine not in _VALID_KEYS:
            return
        self.engine = engine
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump({"engine": self.engine}, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[ScoringEngineConfig] Save error: {exc}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            key = data.get("engine", _DEFAULT)
            if key in _VALID_KEYS:
                self.engine = key
        except Exception:
            pass  # file missing or corrupt → use default
