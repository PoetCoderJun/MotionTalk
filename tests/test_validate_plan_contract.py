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
        "source": {
            "video": "/data/edited.mp4",
            "subtitles": "/data/final.srt",
            "width": 1280,
            "height": 720,
            "fps": 30,
            "duration_seconds": 2,
        },
        "render_spec": {
            "width": 1080,
            "height": 1920,
            "fps": 30,
        },
        "visual_direction": (
            "Keep the presenter full-screen and place only necessary MG in measured "
            "safe zones. This is project direction, not a named code mode."
        ),
        "package_direction": (
            "Render one caption layer and the chapter/progress treatment approved "
            "in the director plan."
        ),
        "cues": [
            {
                "id": "opening",
                "start_seconds": 0,
                "end_seconds": 1,
                "visual_prompt": "Keep the presenter full-screen.",
                "spec": {
                    "semantic_invariants": [
                        {
                            "id": "opening-meaning",
                            "assertion": "The presenter remains visible.",
                            "proof_moment": 0.5,
                            "forbidden": ["replace the presenter"],
                        }
                    ]
                },
            },
            {
                "id": "explanation",
                "start_seconds": 1,
                "end_seconds": 2,
                "visual_prompt": "Use a relationship diagram beside the presenter.",
                "spec": {
                    "semantic_invariants": [
                        {
                            "id": "relationship",
                            "assertion": "The diagram shows the stated relationship.",
                            "proof_moment": 1.5,
                            "forbidden": [],
                        }
                    ]
                },
            },
        ],
    }


class ValidatePlanContractTests(unittest.TestCase):
    def test_arbitrary_render_spec_and_visual_prompt_pass(self):
        self.assertEqual(validator.validate(valid_plan()), [])

    def test_visual_direction_is_freeform_not_a_theme_enum(self):
        plan = valid_plan()
        plan["visual_direction"] = (
            "Switch among presenter, full-screen diagrams, and a screen recording "
            "when the narration calls for it."
        )
        self.assertEqual(validator.validate(plan), [])

    def test_source_and_render_spec_are_positive_project_data(self):
        plan = valid_plan()
        plan["render_spec"]["width"] = 0
        plan["source"]["fps"] = -1
        errors = validator.validate(plan)
        self.assertTrue(any("render_spec.width" in error for error in errors))
        self.assertTrue(any("source.fps" in error for error in errors))

    def test_cues_use_the_approved_render_fps_grid(self):
        plan = valid_plan()
        plan["cues"][0]["end_seconds"] = 0.999
        plan["cues"][1]["start_seconds"] = 0.999
        errors = validator.validate(plan)
        self.assertTrue(any("render fps frame grid" in error for error in errors))

    def test_each_cue_requires_a_visual_prompt_and_semantic_evidence(self):
        plan = valid_plan()
        plan["cues"][1].pop("visual_prompt")
        plan["cues"][0]["spec"]["semantic_invariants"] = []
        errors = validator.validate(plan)
        self.assertTrue(any("visual_prompt" in error for error in errors))
        self.assertTrue(any("semantic_invariants" in error for error in errors))

    def test_plan_must_be_explicitly_approved(self):
        plan = valid_plan()
        plan["status"] = "draft"
        self.assertIn("plan must be explicitly approved", validator.validate(plan))


if __name__ == "__main__":
    unittest.main()
