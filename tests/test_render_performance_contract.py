import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class RenderPerformanceContractTests(unittest.TestCase):
    def setUp(self):
        self.renderer = (SKILL_ROOT / "scripts" / "render_master.mjs").read_text(
            encoding="utf-8"
        )

    def test_renderer_does_not_force_single_threaded_frame_generation(self):
        self.assertNotIn("concurrency: 1", self.renderer)
        self.assertNotIn("offthreadVideoThreads: 1", self.renderer)
        self.assertNotIn("disallowParallelEncoding: true", self.renderer)
        self.assertIn('DEFAULT_CONCURRENCY = "75%"', self.renderer)
        self.assertIn("concurrency: renderOptions.concurrency", self.renderer)

    def test_renderer_defaults_to_portable_hardware_fallback(self):
        self.assertIn(
            'DEFAULT_HARDWARE_ACCELERATION = "if-possible"', self.renderer
        )
        self.assertNotIn(
            'DEFAULT_HARDWARE_ACCELERATION = "required"', self.renderer
        )
        self.assertIn("--hardware-acceleration MODE", self.renderer)
        self.assertIn("--video-bitrate RATE", self.renderer)

    def test_renderer_uses_project_local_remotion_managed_browser(self):
        self.assertIn("createRequire(path.join(projectDir, \"package.json\"))", self.renderer)
        self.assertNotIn("--browser-executable", self.renderer)
        self.assertNotIn("browserExecutable", self.renderer)

        docs = "\n".join(
            (SKILL_ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "README.md",
                "README_EN.md",
                "references/03-deliver.md",
            )
        )
        self.assertIn("Remotion 自管", docs)
        self.assertIn("Remotion-managed", docs)
        self.assertIn("不要传入系统 Chrome", docs)

    def test_videotoolbox_is_optional_readme_guidance_only(self):
        readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (SKILL_ROOT / "README_EN.md").read_text(encoding="utf-8")
        operational_docs = "\n".join(
            (SKILL_ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "SKILL.md",
                "references/01-plan.md",
                "references/02-build.md",
                "references/03-deliver.md",
            )
        )

        self.assertIn("macOS 性能建议", readme)
        self.assertIn("h264_videotoolbox", readme)
        self.assertIn("macOS performance recommendation", readme_en)
        self.assertIn("h264_videotoolbox", readme_en)
        self.assertNotIn("VideoToolbox", operational_docs)
        self.assertNotIn("h264_videotoolbox", operational_docs)


if __name__ == "__main__":
    unittest.main()
