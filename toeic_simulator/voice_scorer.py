"""
Voice Scorer — iFlytek ISE (Intelligent Speaking Evaluation) API client.

Credentials are read in priority order:
  1. Environment variables: XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET
  2. Local config file:     xunfei_config.json  (saved via save_config())

All scoring is fully manual (user clicks button); never auto-starts or runs
in the background without explicit user action.

Timeout: 5 seconds. Caller receives error="__TIMEOUT__" to show retry dialog.

Requires: websocket-client  (pip install websocket-client)
"""
import base64
import hashlib
import hmac
import json
import os
import threading
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time


class _Timeout(Exception):
    """Raised internally when the 5-second scoring timeout elapses."""


class VoiceScorer:
    """
    Asynchronously scores a WAV recording via the iFlytek ISE WebSocket API.

    Usage:
        scorer = VoiceScorer(base_dir)
        scorer.score_async(wav_path, reference_text, my_callback)

        def my_callback(result: dict | None, error: str | None):
            if error == "__TIMEOUT__":
                ask_retry()
            elif error:
                show_error(error)
            else:
                show_scores(result)  # keys: pronunciation, fluency, completeness, overall
    """

    _WSS_URL = "wss://ise-api.xfyun.cn/v2/open-ise"
    _HOST    = "ise-api.xfyun.cn"
    _PATH    = "/v2/open-ise"

    def __init__(self, base_dir: str = ""):
        self._base_dir   = base_dir
        self.app_id      = ""
        self.api_key     = ""
        self.api_secret  = ""
        self._load_config()

    # ── Public API ────────────────────────────────────────────────────────────

    def has_credentials(self) -> bool:
        """True when all three credentials are non-empty."""
        return bool(self.app_id and self.api_key and self.api_secret)

    def _config_path(self) -> str:
        return os.path.join(self._base_dir, "xunfei_config.json")

    def _load_config(self) -> None:
        """Load credentials: env vars take priority over config file."""
        self.app_id     = os.environ.get("XUNFEI_APP_ID",     "")
        self.api_key    = os.environ.get("XUNFEI_API_KEY",    "")
        self.api_secret = os.environ.get("XUNFEI_API_SECRET", "")
        if not (self.app_id and self.api_key and self.api_secret):
            try:
                with open(self._config_path(), encoding="utf-8") as f:
                    cfg = json.load(f)
                self.app_id     = self.app_id     or cfg.get("app_id",     "")
                self.api_key    = self.api_key    or cfg.get("api_key",    "")
                self.api_secret = self.api_secret or cfg.get("api_secret", "")
            except Exception:
                pass

    def save_config(self, app_id: str, api_key: str, api_secret: str) -> None:
        """Persist credentials to config file and update instance state."""
        self.app_id     = app_id.strip()
        self.api_key    = api_key.strip()
        self.api_secret = api_secret.strip()
        try:
            with open(self._config_path(), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "app_id":     self.app_id,
                        "api_key":    self.api_key,
                        "api_secret": self.api_secret,
                    },
                    f,
                    ensure_ascii=False,
                )
        except Exception as exc:
            print(f"[VoiceScorer] Config save error: {exc}")

    def score_async(self, wav_path: str, reference_text: str, callback) -> None:
        """
        Score a recording asynchronously.
        callback(result: dict | None, error: str | None)
        result keys: pronunciation, fluency, completeness, overall (0.0–100.0)
        Special error value: "__TIMEOUT__" → caller should offer retry.
        """
        def _run():
            if not self.has_credentials():
                callback(
                    None,
                    "未配置讯飞 API 凭证\n\n"
                    "请设置环境变量：\n"
                    "  XUNFEI_APP_ID\n"
                    "  XUNFEI_API_KEY\n"
                    "  XUNFEI_API_SECRET",
                )
                return
            if not wav_path or not os.path.isfile(wav_path):
                callback(None, "录音文件不存在，请先完成录音")
                return
            try:
                result = self._call_ise(wav_path, reference_text or "")
                callback(result, None)
            except _Timeout:
                callback(None, "__TIMEOUT__")
            except OSError as exc:
                callback(None, f"请检查网络连接，语音评分需联网使用\n({exc})")
            except Exception as exc:
                callback(None, f"评分失败：{exc}")

        threading.Thread(target=_run, daemon=True).start()

    # ── Private — Auth ────────────────────────────────────────────────────────

    def _build_url(self) -> str:
        now  = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        sig_origin = (
            f"host: {self._HOST}\n"
            f"date: {date}\n"
            f"GET {self._PATH} HTTP/1.1"
        )
        sig_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            sig_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(sig_sha).decode("utf-8")
        auth_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(auth_origin.encode("utf-8")).decode("utf-8")
        return self._WSS_URL + "?" + urlencode({
            "authorization": authorization,
            "date":          date,
            "host":          self._HOST,
        })

    # ── Private — WebSocket call ──────────────────────────────────────────────

    def _call_ise(self, wav_path: str, ref_text: str) -> dict:
        try:
            import websocket  # type: ignore  (websocket-client)
        except ImportError:
            raise RuntimeError(
                "websocket-client 未安装。\n请运行: pip install websocket-client"
            )

        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        url      = self._build_url()
        result   = {}
        done_evt = threading.Event()
        errors   = []

        def on_open(ws):
            req = {
                "common":   {"app_id": self.app_id},
                "business": {
                    "category": "read_sentence",
                    "rstcd":    "utf8",
                    "group":    "pupil",
                    "sub":      "ise",
                    "ent":      "en_vip",
                    "text":     "\uFEFF" + ref_text,
                },
                "data": {
                    "status":   2,
                    "encoding": "raw",
                    "audio":    audio_b64,
                },
            }
            ws.send(json.dumps(req))

        def on_message(ws, message):
            msg = json.loads(message)
            if msg.get("code") != 0:
                errors.append(
                    f"ISE error {msg.get('code')}: {msg.get('message', '')}"
                )
            else:
                result.update(self._parse(msg))
            ws.close()

        def on_error(ws, error):
            errors.append(str(error))
            done_evt.set()

        def on_close(ws, *_args):
            done_evt.set()

        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        t = threading.Thread(
            target=ws.run_forever, daemon=True
        )
        t.start()
        done_evt.wait(timeout=15)

        if not done_evt.is_set():
            try:
                ws.close()
            except Exception:
                pass
            raise _Timeout()

        if errors:
            raise OSError(errors[0])

        return result or {
            "pronunciation": 0.0,
            "fluency":       0.0,
            "completeness":  0.0,
            "overall":       0.0,
        }

    # ── Private — XML parse ───────────────────────────────────────────────────

    def _parse(self, msg: dict) -> dict:
        try:
            data_b64 = msg.get("data", {}).get("data", "")
            xml_str  = base64.b64decode(data_b64).decode("utf-8")
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_str)

            total  = float(root.get("total_score") or 0)
            pron   = 0.0
            flu    = 0.0
            compl  = 0.0

            for node in root.iter():
                tag = node.tag.lower()
                try:
                    sc = float(node.get("score") or node.get("total_score") or 0)
                except (TypeError, ValueError):
                    sc = 0.0
                if sc and "pron" in tag and not pron:
                    pron = sc
                elif sc and "flu" in tag and not flu:
                    flu = sc
                elif sc and "int" in tag and not compl:
                    compl = sc

            return {
                "pronunciation": round(pron,  1),
                "fluency":       round(flu,   1),
                "completeness":  round(compl, 1),
                "overall":       round(total, 1),
            }
        except Exception as exc:
            print(f"[VoiceScorer] Parse error: {exc}")
            return {
                "pronunciation": 0.0,
                "fluency":       0.0,
                "completeness":  0.0,
                "overall":       0.0,
            }
