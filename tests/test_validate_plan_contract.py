import importlib.util
from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "validate_plan.py"
spec = importlib.util.spec_from_file_location("validate_plan", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def valid_plan() -> dict:
    return {
        "status": "approved",
        "approved": True,
        "mg_theme": "mg-with-presenter-window",
        "source": {
            "video": "/data/edited.mp4",
            "subtitles": "/data/final.srt",
            "width": 1920,
            "height": 1080,
            "fps": 60,
            "duration_seconds": 2,
        },
        "cues": [
            {
                "id": "presenter-01",
                "start_seconds": 0,
                "end_seconds": 1,
                "visual": "presenter-full-screen",
            },
            {
                "id": "mg-01",
                "start_seconds": 1,
                "end_seconds": 2,
                "visual": "full-screen-mg",
                "spec": {
                    "semantic_invariants": [
                        {
                            "id": "meaning-01",
                            "assertion": "The diagram shows the stated relationship.",
                            "proof_moment": 1.5,
                            "forbidden": [],
                        }
                    ]
                },
            },
        ],
        "chapters": [
            {
                "id": "chapter-01",
                "start_seconds": 0,
                "end_seconds": 2,
                "title": "Opening",
            }
        ],
        "caption_highlights": {
            "enabled": True,
            "cues": {"1": ["important"]},
        },
        "package_style": {
            "profile": "sample-classic-v1",
            "chapter_header": {"enabled": True},
            "progress": {
                "enabled": True,
                "height_px": 30,
                "mode": "continuous-cumulative",
                "segment_by_chapter_duration": True,
                "show_labels": True,
                "label_layer": "ass-only",
            },
            "captions": {"enabled": True, "single_layer": True},
        },
    }


class ValidatePlanContractTests(unittest.TestCase):
    def test_valid_default_theme_plan_passes(self):
        self.assertEqual(validator.validate(valid_plan()), [])

    def test_disabled_caption_highlights_do_not_require_cues(self):
        plan = valid_plan()
        plan["caption_highlights"] = {"enabled": False}
        self.assertEqual(validator.validate(plan), [])

    def test_theme_and_source_format_are_required(self):
        plan = valid_plan()
        plan.pop("mg_theme")
        plan["source"]["fps"] = 30
        errors = validator.validate(plan)
        self.assertTrue(any("mg_theme" in error for error in errors))
        self.assertIn("source must be 1920x1080 at 60fps", errors)

    def test_cues_must_cover_source_on_frame_grid(self):
        plan = valid_plan()
        plan["cues"][0]["end_seconds"] = 0.999
        plan["cues"][1]["start_seconds"] = 0.999
        plan["cues"][1]["end_seconds"] = 1.5
        errors = validator.validate(plan)
        self.assertTrue(any("60fps frame grid" in error for error in errors))
        self.assertIn("cue timeline must end at source.duration_seconds", errors)

    def test_floating_overlay_requires_keyed_visual_and_policy(self):
        plan = valid_plan()
        plan["mg_theme"] = "floating-overlay"
        errors = validator.validate(plan)
        self.assertTrue(
            any("floating-overlay MG cues must use" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
