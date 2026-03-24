"""
Exam Engine — state machine driving the full TOEIC Speaking Test flow.

Step types
──────────
  screen      : update display; advance immediately (50 ms paint delay)
  tts         : speak text; advance when TTSManager emits finished
  timer       : count down N seconds; advance when counter hits 0
  set_answer  : silently update current answer text; advance immediately
  record_start: start microphone recording; advance immediately
  record_stop : stop recording; advance immediately
  end         : emit exam_finished

New public API (v2)
───────────────────
  sets          -> list[dict]          all loaded sets  [{id, name}, ...]
  load_set(id)                         select set before start_exam()
  start_exam()                         build steps & run
  skip()                               stop current timer, advance
"""
import csv
import json
import os
import sys
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from tts_manager import TTSManager

# ── Fixed instruction strings ────────────────────────────────────────────────
_PART1_INTRO = (
    "In this part of the test, you will read aloud the text on the screen. "
    "You will have 45 seconds to prepare. "
    "Then you will have 45 seconds to read the text aloud."
)
_PART2_INTRO = (
    "In this part of the test, you will describe the picture on your screen "
    "in as much detail as you can. "
    "You will have 45 seconds to prepare your response. "
    "Then you will have 30 seconds to speak about the picture."
)
_PART3_INTRO = (
    "In this part of the test, you will answer three questions. "
    "You will have three seconds to prepare after you hear each question. "
    "You will have 15 seconds to respond to Questions 5 and 6, "
    "and 30 seconds to respond to Question 7."
)
_PART4_INTRO = (
    "In this part of the test, you will answer three questions based on the "
    "information provided. You will have 45 seconds to read the information "
    "before the questions begin. You will have three seconds to prepare and "
    "15 seconds to respond to Questions 8 and 9. "
    "You will hear Question 10 two times. "
    "You will have three seconds to prepare and 30 seconds to respond to "
    "Question 10."
)
_PART5_INTRO = (
    "In this part of the test, you will give your opinion about a specific "
    "topic. Be sure to say as much as you can in the time allowed. "
    "You will have 45 seconds to prepare. Then you will have 60 seconds to speak."
)
_BEGIN_PREPARING = "Begin preparing now"
_BEGIN_READING   = "Begin reading now"
_BEGIN_SPEAKING  = "Begin speaking now"


