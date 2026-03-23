"""
template_manager.py
───────────────────
Loads high-score answer templates for the TOEIC Speaking Test.

Source file : answer_templates.json in BASE_DIR (editable by user/teacher)
Fallback    : built-in defaults embedded here (one template per part)
"""
import json
import os

# ── Built-in defaults ─────────────────────────────────────────────────────────
_DEFAULT_TEMPLATES = {
    "Part1": [
        {
            "title": "朗读万能框架",
            "content": (
                "【准备45秒】\n"
                "1. 快速默读，标注重音词（名词、动词、数字、专有名词）。\n"
                "2. 标出断句点（逗号、句号、分号）。\n"
                "3. 在脑中模拟一遍语调变化。\n\n"
                "【作答45秒】\n"
                "• 匀速朗读，每句话结束后略作停顿（0.3 秒）。\n"
                "• 陈述句末↓降调，疑问句末↑升调。\n"
                "• 数字与专有名词放慢，字字清晰。\n\n"
                "⭐ 示例开场：\n"
                "\"Good morning, everyone. Today I'd like to announce that…\""
            ),
        },
    ],
    "Part2": [
        {
            "title": "图片描述结构模板（45s准备 / 30s作答）",
            "content": (
                "Opening  : This picture shows [location / setting].\n"
                "People   : There are [number] people who appear to be [action].\n"
                "Foreground: In the foreground, I can see [object / detail].\n"
                "Background: In the background, there is/are [element].\n"
                "Mood     : The overall atmosphere seems [adjective].\n"
                "Closing  : This looks like [interpretation / guess].\n\n"
                "⭐ 常用词组：\n"
                "in the foreground / background / center of the image\n"
                "appear to be + V-ing  |  is/are wearing  |  is/are holding\n"
                "on the left/right  |  next to  |  in front of"
            ),
        },
    ],
    "Part3": [
        {
            "title": "即兴问答答题公式（Q5/Q6: 15s | Q7: 30s）",
            "content": (
                "Q5 / Q6（15秒）：直接答 → 简短理由\n"
                "  \"I [answer]. For example / because [brief reason].\"\n\n"
                "Q7（30秒）：立场 → 原因1 → 原因2 → 总结\n"
                "  \"I would [action] because, first, [reason 1].\n"
                "   Furthermore, [reason 2].\n"
                "   Therefore, I think [restate position].\"\n\n"
                "⭐ 过渡词：\n"
                "First, … / In addition, … / For example, … / As a result, …\n"
                "However, … / On the other hand, … / Therefore, …"
            ),
        },
    ],
    "Part4": [
        {
            "title": "信息题答题技巧（45s读信息 | Q8/Q9: 15s | Q10: 30s）",
            "content": (
                "【准备45秒】快速定位：日期、时间、地点、人物、数字等关键信息。\n\n"
                "Q8 / Q9（15秒）——直接引用信息，无需个人观点：\n"
                "  \"According to the information, [fact from schedule/text].\"\n\n"
                "Q10（30秒）——可结合推理：\n"
                "  \"Based on the information, I would recommend [option]\n"
                "   because [reason from text]. Additionally, [detail].\"\n\n"
                "⭐ 注意：Q10 会播放两遍，请利用第二遍确认关键词。"
            ),
        },
    ],
    "Part5": [
        {
            "title": "观点表达黄金结构（45s准备 / 60s作答）",
            "content": (
                "【准备45秒】脑中草拟：立场 + 2个理由 + 结束语。\n\n"
                "【60秒作答时间轴】\n"
                "[0–10s]  立场：\"In my opinion, [position].\"\n"
                "[10–35s] 理由1：\"First, [reason]. For instance, [example].\"\n"
                "[35–55s] 理由2：\"Furthermore, [reason]. This means [impact].\"\n"
                "[55–60s] 总结：\"Therefore, I strongly believe [restate].\"\n\n"
                "⭐ 加分词组：\n"
                "significantly / particularly / consequently / as a result\n"
                "It is widely acknowledged that… / Research suggests that…"
            ),
        },
    ],
}


class TemplateManager:
    """Loads and serves answer templates by part name."""

    def __init__(self, base_dir: str):
        self._path = os.path.join(base_dir, "answer_templates.json")
        self._templates: dict = {}
        self._load()

    def get_templates(self, part: str) -> list:
        """
        Return list of {title, content} dicts for the given part.
        part: "Part1" … "Part5"
        Falls back to built-in defaults if part not in loaded file.
        """
        user = self._templates.get(part)
        if user:
            return user
        return _DEFAULT_TEMPLATES.get(part, [])

    def all_parts(self) -> list:
        return ["Part1", "Part2", "Part3", "Part4", "Part5"]

    # ── Private ───────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not os.path.isfile(self._path):
            self._templates = {}
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            self._templates = data if isinstance(data, dict) else {}
        except Exception as exc:
            print(f"[TemplateManager] Load error: {exc}")
            self._templates = {}
