import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CompositionThemesContractTests(unittest.TestCase):
    def test_skill_routes_all_four_reference_themes_through_one_document(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        themes_path = ROOT / "references" / "04-reference-theme-prompt.md"

        self.assertTrue(themes_path.is_file())
        self.assertIn("04-reference-theme-prompt.md", skill)
        self.assertFalse((ROOT / "references" / "04-reference-themes.md").exists())
        self.assertFalse((ROOT / "references" / "05-mg-themes.md").exists())
        self.assertFalse(
            (ROOT / "references" / "04-theme-ppt-focus-portrait.md").exists()
        )

        themes = themes_path.read_text(encoding="utf-8")
        for name in (
            "floating-overlay",
            "mg-with-presenter-window",
            "switching",
            "PPT Focus Portrait",
        ):
            self.assertIn(name, themes)

    def test_reference_themes_are_optional_shortcuts_for_natural_language(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        themes = (ROOT / "references" / "04-reference-theme-prompt.md").read_text(
            encoding="utf-8"
        )

        for text in (readme, skill, themes):
            self.assertIn("自然语言", text)
        self.assertIn("快速生成相似视频", readme)
        self.assertIn("不是必选项", themes)
        self.assertIn("# 参考主题 Prompt", themes)
        self.assertIn("你可以参考以下效果", themes)
        self.assertIn("不要要求用户选择主题", themes)

    def test_themes_remain_prompt_references_not_validator_modes(self):
        validator = (ROOT / "scripts" / "validate_plan.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("mg_theme", validator)
        self.assertNotIn("allowed_themes", validator)


if __name__ == "__main__":
    unittest.main()
