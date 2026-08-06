import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CompositionThemesContractTests(unittest.TestCase):
    def test_skill_routes_all_four_prompt_themes(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        foundations_path = ROOT / "references" / "05-mg-themes.md"

        self.assertTrue(foundations_path.is_file())
        self.assertIn("05-mg-themes.md", skill)
        self.assertIn("04-theme-ppt-focus-portrait.md", skill)

        foundations = foundations_path.read_text(encoding="utf-8")
        for name in (
            "floating-overlay",
            "mg-with-presenter-window",
            "switching",
        ):
            self.assertIn(name, foundations)

    def test_themes_remain_prompt_references_not_validator_modes(self):
        validator = (ROOT / "scripts" / "validate_plan.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("mg_theme", validator)
        self.assertNotIn("allowed_themes", validator)


if __name__ == "__main__":
    unittest.main()
