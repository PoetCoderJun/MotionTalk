from pathlib import Path
import subprocess
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class EfficientPipelineContractTests(unittest.TestCase):
    def test_skill_supports_talking_video_and_mg_only(self):
        checked = (
            "README.md",
            "README_EN.md",
            "SKILL.md",
            "references/01-plan.md",
            "references/02-build.md",
            "references/03-deliver.md",
            "agents/openai.yaml",
        )
        forbidden = (
            "screen_video",
            "screen recording",
            "synchronized screen",
            "录屏",
            "双视频",
            "screen_windows",
        )
        for relative in checked:
            text = (SKILL_ROOT / relative).read_text(encoding="utf-8").lower()
            for token in forbidden:
                self.assertNotIn(token.lower(), text, f"{relative}: {token}")

    def test_bundled_pipeline_scripts_exist_and_have_help(self):
        scripts = (
            "build_and_package.py",
            "quality_gate.py",
            "render_segments.mjs",
            "render_package_overlays.mjs",
        )
        for name in scripts:
            path = SKILL_ROOT / "scripts" / name
            self.assertTrue(path.is_file(), name)
            runtime = "node" if path.suffix == ".mjs" else sys.executable
            result = subprocess.run(
                [runtime, str(path), "--help"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_build_script_encodes_once_with_stable_timestamps_and_color(self):
        text = (SKILL_ROOT / "scripts" / "build_and_package.py").read_text(
            encoding="utf-8"
        )
        required = (
            "-nostats",
            "h264_videotoolbox",
            "in_range=auto:out_range=tv",
            "setpts=N/(60*TB)",
            "-c:a",
            "copy",
            "package-overlays",
        )
        for token in required:
            self.assertIn(token, text)
        self.assertNotIn("package-chapters", text)

    def test_optional_pacing_pass_keeps_delivery_at_60fps(self):
        build = (SKILL_ROOT / "scripts" / "build_and_package.py").read_text(
            encoding="utf-8"
        )
        gate = (SKILL_ROOT / "scripts" / "quality_gate.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("--speed", build)
        self.assertIn("atempo", build)
        self.assertIn("FPS = 60", build)
        self.assertIn("setpts=N/(60*TB)", build)
        self.assertIn("Style: Progress", build)
        self.assertIn("short_label", build)
        self.assertIn("--speed", gate)
        self.assertNotIn('"-count_frames"', gate)
        self.assertNotIn("FPS = 120", build)

    def test_references_route_to_bundled_scripts(self):
        build = (SKILL_ROOT / "references" / "02-build.md").read_text(
            encoding="utf-8"
        )
        deliver = (SKILL_ROOT / "references" / "03-deliver.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("本 Skill 仓库不分发可执行代码", build)
        self.assertIn("scripts/render_package_overlays.mjs", deliver)
        self.assertIn("scripts/build_and_package.py", deliver)
        self.assertIn("scripts/quality_gate.py", deliver)
        self.assertIn("单次整片包装", deliver)
        self.assertNotIn("每章以同一 VideoToolbox 参数编码，concat demuxer", deliver)


if __name__ == "__main__":
    unittest.main()