# ── Step builder ─────────────────────────────────────────────────────────────
def _build_steps(set_data: dict, set_id: int, base_dir: str) -> list[dict]:
    """Return the full ordered list of exam steps for one question set."""

    def scr(title="", content="", secondary="", image="", answer=""):
        return {"type": "screen", "title": title, "content": content,
                "secondary": secondary, "image": image, "answer": answer}

    def t(text):
        return {"type": "tts", "text": text}

    def tm(duration, phase=""):
        return {"type": "timer", "duration": duration, "phase": phase}

    def sa(answer):
        return {"type": "set_answer", "answer": answer}

    def rs(hint):
        return {"type": "record_start",
                "subdir": f"records/set_{set_id}",
                "hint":   hint}

    rs_stop = {"type": "record_stop"}
    PREP, RESP = "Preparation Time", "Response Time"
    steps: list[dict] = []

    # ── PART 1 ───────────────────────────────────────────────────────────────
    steps += [scr("Questions 1 - 2: Read a text aloud", _PART1_INTRO), t(_PART1_INTRO)]
    for i, item in enumerate((set_data.get("part1") or [])[:2], 1):
        steps += [
            scr(f"Question {i} of 11", item.get("text", ""), answer=item.get("answer", "")),
            t(_BEGIN_PREPARING),
            tm(45, PREP),
            t(_BEGIN_READING),
            rs(f"p1_q{i}"),
            tm(45, RESP),
            rs_stop,
        ]

    # ── PART 2 ───────────────────────────────────────────────────────────────
    steps += [scr("Questions 3 - 4: Describe a picture", _PART2_INTRO), t(_PART2_INTRO)]
    for i, item in enumerate((set_data.get("part2") or [])[:2], 3):
        raw = item.get("image", "")
        img = raw if os.path.isabs(raw) else os.path.join(base_dir, raw)
        steps += [
            scr(f"Question {i} of 11", image=img, answer=item.get("answer", "")),
            t(_BEGIN_PREPARING),
            tm(45, PREP),
            t(_BEGIN_SPEAKING),
            rs(f"p2_q{i}"),
            tm(30, RESP),
            rs_stop,
        ]

    # ── PART 3 ───────────────────────────────────────────────────────────────
    steps += [scr("Questions 5 - 7: Respond to questions", _PART3_INTRO), t(_PART3_INTRO)]
    p3   = set_data.get("part3") or {}
    bg   = p3.get("background", "")
    p3qs = (p3.get("questions") or [])[:3]
    steps += [scr("Questions 5 - 7 of 11", bg), t(bg)]
    for idx, (q_num, dur) in enumerate([(5, 15), (6, 15), (7, 30)]):
        if idx < len(p3qs):
            qt = p3qs[idx].get("text", "")
            ans = p3qs[idx].get("answer", "")
            steps += [
                {"type": "screen", "title": f"Question {q_num} of 11",
                 "content": bg, "secondary": qt, "image": "", "answer": ans},
                t(qt), t(_BEGIN_PREPARING), tm(3, PREP), t(_BEGIN_SPEAKING),
                rs(f"p3_q{q_num}"), tm(dur, RESP), rs_stop,
            ]

    # ── PART 4 ───────────────────────────────────────────────────────────────
    steps += [
        scr("Questions 8 - 10: Respond to questions using information provided",
            _PART4_INTRO),
        t(_PART4_INTRO),
    ]
    p4   = set_data.get("part4") or {}
    info = p4.get("info", "")
    p4qs = (p4.get("questions") or [])[:3]
    steps += [scr("Questions 8 \u2013 10 of 11", info), t(_BEGIN_PREPARING), tm(45, PREP)]
    for idx, (q_num, dur) in enumerate([(8, 15), (9, 15), (10, 30)]):
        if idx < len(p4qs):
            qt  = p4qs[idx].get("text", "")
            ans = p4qs[idx].get("answer", "")
            plays = [t(qt), t(qt)] if q_num == 10 else [t(qt)]
            steps += [sa(ans)] + plays + [
                t(_BEGIN_PREPARING), tm(3, PREP), t(_BEGIN_SPEAKING),
                rs(f"p4_q{q_num}"), tm(dur, RESP), rs_stop,
            ]

    # ── PART 5 ───────────────────────────────────────────────────────────────
    steps += [scr("Question 11: Express an opinion", _PART5_INTRO), t(_PART5_INTRO)]
    p5   = set_data.get("part5") or {}
    q11  = p5.get("text", "")
    ans5 = p5.get("answer", "")
    steps += [
        scr("Question 11 of 11", q11, answer=ans5),
        t(q11), t(_BEGIN_PREPARING), tm(45, PREP), t(_BEGIN_SPEAKING),
        rs("p5_q11"), tm(60, RESP), rs_stop,
    ]

    steps.append({"type": "end"})
    return steps


