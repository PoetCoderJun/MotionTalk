import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class PptFocusPortraitThemeContractTests(unittest.TestCase):
    def setUp(self):
        self.theme_path = SKILL_ROOT / "references" / "04-theme-ppt-focus-portrait.md"

    def test_theme_is_a_prompt_reference_not_a_code_mode(self):
        self.assertTrue(self.theme_path.exists())
        theme = self.theme_path.read_text(encoding="utf-8")
        validator = (SKILL_ROOT / "scripts" / "validate_plan.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("PPT Focus Portrait", theme)
        self.assertIn("比例", theme)
        self.assertIn("不是代码模式", theme)
        self.assertNotIn("ppt-focus-portrait", validator)

    def test_theme_preserves_the_proven_visual_hierarchy(self):
        theme = self.theme_path.read_text(encoding="utf-8")
        for required in (
            "PPT 为第一视觉层级",
            "字幕严格最多两行",
            "右下人物窗",
            "左下花字",
            "底部章节进度",
            "最长字幕",
            "不得用省略号",
        ):
            self.assertIn(required, theme)

    def test_skill_routes_explicit_theme_requests_to_the_reference(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        planning = (SKILL_ROOT / "references" / "01-plan.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("04-theme-ppt-focus-portrait.md", skill)
        self.assertIn("04-theme-ppt-focus-portrait.md", planning)


if __name__ == "__main__":
    unittest.main()
