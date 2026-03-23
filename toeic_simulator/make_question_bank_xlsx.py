"""
make_question_bank_xlsx.py
──────────────────────────
Converts question_bank.json → question_bank.xlsx (one-time migration tool).

Run once from the toeic_simulator/ directory:
    python make_question_bank_xlsx.py

Sheet layout produced
─────────────────────
  Sets    : set_id | set_name
  Part1   : set_id | text      | answer
  Part2   : set_id | image     | answer
  Part3   : set_id | background | question_text | answer
            (background written only on first question row per set)
  Part4   : set_id | info       | question_text | answer
            (info written only on first question row per set)
  Part5   : set_id | text       | answer

After generating the file, edit question_bank.xlsx directly in Excel to add /
modify question sets.  The simulator reads .xlsx first, then falls back to .json.
"""
import json
import os
import sys

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError:
    sys.exit("openpyxl is required.  Run:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))


def _hdr(ws, columns: list[str]):
    """Write a bold header row and set column widths."""
    fill = PatternFill("solid", fgColor="003087")
    font = Font(bold=True, color="FFFFFF", name="Calibri")
    for col_idx, name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=name)
        cell.font = font
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 18


def _col_widths(ws, widths: list[int]):
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def convert(json_path: str, xlsx_path: str):
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    # Support old single-set format
    if "part1" in raw and "sets" not in raw:
        raw = {"sets": [dict(raw, id=1, name="套题 1")]}

    sets = raw.get("sets", [])

    wb = openpyxl.Workbook()
    wb.remove(wb.active)          # remove the default empty sheet

    # ── Sets ─────────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Sets")
    _hdr(ws, ["set_id", "set_name"])
    _col_widths(ws, [8, 40])
    for s in sets:
        ws.append([s.get("id", ""), s.get("name", "")])

    # ── Part 1 ───────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Part1")
    _hdr(ws, ["set_id", "text", "answer"])
    _col_widths(ws, [8, 60, 80])
    for s in sets:
        for item in (s.get("part1") or []):
            ws.append([s["id"], item.get("text", ""), item.get("answer", "")])

    # ── Part 2 ───────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Part2")
    _hdr(ws, ["set_id", "image", "answer"])
    _col_widths(ws, [8, 40, 80])
    for s in sets:
        for item in (s.get("part2") or []):
            ws.append([s["id"], item.get("image", ""), item.get("answer", "")])

    # ── Part 3 ───────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Part3")
    _hdr(ws, ["set_id", "background", "question_text", "answer"])
    _col_widths(ws, [8, 70, 60, 80])
    for s in sets:
        p3 = s.get("part3") or {}
        bg = p3.get("background", "")
        for idx, q in enumerate(p3.get("questions") or []):
            # background only on first question row per set
            ws.append([s["id"], bg if idx == 0 else "", q.get("text", ""), q.get("answer", "")])

    # ── Part 4 ───────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Part4")
    _hdr(ws, ["set_id", "info", "question_text", "answer"])
    _col_widths(ws, [8, 70, 60, 80])
    for s in sets:
        p4 = s.get("part4") or {}
        info = p4.get("info", "")
        for idx, q in enumerate(p4.get("questions") or []):
            ws.append([s["id"], info if idx == 0 else "", q.get("text", ""), q.get("answer", "")])

    # ── Part 5 ───────────────────────────────────────────────────────────────
    ws = wb.create_sheet("Part5")
    _hdr(ws, ["set_id", "text", "answer"])
    _col_widths(ws, [8, 60, 80])
    for s in sets:
        p5 = s.get("part5") or {}
        ws.append([s["id"], p5.get("text", ""), p5.get("answer", "")])

    # Wrap text in all data cells for readability
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(xlsx_path)
    print(f"Saved → {xlsx_path}  ({len(sets)} sets, {sum(wb[s].max_row - 1 for s in wb.sheetnames)} data rows)")


if __name__ == "__main__":
    json_src  = os.path.join(HERE, "question_bank.json")
    xlsx_dest = os.path.join(HERE, "question_bank.xlsx")

    if not os.path.isfile(json_src):
        sys.exit(f"Source not found: {json_src}")

    if os.path.isfile(xlsx_dest):
        ans = input(f"{xlsx_dest} already exists.  Overwrite? [y/N] ").strip().lower()
        if ans != "y":
            sys.exit("Aborted.")

    convert(json_src, xlsx_dest)
