import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CloseEvidencePortraitThemeContractTests(unittest.TestCase):
    def test_readmes_publish_the_recent_primary_theme_and_visual(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README_EN.md").read_text(encoding="utf-8")
        asset = "assets/readme/theme-close-evidence-portrait.webp"

        self.assertIn("近景证据流（近期主用）", zh)
        self.assertIn("这是我近期发布视频的主要主题", zh)
        self.assertIn("current primary style", en)
        self.assertIn("This is my primary theme for recent videos", en)
        self.assertIn(asset, zh)
        self.assertIn(asset, en)

    def test_theme_uses_optical_centering_and_semantic_states(self):
        theme = (ROOT / "references" / "04-reference-theme-prompt.md").read_text(
            encoding="utf-8"
        )

        for required in (
            "Close Evidence Portrait / 近景证据流",
            "距底部约 `55%`",
            "视觉重心",
            "亲近讲解态",
            "证据放大态",
            "全屏证明态",
            "删除倒计时",
            "双层柔影",
        ):
            self.assertIn(required, theme)

        self.assertIn("`36 px`", theme)
        self.assertIn("`18 px`", theme)

    def test_theme_remains_prompt_guidance_not_a_validator_mode(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        validator = (ROOT / "scripts" / "validate_plan.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("Close Evidence Portrait", skill)
        self.assertIn("近景证据流", skill)
        self.assertNotIn("close_evidence_portrait", validator)


if __name__ == "__main__":
    unittest.main()
