"""
Marks Manager — persists per-question marks (weak / high-frequency) locally.

Storage: marks.json in base_dir.
Question ID scheme: "{set_id}:{part}:{index}"
  Examples: "1:p1:0"  "2:p3:2"  "1:p5:0"
"""
import json
import os


class MarksManager:
    """
    Lightweight local mark store for TOEIC review mode.

    Marks are independent of the question bank files — they live in a separate
    marks.json that is never modified by the question loader.
    """

    def __init__(self, base_dir: str):
        self._path = os.path.join(base_dir, "marks.json")
        self._data: dict = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if os.path.isfile(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as exc:
                print(f"[Marks] Load error: {exc}")
                self._data = {}

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[Marks] Save error: {exc}")

    def _entry(self, qid: str) -> dict:
        return self._data.setdefault(qid, {"weak": False, "high_freq": False})

    # ── Public API ────────────────────────────────────────────────────────────

    def toggle_weak(self, qid: str) -> bool:
        """Toggle weak mark. Returns new state (True = marked)."""
        e = self._entry(qid)
        e["weak"] = not e["weak"]
        self._save()
        return e["weak"]

    def toggle_high_freq(self, qid: str) -> bool:
        """Toggle high-freq mark. Returns new state (True = marked)."""
        e = self._entry(qid)
        e["high_freq"] = not e["high_freq"]
        self._save()
        return e["high_freq"]

    def is_weak(self, qid: str) -> bool:
        return self._data.get(qid, {}).get("weak", False)

    def is_high_freq(self, qid: str) -> bool:
        return self._data.get(qid, {}).get("high_freq", False)

    def get_weak_ids(self) -> set:
        return {k for k, v in self._data.items() if v.get("weak")}

    def get_high_freq_ids(self) -> set:
        return {k for k, v in self._data.items() if v.get("high_freq")}
