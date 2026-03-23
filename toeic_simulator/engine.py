"""
Exam Engine — state machine that drives the full TOEIC Speaking Test flow.

Each exam is modelled as an ordered list of *steps*; each step is a dict:
  {"type": "screen",   "title": ..., "content": ..., "secondary": ..., "image": ...}
  {"type": "tts",      "text": ...}
  {"type": "timer",    "duration": <int seconds>, "phase": ...}
  {"type": "end"}

Execution is fully sequential:
  • "screen"  → update UI, then advance after a 50ms paint delay
  • "tts"     → speak text; advance when TTSManager emits finished
  • "timer"   → count down; advance when counter reaches 0
  • "end"     → emit exam_finished
"""
import os
import sys
import json
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from tts_manager import TTSManager


# ──────────────────────────────────────────────
#  Fixed instruction texts
# ──────────────────────────────────────────────
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


# ──────────────────────────────────────────────
#  Step-list builder
# ──────────────────────────────────────────────
def _build_steps(questions: dict, base_dir: str) -> list[dict]:
    """Return the complete ordered list of exam steps."""
    steps: list[dict] = []

    def s(title="", content="", secondary="", image=""):
        """Helper: screen step."""
        return {"type": "screen", "title": title, "content": content,
                "secondary": secondary, "image": image}

    def t(text):
        return {"type": "tts", "text": text}

    def tm(duration, phase=""):
        return {"type": "timer", "duration": duration, "phase": phase}

    PREP  = "Preparation Time"
    RESP  = "Response Time"

    # ── PART 1 ──────────────────────────────────────────────────────────────
    steps += [
        s("Questions 1 - 2: Read a text aloud", _PART1_INTRO),
        t(_PART1_INTRO),
    ]
    for i, item in enumerate((questions.get("part1") or [])[:2], 1):
        steps += [
            s(f"Question {i} of 11", item.get("text", "")),
            t(_BEGIN_PREPARING),
            tm(45, PREP),
            t(_BEGIN_READING),
            tm(45, RESP),
        ]

    # ── PART 2 ──────────────────────────────────────────────────────────────
    steps += [
        s("Questions 3 - 4: Describe a picture", _PART2_INTRO),
        t(_PART2_INTRO),
    ]
    for i, item in enumerate((questions.get("part2") or [])[:2], 3):
        raw_path = item.get("image", "")
        img_path = raw_path if os.path.isabs(raw_path) else os.path.join(base_dir, raw_path)
        steps += [
            s(f"Question {i} of 11", image=img_path),
            t(_BEGIN_PREPARING),
            tm(45, PREP),
            t(_BEGIN_SPEAKING),
            tm(30, RESP),
        ]

    # ── PART 3 ──────────────────────────────────────────────────────────────
    steps += [
        s("Questions 5 - 7: Respond to questions", _PART3_INTRO),
        t(_PART3_INTRO),
    ]
    p3   = questions.get("part3") or {}
    bg   = p3.get("background", "")
    p3qs = (p3.get("questions") or [])[:3]

    steps += [
        s("Questions 5 - 7 of 11", bg),
        t(bg),
    ]
    for idx, (q_num, duration) in enumerate([(5, 15), (6, 15), (7, 30)]):
        if idx < len(p3qs):
            qt = p3qs[idx].get("text", "")
            steps += [
                {"type": "screen", "title": f"Question {q_num} of 11",
                 "content": bg, "secondary": qt, "image": ""},
                t(qt),
                t(_BEGIN_PREPARING),
                tm(3, PREP),
                t(_BEGIN_SPEAKING),
                tm(duration, RESP),
            ]

    # ── PART 4 ──────────────────────────────────────────────────────────────
    steps += [
        s("Questions 8 - 10: Respond to questions using information provided",
          _PART4_INTRO),
        t(_PART4_INTRO),
    ]
    p4   = questions.get("part4") or {}
    info = p4.get("info", "")
    p4qs = (p4.get("questions") or [])[:3]

    steps += [
        s("Questions 8 \u2013 10 of 11", info),
        t(_BEGIN_PREPARING),
        tm(45, PREP),
    ]
    for idx, (q_num, duration) in enumerate([(8, 15), (9, 15), (10, 30)]):
        if idx < len(p4qs):
            qt = p4qs[idx].get("text", "")
            plays = [t(qt), t(qt)] if q_num == 10 else [t(qt)]
            steps += plays + [
                t(_BEGIN_PREPARING),
                tm(3, PREP),
                t(_BEGIN_SPEAKING),
                tm(duration, RESP),
            ]

    # ── PART 5 ──────────────────────────────────────────────────────────────
    steps += [
        s("Question 11: Express an opinion", _PART5_INTRO),
        t(_PART5_INTRO),
    ]
    q11 = (questions.get("part5") or {}).get("text", "")
    steps += [
        s("Question 11 of 11", q11),
        t(q11),
        t(_BEGIN_PREPARING),
        tm(45, PREP),
        t(_BEGIN_SPEAKING),
        tm(60, RESP),
    ]

    steps.append({"type": "end"})
    return steps