def _build_part_steps(set_data: dict, set_id: int, base_dir: str, part_num: int) -> list[dict]:
    """Build exam steps for a single PART (1–5) only — same timing rules as full exam."""

    def scr(title="", content="", secondary="", image="", answer=""):
        return {"type": "screen", "title": title, "content": content,
                "secondary": secondary, "image": image, "answer": answer}

    def t(text):
        return {"type": "tts", "text": text}

    def tm(duration, phase=""):
        return {"type": "timer", "duration": duration, "phase": phase}

    def sa(answer):
        return {"type": "set_answer", "answer": answer}

    def rs(hint):
        return {"type": "record_start",
                "subdir": f"records/set_{set_id}",
                "hint":   hint}

    rs_stop = {"type": "record_stop"}
    PREP, RESP = "Preparation Time", "Response Time"
    steps: list[dict] = []

    if part_num == 1:
        steps += [scr("Part 1 — 朗读文章  Read a text aloud", _PART1_INTRO), t(_PART1_INTRO)]
        for i, item in enumerate((set_data.get("part1") or [])[:2], 1):
            steps += [
                scr(f"Question {i} of 2  (Part 1)", item.get("text", ""),
                    answer=item.get("answer", "")),
                t(_BEGIN_PREPARING), tm(45, PREP), t(_BEGIN_READING),
                rs(f"p1_q{i}"), tm(45, RESP), rs_stop,
            ]

    elif part_num == 2:
        steps += [scr("Part 2 — 描述图片  Describe a picture", _PART2_INTRO), t(_PART2_INTRO)]
        for i, item in enumerate((set_data.get("part2") or [])[:2], 3):
            raw = item.get("image", "")
            img = raw if os.path.isabs(raw) else os.path.join(base_dir, raw)
            steps += [
                scr(f"Question {i - 2} of 2  (Part 2)", image=img,
                    answer=item.get("answer", "")),
                t(_BEGIN_PREPARING), tm(45, PREP), t(_BEGIN_SPEAKING),
                rs(f"p2_q{i}"), tm(30, RESP), rs_stop,
            ]

    elif part_num == 3:
        steps += [scr("Part 3 — 回答问题  Respond to questions", _PART3_INTRO), t(_PART3_INTRO)]
        p3   = set_data.get("part3") or {}
        bg   = p3.get("background", "")
        p3qs = (p3.get("questions") or [])[:3]
        steps += [scr("Part 3  Questions 1–3", bg), t(bg)]
        for idx, (q_num, dur) in enumerate([(5, 15), (6, 15), (7, 30)]):
            if idx < len(p3qs):
                qt  = p3qs[idx].get("text", "")
                ans = p3qs[idx].get("answer", "")
                steps += [
                    {"type": "screen", "title": f"Question {idx + 1} of 3  (Part 3)",
                     "content": bg, "secondary": qt, "image": "", "answer": ans},
                    t(qt), t(_BEGIN_PREPARING), tm(3, PREP), t(_BEGIN_SPEAKING),
                    rs(f"p3_q{q_num}"), tm(dur, RESP), rs_stop,
                ]

    elif part_num == 4:
        steps += [
            scr("Part 4 — 信息问答  Respond using information provided", _PART4_INTRO),
            t(_PART4_INTRO),
        ]
        p4   = set_data.get("part4") or {}
        info = p4.get("info", "")
        p4qs = (p4.get("questions") or [])[:3]
        steps += [scr("Part 4  Questions 1–3", info), t(_BEGIN_PREPARING), tm(45, PREP)]
        for idx, (q_num, dur) in enumerate([(8, 15), (9, 15), (10, 30)]):
            if idx < len(p4qs):
                qt   = p4qs[idx].get("text", "")
                ans  = p4qs[idx].get("answer", "")
                plays = [t(qt), t(qt)] if q_num == 10 else [t(qt)]
                steps += [sa(ans)] + plays + [
                    t(_BEGIN_PREPARING), tm(3, PREP), t(_BEGIN_SPEAKING),
                    rs(f"p4_q{q_num}"), tm(dur, RESP), rs_stop,
                ]

    elif part_num == 5:
        steps += [scr("Part 5 — 发表意见  Express an opinion", _PART5_INTRO), t(_PART5_INTRO)]
        p5   = set_data.get("part5") or {}
        q11  = p5.get("text", "")
        ans5 = p5.get("answer", "")
        steps += [
            scr("Question 1 of 1  (Part 5)", q11, answer=ans5),
            t(q11), t(_BEGIN_PREPARING), tm(45, PREP), t(_BEGIN_SPEAKING),
            rs("p5_q11"), tm(60, RESP), rs_stop,
        ]

    steps.append({"type": "end"})
    return steps


