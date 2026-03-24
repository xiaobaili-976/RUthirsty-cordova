"""
Placeholder scorer classes for Tencent Cloud 智聆, Chivox 驰声, and local
Whisper + SpeechScore engines.

Each class exposes the same public interface as VoiceScorer so that
window.py can treat all scorers uniformly:

    has_credentials() -> bool
    save_config(app_id, api_key, api_secret) -> None
    score_async(wav_path, answer_text, callback) -> None
    _load_config() -> None          # no-op acceptable for local engine
    app_id / api_key / api_secret   # string attributes (empty for local)

score_async fires callback(result: dict | None, error: str | None) from a
daemon thread — callers use QTimer.singleShot to marshal back to the UI thread.
"""
import json
import os
import threading


# ── Shared base for API-key-based engines ────────────────────────────────────

class _ApiBaseScorer:
    """
    Common base for cloud API scorers that need (App ID, API Key, API Secret).
    Subclasses override _config_file and optionally _score_thread.
    """

    _config_file: str = ""   # set by subclass

    def __init__(self, base_dir: str):
        self._base_dir  = base_dir
        self.app_id     = ""
        self.api_key    = ""
        self.api_secret = ""
        self._load_config()

    # ── Public API ─────────────────────────────────────────────────────────

    def has_credentials(self) -> bool:
        return bool(self.app_id and self.api_key and self.api_secret)

    def save_config(self, app_id: str, api_key: str, api_secret: str) -> None:
        self.app_id     = app_id.strip()
        self.api_key    = api_key.strip()
        self.api_secret = api_secret.strip()
        try:
            path = os.path.join(self._base_dir, self._config_file)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "app_id":     self.app_id,
                        "api_key":    self.api_key,
                        "api_secret": self.api_secret,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:
            print(f"[{type(self).__name__}] Config save error: {exc}")

    def _load_config(self) -> None:
        try:
            path = os.path.join(self._base_dir, self._config_file)
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            self.app_id     = cfg.get("app_id",     "")
            self.api_key    = cfg.get("api_key",    "")
            self.api_secret = cfg.get("api_secret", "")
        except Exception:
            pass

    def score_async(self, wav_path: str, answer_text: str, callback) -> None:
        threading.Thread(
            target=self._score_thread,
            args=(wav_path, answer_text, callback),
            daemon=True,
        ).start()

    def _score_thread(self, wav_path: str, answer_text: str, callback) -> None:
        """
        Override in a real implementation.
        This stub returns an informative "not yet integrated" error.
        """
        callback(None, "该评分引擎尚未完整接入，敬请期待后续版本。")


# ── Concrete cloud scorer stubs ───────────────────────────────────────────────

class TencentScorer(_ApiBaseScorer):
    """腾讯云智聆口语评测 (stub — API integration pending)."""
    _config_file = "tencent_config.json"


class ChivoxScorer(_ApiBaseScorer):
    """驰声 Chivox 语音评测 (stub — API integration pending)."""
    _config_file = "chivox_config.json"


# ── Local open-source scorer ──────────────────────────────────────────────────

class LocalScorer:
    """
    Local open-source scoring engine using Whisper + SpeechScore.
    No credentials required; evaluation runs entirely offline.

    Full offline implementation is pending; this stub returns a clear
    informational message so the user understands the state.
    """

    app_id     = ""
    api_key    = ""
    api_secret = ""

    def __init__(self, base_dir: str = ""):
        self._base_dir = base_dir

    def has_credentials(self) -> bool:
        """Local engine requires no credentials."""
        return True

    def save_config(self, *_args) -> None:
        """No-op — local engine has no remote credentials."""

    def _load_config(self) -> None:
        """No-op — nothing to load for local engine."""

    def score_async(self, wav_path: str, answer_text: str, callback) -> None:
        threading.Thread(
            target=self._score_thread,
            args=(wav_path, answer_text, callback),
            daemon=True,
        ).start()

    def _score_thread(self, wav_path: str, answer_text: str, callback) -> None:
        # Stub: offline Whisper + SpeechScore integration pending.
        callback(None, "本地开源评分引擎（Whisper+SpeechScore）尚未集成，敬请期待后续版本。")
