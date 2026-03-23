"""
score_analyzer.py
─────────────────
Lightweight speaking-score analyzer for TOEIC practice.

Scoring model (heuristic, not official TOEIC):
  • Preparation usage  30% — did the user use prep time fully?
  • Response timing    40% — was response time well used (not too short/long)?
  • Fluency (WPM)      30% — words-per-minute from optional vosk transcription

All sub-scores are 0–100.  Band mapping of the final score:
  90-100 → Advanced    参考分 180–200
  75-89  → High-Inter  参考分 141–180
  55-74  → Inter       参考分 94–140
  30-54  → Low-Inter   参考分 54–93
  0-29   → Basic       参考分 0–53
"""
import time
from typing import Optional

_TARGET_WPM_LOW  = 90
_TARGET_WPM_HIGH = 150


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


class ResponseSession:
    """Tracks timestamps for a single question's prep + response phases."""

    def __init__(self, prep_seconds: int, resp_seconds: int, part: str):
        self.part          = part
        self.prep_duration = prep_seconds
        self.resp_duration = resp_seconds
        self._prep_start: Optional[float] = None
        self._resp_start: Optional[float] = None
        self._resp_end:   Optional[float] = None
        self.transcript: str = ""

    def on_prep_start(self) -> None:
        self._prep_start = time.monotonic()

    def on_resp_start(self) -> None:
        self._resp_start = time.monotonic()

    def on_resp_end(self) -> None:
        self._resp_end = time.monotonic()

    def set_transcript(self, text: str) -> None:
        self.transcript = text.strip()

    def compute_score(self) -> dict:
        """Return score dict with breakdown and coaching suggestions."""
        # ── 1. Preparation usage score ───────────────────────────────────────
        prep_score = 50.0
        if self._prep_start and self._resp_start:
            used_ratio = (self._resp_start - self._prep_start) / max(self.prep_duration, 1)
            prep_score = _clamp(used_ratio * 100)

        # ── 2. Response timing score ─────────────────────────────────────────
        resp_score = 50.0
        if self._resp_start and self._resp_end:
            actual     = self._resp_end - self._resp_start
            ratio      = actual / max(self.resp_duration, 1)
            if ratio >= 0.7:
                # Full or slightly over — ideal; small penalty for far over
                resp_score = _clamp(100.0 - max(0.0, ratio - 1.0) * 50.0)
            else:
                # Too short — proportional penalty
                resp_score = _clamp(ratio / 0.7 * 80.0)

        # ── 3. Fluency score (WPM from transcript) ───────────────────────────
        fluency_score = 50.0
        wpm = 0
        pacing_tip = ""
        if self.transcript and self._resp_start and self._resp_end:
            dur_min   = (self._resp_end - self._resp_start) / 60.0
            word_cnt  = len(self.transcript.split())
            wpm       = int(word_cnt / max(dur_min, 0.001))
            if wpm < _TARGET_WPM_LOW:
                fluency_score = _clamp(wpm / _TARGET_WPM_LOW * 70.0)
                pacing_tip = f"语速偏慢（{wpm} WPM），建议加快节奏，减少无效停顿。"
            elif wpm > _TARGET_WPM_HIGH:
                fluency_score = _clamp(100.0 - (wpm - _TARGET_WPM_HIGH) * 0.5)
                pacing_tip = f"语速偏快（{wpm} WPM），建议适当放慢，注意断句清晰。"
            else:
                fluency_score = 100.0
                pacing_tip = f"语速适中（{wpm} WPM），节奏良好！"

        # ── Final weighted score ─────────────────────────────────────────────
        final = _clamp(prep_score * 0.30 + resp_score * 0.40 + fluency_score * 0.30)
        band, ref_range = _score_to_band(final)
        suggestions = _build_suggestions(prep_score, resp_score,
                                          fluency_score, pacing_tip, self.part)
        return {
            "final":         round(final),
            "prep_score":    round(prep_score),
            "resp_score":    round(resp_score),
            "fluency_score": round(fluency_score),
            "wpm":           wpm,
            "band":          band,
            "ref_range":     ref_range,
            "suggestions":   suggestions,
        }


def _score_to_band(score: float) -> tuple:
    if score >= 90: return "Advanced",   "参考分 180–200"
    if score >= 75: return "High-Inter", "参考分 141–180"
    if score >= 55: return "Inter",      "参考分 94–140"
    if score >= 30: return "Low-Inter",  "参考分 54–93"
    return "Basic", "参考分 0–53"


def _build_suggestions(prep: float, resp: float, fluency: float,
                        pacing_tip: str, part: str) -> list:
    tips = []
    if prep < 60:
        tips.append("充分利用准备时间：列出关键词、句子框架，不要提前开口。")
    if resp < 60:
        tips.append("尽量填满作答时间；可用举例或细节延伸，避免沉默。")
    if fluency < 60 and not pacing_tip:
        tips.append("注意语速均匀，减少'um/uh'等填充词，提升流利度。")
    if pacing_tip:
        tips.append(pacing_tip)
    part_tips = {
        "Part1": "Part 1：注意正确发音与连读，强调关键名词/动词，逗号处自然停顿。",
        "Part2": "Part 2：按前景→背景→动作→整体感受的顺序描述图片，使用 appear to be。",
        "Part3": "Part 3：先直接回答，再给出理由；Q7 使用 First/Furthermore/Therefore 结构。",
        "Part4": "Part 4：直接从信息中引用事实，Q8/Q9 无需观点，Q10 可适当推理。",
        "Part5": "Part 5：开门见山亮出立场，用2个具体例子支撑，最后一句重述观点。",
    }
    if part in part_tips:
        tips.append(part_tips[part])
    return tips[:4]


class ScoreAnalyzer:
    """
    Manages one ResponseSession per question key.
    key convention: "p1_q1", "p3_q5", etc. (matches recorder hint)
    """

    def __init__(self):
        self._sessions: dict = {}
        self._current_key: Optional[str] = None
        self._current_session: Optional[ResponseSession] = None

    def begin_question(self, key: str, part: str,
                       prep_secs: int, resp_secs: int) -> None:
        """Call when the question screen is first shown."""
        sess = ResponseSession(prep_secs, resp_secs, part)
        self._sessions[key] = sess
        self._current_key     = key
        self._current_session = sess

    def on_prep_start(self) -> None:
        if self._current_session:
            self._current_session.on_prep_start()

    def on_resp_start(self, key: Optional[str] = None) -> None:
        sess = (self._sessions.get(key) if key
                else self._current_session)
        if sess:
            sess.on_resp_start()

    def on_resp_end(self, key: Optional[str] = None) -> None:
        sess = (self._sessions.get(key) if key
                else self._current_session)
        if sess:
            sess.on_resp_end()

    def add_transcript(self, key: str, text: str) -> None:
        if key in self._sessions:
            self._sessions[key].set_transcript(text)

    def get_score(self, key: str) -> Optional[dict]:
        sess = self._sessions.get(key)
        return sess.compute_score() if sess else None

    def current_key(self) -> Optional[str]:
        return self._current_key