# ── Default bank (fallback) ──────────────────────────────────────────────────
def _default_bank() -> dict:
    return {"sets": [{"id": 1, "name": "Default Set",
                      "part1": [
                          {"text": "Good morning, everyone. Welcome to the annual company meeting. "
                                   "Today we will discuss the financial results for the past year.",
                           "answer": "Read clearly at a steady pace, emphasizing key figures and dates."},
                          {"text": "Attention all passengers. The train service has been delayed "
                                   "by approximately twenty minutes. We apologize for any inconvenience.",
                           "answer": "Focus on clear pronunciation of numbers and apology phrases."},
                      ],
                      "part2": [
                          {"image": "images/set1/q3.jpg",
                           "answer": "Describe people, location, actions, and any objects in the foreground and background."},
                          {"image": "images/set1/q4.jpg",
                           "answer": "Comment on the setting, number of people, what they appear to be doing, and the mood."},
                      ],
                      "part3": {
                          "background": "Imagine that a Canadian marketing firm is doing research. "
                                        "You have agreed to participate in a telephone interview about workplace preferences.",
                          "questions": [
                              {"text": "How long have you been working in your current industry?",
                               "answer": "I have been working in [industry] for [X] years. I started as a [role]..."},
                              {"text": "What do you find most challenging about your job?",
                               "answer": "The most challenging aspect is [challenge]. However, I manage it by [strategy]..."},
                              {"text": "If you could redesign your workplace, what changes would you make and why?",
                               "answer": "I would introduce [change 1] and [change 2] because they would improve [benefit]. "
                                         "For example, flexible hours would increase productivity by allowing..."},
                          ],
                      },
                      "part4": {
                          "info": "Community Library — Spring Events\nDate: Saturday, April 12\n\n"
                                  "10:00 AM — Library Opens / Welcome Coffee\n"
                                  "10:30 AM — Author Talk: Writing Your First Novel\n"
                                  "12:00 PM — Lunch Break\n"
                                  "01:00 PM — Children's Story Hour (Room 201)\n"
                                  "02:30 PM — Book Club Discussion\n"
                                  "05:30 PM — Raffle Draw & Closing",
                          "questions": [
                              {"text": "What time does the library open and what is offered?",
                               "answer": "The library opens at 10:00 AM with welcome coffee for attendees."},
                              {"text": "Where can visitors get lunch and at what time?",
                               "answer": "Visitors can get lunch at the café on the Ground Floor. The lunch break begins at 12:00 PM."},
                              {"text": "A friend arrives at 1 PM. Which events can she attend, and which suits a book lover?",
                               "answer": "She can attend Children's Story Hour, Book Club Discussion, Local Poets Panel, and the Raffle. "
                                         "The Book Club Discussion at 2:30 PM would be best for someone who enjoys discussing books."},
                          ],
                      },
                      "part5": {
                          "text": "Some companies allow employees to work from home. "
                                  "Which do you think is more effective: working in the office or at home? Give reasons.",
                          "answer": "I believe working in the office is more effective because it facilitates collaboration. "
                                    "For example, spontaneous meetings often lead to better ideas. "
                                    "Additionally, a structured environment helps maintain focus and work-life balance.",
                      }}]}


