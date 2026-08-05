import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class PromptFirstContractTests(unittest.TestCase):
    def test_skill_does_not_bundle_a_heavy_remotion_template(self):
        self.assertFalse(
            (SKILL_ROOT / "assets" / "remotion-direct").exists(),
            "MotionTalk should prompt the agent to create project-specific Remotion code",
        )

    def test_theme_choices_are_prompt_guidance_not_code_modes(self):
        validator = (SKILL_ROOT / "scripts" / "validate_plan.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (
            "allowed_themes",
            "mg-with-presenter-window",
            "floating-overlay-on-presenter",
        ):
            self.assertNotIn(forbidden, validator)

        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("prompt-first", skill)
        self.assertIn("不是代码枚举", skill)

    def test_render_spec_and_packaging_are_project_data(self):
        scripts = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SKILL_ROOT / "scripts").glob("*")
            if path.is_file() and path.suffix in {".py", ".mjs"}
        )
        for forbidden in (
            "1920",
            "1080",
            "height_px",
            "label_font_size_px",
            "sample-classic-v1",
        ):
            self.assertNotIn(forbidden, scripts)

        build = (SKILL_ROOT / "references" / "02-build.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("由批准版导演计划决定", build)
        self.assertNotIn("60px", build)
        self.assertNotIn("30px", build)

    def test_fixed_entrypoints_remain_small_and_generic(self):
        renderer = SKILL_ROOT / "scripts" / "render_master.mjs"
        validator = SKILL_ROOT / "scripts" / "validate_master.mjs"
        self.assertTrue(renderer.exists())
        self.assertTrue(validator.exists())
        self.assertLess(len(renderer.read_text(encoding="utf-8").splitlines()), 180)
        self.assertLess(len(validator.read_text(encoding="utf-8").splitlines()), 220)


if __name__ == "__main__":
    unittest.main()