# ──────────────────────────────────────────────
#  Default questions (fallback if JSON missing)
# ──────────────────────────────────────────────
def _default_questions() -> dict:
    return {
        "part1": [
            {"text": "Good morning, everyone. Welcome to the annual company meeting. "
                     "Today we will discuss the financial results for the past year and "
                     "our strategic plans for the upcoming year. Please take a seat and "
                     "make sure your microphones are working properly."},
            {"text": "Attention all passengers. Due to heavy rainfall this morning, "
                     "the train service between Central Station and Riverside has been "
                     "temporarily suspended. Replacement buses are available at Exit B. "
                     "We apologize for any inconvenience this may cause."},
        ],
        "part2": [
            {"image": "images/q3.jpg"},
            {"image": "images/q4.jpg"},
        ],
        "part3": {
            "background": (
                "Directions: In this part of the test, you will answer three questions "
                "based on the information below.\n\n"
                "Imagine that a Canadian marketing firm is doing research in your area. "
                "You have agreed to participate in a telephone interview about workplace "
                "preferences."
            ),
            "questions": [
                {"text": "How long have you been working in your current industry?"},
                {"text": "What do you find most challenging about your job?"},
                {"text": "If you could redesign your workplace to improve both "
                         "productivity and employee well-being, what specific changes "
                         "would you make, and how do you think those changes would "
                         "benefit the team?"},
            ],
        },
        "part4": {
            "info": (
                "Riverside Community Library — Spring Events Schedule\n\n"
                "Date: Saturday, April 12\n"
                "Venue: Riverside Community Library, 2nd Floor\n\n"
                "10:00 AM  — Library Opens / Coffee & Welcome\n"
                "10:30 AM  — Author Talk: Writing Your First Novel\n"
                "12:00 PM  — Lunch Break (café on Ground Floor)\n"
                "01:00 PM  — Children's Story Hour (Room 201)\n"
                "02:30 PM  — Book Club Discussion: The Sea at Dawn\n"
                "04:00 PM  — Panel: Local Poets & Writers\n"
                "05:30 PM  — Raffle Draw & Closing"
            ),
            "questions": [
                {"text": "What time does the library open and what is offered when it opens?"},
                {"text": "Where can visitors get lunch, and at what time does the lunch break begin?"},
                {"text": "A friend wants to attend but cannot arrive until one o'clock. "
                         "Which events can she attend, and which would be best for someone "
                         "who enjoys discussing books with other readers?"},
            ],
        },
        "part5": {
            "text": (
                "Some companies require all employees to work in the office every day, "
                "while others allow employees to work from home some or all of the time. "
                "Which policy do you think is better for both the company and its employees? "
                "Give specific reasons and examples to support your opinion."
            )
        },
    }


# ──────────────────────────────────────────────
#  ExamEngine
# ──────────────────────────────────────────────
class ExamEngine(QObject):
    update_display = pyqtSignal(dict)   # {"title", "content", "secondary", "image"}
    update_timer   = pyqtSignal(int, str)  # (seconds_remaining, phase_label); -1 = hide
    exam_finished  = pyqtSignal()

    def __init__(self, base_dir: str):
        super().__init__()
        self._base_dir = base_dir
        self._questions: dict = {}

        self.tts = TTSManager()
        self.tts.finished.connect(self._advance)

        self._countdown = QTimer(self)
        self._countdown.setInterval(1000)
        self._countdown.timeout.connect(self._tick)
        self._remaining = 0
        self._phase = ""

        self._steps: list[dict] = []
        self._idx = 0

        self._load_questions()

    # ── public ──────────────────────────────────────────────────────────────
    def start_exam(self) -> None:
        self._countdown.stop()
        self._steps = _build_steps(self._questions, self._base_dir)
        self._idx = 0
        self._run()

    # ── private ─────────────────────────────────────────────────────────────
    def _load_questions(self) -> None:
        path = os.path.join(self._base_dir, "questions.json")
        try:
            with open(path, encoding="utf-8") as f:
                self._questions = json.load(f)
            print(f"[Engine] Loaded questions from {path}")
        except Exception as exc:
            print(f"[Engine] Could not load questions.json ({exc}); using defaults.")
            self._questions = _default_questions()

    def _run(self) -> None:
        if self._idx >= len(self._steps):
            self.exam_finished.emit()
            return

        step = self._steps[self._idx]
        stype = step.get("type")

        if stype == "screen":
            self.update_display.emit({
                "title":     step.get("title", ""),
                "content":   step.get("content", ""),
                "secondary": step.get("secondary", ""),
                "image":     step.get("image", ""),
            })
            self.update_timer.emit(-1, "")
            QTimer.singleShot(50, self._advance)   # let Qt paint before next step

        elif stype == "tts":
            self.tts.speak(step.get("text", ""))

        elif stype == "timer":
            self._phase     = step.get("phase", "")
            self._remaining = step.get("duration", 0)
            self.update_timer.emit(self._remaining, self._phase)
            self._countdown.start()

        elif stype == "end":
            self.exam_finished.emit()

    def _advance(self) -> None:
        self._idx += 1
        self._run()

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._countdown.stop()
            self.update_timer.emit(0, self._phase)
            self._advance()
        else:
            self.update_timer.emit(self._remaining, self._phase)
