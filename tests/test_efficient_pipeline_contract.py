from pathlib import Path
import subprocess
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class EfficientPipelineContractTests(unittest.TestCase):
    def test_skill_keeps_single_video_base_contract(self):
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
            "双视频",
            "screen_windows",
        )
        for relative in checked:
            text = (SKILL_ROOT / relative).read_text(encoding="utf-8").lower()
            for token in forbidden:
                self.assertNotIn(token.lower(), text, f"{relative}: {token}")

    def test_optional_screen_recording_is_scoped_to_switching_theme(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        themes = (SKILL_ROOT / "references" / "05-mg-themes.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("精剪口播视频", skill)
        self.assertIn("最终 SRT", skill)
        self.assertIn("switching", themes)
        self.assertIn("录屏", themes)
        self.assertIn("未明确时默认 **B**", themes)

    def test_bundled_pipeline_scripts_exist_and_have_help(self):
        scripts = (
            "build_and_package.py",
            "quality_gate.py",
            "render_segments.mjs",
            "render_package_overlays.mjs",
            "validate_plan.py",
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
            "-filter_complex_threads",
            "-c:a",
            "copy",
            "package-overlays",
            "package-overlays-cropped",
            "progress-track.png",
            "package-pills.ffconcat",
            "package-pills-qtrle.mov",
            '"qtrle"',
        )
        for token in required:
            self.assertIn(token, text)
        self.assertNotIn("package-chapters", text)

    def test_build_script_supports_full_presenter_keyed_overlay(self):
        text = (SKILL_ROOT / "scripts" / "build_and_package.py").read_text(
            encoding="utf-8"
        )
        required = (
            "transparent-floating-overlay-on-presenter",
            "key_color",
            "key_similarity",
            "key_blend",
            "colorkey=",
            "despill=",
            "[base][mg]overlay=0:0",
            "needs_legacy_circle",
        )
        for token in required:
            self.assertIn(token, text)

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
        self.assertIn("latest_extractable_time", gate)
        self.assertIn("package_contract_ok", gate)
        self.assertIn('"progress_height_px"', gate)
        self.assertIn('show_progress_labels = bool(progress_style.get("show_labels", True))', build)
        self.assertIn("progress.height_px must be at least 24", build)
        self.assertIn("progress.label_layer must be ass-only", build)
        self.assertIn("[base][track]overlay=", build)
        self.assertIn("[withtrack][progress]overlay=", build)

    def test_package_overlay_renderer_selects_each_chapter(self):
        text = (SKILL_ROOT / "scripts" / "render_package_overlays.mjs").read_text(
            encoding="utf-8"
        )
        self.assertIn("inputProps.topics.entries()", text)
        self.assertIn("const chapterProps = {...inputProps, chapterIndex}", text)
        self.assertIn("inputProps: chapterProps", text)

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
        self.assertIn("04-package-contract.md", (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertTrue((SKILL_ROOT / "assets" / "remotion" / "Package.tsx").is_file())


if __name__ == "__main__":
    unittest.main()