# ── ExamEngine ───────────────────────────────────────────────────────────────
class ExamEngine(QObject):
    # ── existing signals ──────────────────────────────────────────────────────
    update_display  = pyqtSignal(dict)
    update_timer    = pyqtSignal(int, str)
    exam_finished   = pyqtSignal()
    # ── new signals ───────────────────────────────────────────────────────────
    answer_updated  = pyqtSignal(str)         # current question answer text
    skip_available  = pyqtSignal(bool)        # True = timer running → skip enabled
    rec_start       = pyqtSignal(str, str)    # (subdir, hint)
    rec_stop        = pyqtSignal()

    def __init__(self, base_dir: str):
        super().__init__()
        self._base_dir   = base_dir
        self._bank: dict = {}
        self._set_data: Optional[dict] = None

        self.tts = TTSManager()
        self.tts.finished.connect(self._on_tts_done)

        self._countdown = QTimer(self)
        self._countdown.setInterval(1000)
        self._countdown.timeout.connect(self._tick)
        self._remaining  = 0
        self._phase      = ""
        self._tts_skipped = False           # True = skip() fired during TTS

        self._steps: list[dict] = []
        self._idx = 0

        self._load_bank()

    # ── public API ────────────────────────────────────────────────────────────
    @property
    def sets(self) -> list[dict]:
        """Return [{id, name}, ...] for the set-selection UI."""
        return [{"id": s.get("id", i + 1), "name": s.get("name", f"套题 {i+1}")}
                for i, s in enumerate(self._bank.get("sets", []))]

    def load_set(self, set_id: int) -> None:
        """Select the question set by id before calling start_exam()."""
        for s in self._bank.get("sets", []):
            if s.get("id") == set_id:
                self._set_data = s
                print(f"[Engine] Loaded set {set_id}: {s.get('name', '')}")
                return
        print(f"[Engine] Set {set_id} not found.")

    def start_exam(self) -> None:
        self._countdown.stop()
        if self._set_data is None and self._bank.get("sets"):
            self._set_data = self._bank["sets"][0]
        if self._set_data is None:
            self._set_data = _default_bank()["sets"][0]

        sid = self._set_data.get("id", 1)
        self._steps = _build_steps(self._set_data, sid, self._base_dir)
        self._idx   = 0
        self._run()

    def start_part_exam(self, set_id: int, part_num: int) -> None:
        """Start practice for a single PART (1–5) using the same timing rules."""
        self._countdown.stop()
        self._set_data = None
        for s in self._bank.get("sets", []):
            if s.get("id") == set_id:
                self._set_data = s
                break
        if self._set_data is None:
            if self._bank.get("sets"):
                self._set_data = self._bank["sets"][0]
            else:
                self._set_data = _default_bank()["sets"][0]
        sid = self._set_data.get("id", 1)
        self._steps = _build_part_steps(self._set_data, sid, self._base_dir, part_num)
        self._idx = 0
        self._run()

    def skip(self) -> None:
        """
        Skip the current step immediately (Method 2 — full unlock).
        • Timer active  → stop countdown, advance on next event-loop tick
        • TTS active    → interrupt TTS, mark skipped, advance after 100 ms buffer
        """
        self.skip_available.emit(False)
        self.rec_stop.emit()

        if self._countdown.isActive():
            # ── timer phase ──────────────────────────────────────────────────
            self._countdown.stop()
            self.update_timer.emit(0, self._phase)
            QTimer.singleShot(0, self._advance)
        else:
            # ── TTS phase ────────────────────────────────────────────────────
            # Mark as skipped so _on_tts_done ignores the pending finished signal
            self._tts_skipped = True
            self.tts.interrupt()
            # 100 ms buffer: lets the audio thread fully release before advancing
            QTimer.singleShot(100, self._advance)

    def abort(self) -> None:
        """Abort exam immediately (user pressed Home button)."""
        self._countdown.stop()
        self._tts_skipped = True
        self.tts.interrupt()
        self.skip_available.emit(False)
        self.update_timer.emit(-1, "")

    def pause_timer(self) -> None:
        """Pause the active countdown without advancing (e.g. scoring dialog open)."""
        if self._countdown.isActive():
            self._countdown.stop()
            self._timer_paused = True

    def resume_timer(self) -> None:
        """Resume a previously paused countdown timer."""
        if getattr(self, '_timer_paused', False) and self._remaining > 0:
            self._timer_paused = False
            self._countdown.start()

    # ── private ───────────────────────────────────────────────────────────────
    def _load_bank(self) -> None:
        # ── 1. Try Excel (.xlsx) ──────────────────────────────────────────────
        xlsx_path = os.path.join(self._base_dir, "question_bank.xlsx")
        if os.path.isfile(xlsx_path):
            try:
                bank = self._load_bank_from_excel(xlsx_path)
                if bank.get("sets"):
                    self._bank = bank
                    print(f"[Engine] Loaded question_bank.xlsx "
                          f"({len(self._bank['sets'])} sets)")
                    return
            except Exception as exc:
                print(f"[Engine] Error loading question_bank.xlsx: {exc}")

        # ── 2. Try CSV bundle (question_bank_sets.csv + part CSVs) ───────────
        csv_sets = os.path.join(self._base_dir, "question_bank_sets.csv")
        if os.path.isfile(csv_sets):
            try:
                bank = self._load_bank_from_csv(self._base_dir)
                if bank.get("sets"):
                    self._bank = bank
                    print(f"[Engine] Loaded CSV bundle "
                          f"({len(self._bank['sets'])} sets)")
                    return
            except Exception as exc:
                print(f"[Engine] Error loading CSV bundle: {exc}")

        # ── 3. Fall back to JSON ──────────────────────────────────────────────
        for fname in ("question_bank.json", "questions.json"):
            path = os.path.join(self._base_dir, fname)
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        raw = json.load(f)
                    # Detect old single-set format (has "part1" key at top level)
                    if "part1" in raw and "sets" not in raw:
                        raw = {"sets": [dict(raw, id=1, name="套题 1")]}
                    self._bank = raw
                    print(f"[Engine] Loaded {fname} ({len(self._bank.get('sets', []))} sets)")
                    return
                except Exception as exc:
                    print(f"[Engine] Error loading {fname}: {exc}")

        print("[Engine] No question file found; using built-in defaults.")
        self._bank = _default_bank()

    # ── Excel loader ──────────────────────────────────────────────────────────
    def _load_bank_from_excel(self, path: str) -> dict:
        """
        Load question bank from a multi-sheet .xlsx file.

        Expected sheet layout (column names in row 1):
          Sets    : set_id | set_name
          Part1   : set_id | text      | answer
          Part2   : set_id | image     | answer
          Part3   : set_id | background | question_text | answer
                    (background filled only on the first row per set)
          Part4   : set_id | info       | question_text | answer
                    (info filled only on the first row per set)
          Part5   : set_id | text       | answer
        """
        import openpyxl  # optional dependency — installed via requirements.txt
        wb = openpyxl.load_workbook(path, data_only=True)

        def _rows(sheet_name: str) -> list[dict]:
            if sheet_name not in wb.sheetnames:
                return []
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            hdrs = [str(h).strip() if h is not None else "" for h in rows[0]]
            return [
                {hdrs[i]: (row[i] if i < len(row) else None)
                 for i in range(len(hdrs))}
                for row in rows[1:]
                if any(c is not None for c in row)
            ]

        def _str(v) -> str:
            return str(v).strip() if v is not None else ""

        def _int(v) -> int:
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0

        # ── Sets ─────────────────────────────────────────────────────────────
        sets_map: dict[int, dict] = {}
        for r in _rows("Sets"):
            sid = _int(r.get("set_id"))
            if sid:
                sets_map[sid] = {
                    "id":    sid,
                    "name":  _str(r.get("set_name")) or f"套题 {sid}",
                    "part1": [],
                    "part2": [],
                    "part3": {"background": "", "questions": []},
                    "part4": {"info": "",       "questions": []},
                    "part5": {"text": "",        "answer":   ""},
                }

        # ── Part 1 ───────────────────────────────────────────────────────────
        for r in _rows("Part1"):
            sid = _int(r.get("set_id"))
            if sid in sets_map:
                sets_map[sid]["part1"].append(
                    {"text": _str(r.get("text")), "answer": _str(r.get("answer"))}
                )

        # ── Part 2 ───────────────────────────────────────────────────────────
        for r in _rows("Part2"):
            sid = _int(r.get("set_id"))
            if sid in sets_map:
                sets_map[sid]["part2"].append(
                    {"image": _str(r.get("image")), "answer": _str(r.get("answer"))}
                )

        # ── Part 3 ───────────────────────────────────────────────────────────
        for r in _rows("Part3"):
            sid = _int(r.get("set_id"))
            if sid not in sets_map:
                continue
            bg = _str(r.get("background"))
            if bg:
                sets_map[sid]["part3"]["background"] = bg
            sets_map[sid]["part3"]["questions"].append(
                {"text": _str(r.get("question_text")), "answer": _str(r.get("answer"))}
            )

        # ── Part 4 ───────────────────────────────────────────────────────────
        for r in _rows("Part4"):
            sid = _int(r.get("set_id"))
            if sid not in sets_map:
                continue
            info = _str(r.get("info"))
            if info:
                sets_map[sid]["part4"]["info"] = info
            sets_map[sid]["part4"]["questions"].append(
                {"text": _str(r.get("question_text")), "answer": _str(r.get("answer"))}
            )

        # ── Part 5 ───────────────────────────────────────────────────────────
        for r in _rows("Part5"):
            sid = _int(r.get("set_id"))
            if sid in sets_map:
                sets_map[sid]["part5"] = {
                    "text":   _str(r.get("text")),
                    "answer": _str(r.get("answer")),
                }

        return {"sets": list(sets_map.values())}

    # ── CSV bundle loader ─────────────────────────────────────────────────────
    def _load_bank_from_csv(self, base_dir: str) -> dict:
        """
        Load question bank from a bundle of CSV files located in base_dir.

        Files (UTF-8, with BOM support):
          question_bank_sets.csv   — set_id, set_name
          question_bank_part1.csv  — set_id, text, answer
          question_bank_part2.csv  — set_id, image, answer
          question_bank_part3.csv  — set_id, background, question_text, answer
          question_bank_part4.csv  — set_id, info, question_text, answer
          question_bank_part5.csv  — set_id, text, answer
        """
        def _read(fname: str) -> list[dict]:
            p = os.path.join(base_dir, fname)
            if not os.path.isfile(p):
                return []
            with open(p, encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))

        def _s(d: dict, key: str) -> str:
            return (d.get(key) or "").strip()

        def _i(d: dict, key: str) -> int:
            try:
                return int((d.get(key) or "0").strip())
            except ValueError:
                return 0

        sets_map: dict[int, dict] = {}
        for r in _read("question_bank_sets.csv"):
            sid = _i(r, "set_id")
            if sid:
                sets_map[sid] = {
                    "id":    sid,
                    "name":  _s(r, "set_name") or f"套题 {sid}",
                    "part1": [],
                    "part2": [],
                    "part3": {"background": "", "questions": []},
                    "part4": {"info": "",       "questions": []},
                    "part5": {"text": "",        "answer":   ""},
                }

        for r in _read("question_bank_part1.csv"):
            sid = _i(r, "set_id")
            if sid in sets_map:
                sets_map[sid]["part1"].append(
                    {"text": _s(r, "text"), "answer": _s(r, "answer")}
                )

        for r in _read("question_bank_part2.csv"):
            sid = _i(r, "set_id")
            if sid in sets_map:
                sets_map[sid]["part2"].append(
                    {"image": _s(r, "image"), "answer": _s(r, "answer")}
                )

        for r in _read("question_bank_part3.csv"):
            sid = _i(r, "set_id")
            if sid not in sets_map:
                continue
            bg = _s(r, "background")
            if bg:
                sets_map[sid]["part3"]["background"] = bg
            sets_map[sid]["part3"]["questions"].append(
                {"text": _s(r, "question_text"), "answer": _s(r, "answer")}
            )

        for r in _read("question_bank_part4.csv"):
            sid = _i(r, "set_id")
            if sid not in sets_map:
                continue
            info = _s(r, "info")
            if info:
                sets_map[sid]["part4"]["info"] = info
            sets_map[sid]["part4"]["questions"].append(
                {"text": _s(r, "question_text"), "answer": _s(r, "answer")}
            )

        for r in _read("question_bank_part5.csv"):
            sid = _i(r, "set_id")
            if sid in sets_map:
                sets_map[sid]["part5"] = {
                    "text":   _s(r, "text"),
                    "answer": _s(r, "answer"),
                }

        return {"sets": list(sets_map.values())}

    def _run(self) -> None:
        if self._idx >= len(self._steps):
            self.exam_finished.emit()
            return

        step  = self._steps[self._idx]
        stype = step.get("type")

        if stype == "screen":
            self.update_display.emit({
                "title":     step.get("title", ""),
                "content":   step.get("content", ""),
                "secondary": step.get("secondary", ""),
                "image":     step.get("image", ""),
            })
            self.update_timer.emit(-1, "")
            self.skip_available.emit(False)
            ans = step.get("answer", "")
            if ans is not None:
                self.answer_updated.emit(ans)
            QTimer.singleShot(50, self._advance)

        elif stype == "tts":
            self._tts_skipped = False
            self.skip_available.emit(True)   # skip allowed during TTS (opt-2 unlock)
            self.tts.speak(step.get("text", ""))

        elif stype == "timer":
            self._phase     = step.get("phase", "")
            self._remaining = step.get("duration", 0)
            self.update_timer.emit(self._remaining, self._phase)
            self.skip_available.emit(True)
            self._countdown.start()

        elif stype == "set_answer":
            self.answer_updated.emit(step.get("answer", ""))
            QTimer.singleShot(0, self._advance)

        elif stype == "record_start":
            self.rec_start.emit(step.get("subdir", "records"), step.get("hint", "resp"))
            QTimer.singleShot(0, self._advance)

        elif stype == "record_stop":
            self.rec_stop.emit()
            QTimer.singleShot(0, self._advance)

        elif stype == "end":
            self.skip_available.emit(False)
            self.exam_finished.emit()

    def _advance(self) -> None:
        self._idx += 1
        self._run()

    def _on_tts_done(self) -> None:
        """Called when TTS finishes — ignored if skip() was called first."""
        if self._tts_skipped:
            self._tts_skipped = False   # reset for next TTS step
            return
        self._advance()

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._countdown.stop()
            self.update_timer.emit(0, self._phase)
            self.skip_available.emit(False)
            self._advance()
        else:
            self.update_timer.emit(self._remaining, self._phase)
