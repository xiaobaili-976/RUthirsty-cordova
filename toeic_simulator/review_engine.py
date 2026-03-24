"""
Review Engine — builds a flat question list from ExamEngine's bank for review mode.

Each question dict:
  id          str  "{set_id}:{part_key}:{index}"  e.g. "1:p1:0", "2:p3:2"
  set_id      int
  set_name    str
  part        int  1–5
  part_label  str  human-readable part name
  title       str  display title
  content     str  main text content (empty for Part 2)
  image       str  image path (Part 2 only, may be relative to base_dir)
  secondary   str  spoken question text (Part 3 / Part 4 sub-questions)
  answer      str  reference answer
"""
import random


class ReviewEngine:
    """
    Provides question lists for the four review sub-modes:
      random    — all questions, randomly shuffled
      speed     — all questions in order (UI shows answers automatically)
      high_freq — questions marked high-freq (shuffled)
      weak      — questions marked weak (shuffled)
    """

    def __init__(self, exam_engine):
        self._engine = exam_engine

    # ── Public API ────────────────────────────────────────────────────────────

    def get_random_questions(self) -> list:
        qs = self._build_all()
        random.shuffle(qs)
        return qs

    def get_all_questions(self) -> list:
        """All questions in bank order (used for speed-review mode)."""
        return self._build_all()

    def get_weak_questions(self, marks_mgr) -> list:
        weak_ids = marks_mgr.get_weak_ids()
        qs = [q for q in self._build_all() if q["id"] in weak_ids]
        random.shuffle(qs)
        return qs

    def get_high_freq_questions(self, marks_mgr) -> list:
        hf_ids = marks_mgr.get_high_freq_ids()
        qs = [q for q in self._build_all() if q["id"] in hf_ids]
        random.shuffle(qs)
        return qs

    # ── Private ───────────────────────────────────────────────────────────────

    def _build_all(self) -> list:
        questions = []
        for s in self._engine._bank.get("sets", []):
            sid   = s.get("id",   0)
            sname = s.get("name", f"套题 {sid}")

            # Part 1 — Read Aloud
            for i, item in enumerate(s.get("part1") or []):
                questions.append({
                    "id":         f"{sid}:p1:{i}",
                    "set_id":     sid,
                    "set_name":   sname,
                    "part":       1,
                    "part_label": "Part 1 · Read Aloud",
                    "title":      f"{sname} — Part 1  Q{i + 1}",
                    "content":    item.get("text",   ""),
                    "image":      "",
                    "secondary":  "",
                    "answer":     item.get("answer", ""),
                })

            # Part 2 — Describe a Picture
            for i, item in enumerate(s.get("part2") or []):
                questions.append({
                    "id":         f"{sid}:p2:{i}",
                    "set_id":     sid,
                    "set_name":   sname,
                    "part":       2,
                    "part_label": "Part 2 · Describe a Picture",
                    "title":      f"{sname} — Part 2  Q{i + 1}",
                    "content":    "",
                    "image":      item.get("image",  ""),
                    "secondary":  "",
                    "answer":     item.get("answer", ""),
                })

            # Part 3 — Respond to Questions
            p3 = s.get("part3") or {}
            bg = p3.get("background", "")
            for i, q in enumerate(p3.get("questions") or []):
                questions.append({
                    "id":         f"{sid}:p3:{i}",
                    "set_id":     sid,
                    "set_name":   sname,
                    "part":       3,
                    "part_label": "Part 3 · Respond to Questions",
                    "title":      f"{sname} — Part 3  Q{i + 1}",
                    "content":    bg,
                    "image":      "",
                    "secondary":  q.get("text",   ""),
                    "answer":     q.get("answer", ""),
                })

            # Part 4 — Use Information Provided
            p4   = s.get("part4") or {}
            info = p4.get("info", "")
            for i, q in enumerate(p4.get("questions") or []):
                questions.append({
                    "id":         f"{sid}:p4:{i}",
                    "set_id":     sid,
                    "set_name":   sname,
                    "part":       4,
                    "part_label": "Part 4 · Use Information Provided",
                    "title":      f"{sname} — Part 4  Q{i + 1}",
                    "content":    info,
                    "image":      "",
                    "secondary":  q.get("text",   ""),
                    "answer":     q.get("answer", ""),
                })

            # Part 5 — Express an Opinion
            p5 = s.get("part5") or {}
            if p5.get("text"):
                questions.append({
                    "id":         f"{sid}:p5:0",
                    "set_id":     sid,
                    "set_name":   sname,
                    "part":       5,
                    "part_label": "Part 5 · Express an Opinion",
                    "title":      f"{sname} — Part 5",
                    "content":    p5.get("text",   ""),
                    "image":      "",
                    "secondary":  "",
                    "answer":     p5.get("answer", ""),
                })

        return questions
