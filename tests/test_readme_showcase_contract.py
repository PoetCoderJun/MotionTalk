import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME_ASSETS = (
    "assets/readme/theme-floating-overlay.webp",
    "assets/readme/theme-presenter-window.webp",
    "assets/readme/theme-switching.webp",
    "assets/readme/theme-ppt-focus-portrait.webp",
)
FLOW_ASSETS = {
    "zh": "assets/readme/motiontalk-flow-zh.png",
    "en": "assets/readme/motiontalk-flow-en.png",
}


class ReadmeShowcaseContractTests(unittest.TestCase):
    def test_bilingual_readmes_show_four_themes_before_capabilities(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README_EN.md").read_text(encoding="utf-8")

        self.assertLess(zh.index("## 参考主题"), zh.index("## 核心能力"))
        self.assertLess(en.index("## Reference themes"), en.index("## Core capabilities"))

        for name in (
            "floating-overlay",
            "mg-with-presenter-window",
            "switching",
            "PPT Focus Portrait",
        ):
            self.assertIn(name, zh)
            self.assertIn(name, en)

        for asset in THEME_ASSETS:
            self.assertIn(asset, zh)
            self.assertIn(asset, en)

        self.assertIn("references/04-reference-theme-prompt.md", zh)
        self.assertIn("references/04-reference-theme-prompt.md", en)
        self.assertNotIn("references/05-mg-themes.md", zh)
        self.assertNotIn("references/04-theme-ppt-focus-portrait.md", zh)

    def test_readmes_do_not_include_removed_performance_sections(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README_EN.md").read_text(encoding="utf-8")

        for removed in ("## 渲染性能", "### macOS 性能建议（可选）"):
            self.assertNotIn(removed, zh)
        for removed in ("## Render performance", "### macOS performance recommendation"):
            self.assertNotIn(removed, en)

    def test_prompt_first_is_explained_as_a_low_barrier_conversation(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README_EN.md").read_text(encoding="utf-8")

        self.assertIn("## 和 AI 说几句话就行", zh)
        self.assertIn("Codex / Kimi / Claude Code", zh)
        self.assertIn("给 AI 视频和字幕，说几句想要的效果", zh)
        self.assertIn("AI 给出导演方案", zh)
        self.assertIn("最终成片", zh)
        self.assertIn("调整（可选）", zh)
        self.assertIn(FLOW_ASSETS["zh"], zh)
        self.assertIn(
            "人物、全屏 MG 与其它视频b-roll素材按内容在你觉得合适的时候切换或者交错",
            zh,
        )
        self.assertNotIn("字幕最多两行；整体简洁一点。先给我看导演方案。", zh)
        self.assertLess(zh.index("## 和 AI 说几句话就行"), zh.index("## 参考主题"))
        self.assertLess(zh.index("## 和 AI 说几句话就行"), zh.index("## 核心能力"))

        self.assertIn("## Just tell the Agent what you want", en)
        self.assertIn("Codex / Kimi / Claude Code", en)
        self.assertIn("Optional adjustments", en)
        self.assertIn(FLOW_ASSETS["en"], en)
        self.assertIn("presenter, full-screen MG, and other video B-roll", en)
        self.assertNotIn("Show me the director plan first.", en)
        self.assertNotIn("```mermaid", zh)
        self.assertNotIn("```mermaid", en)
        self.assertNotIn("## Prompt-first", zh)
        self.assertNotIn("## Prompt-first", en)
        for technical in (
            "## 确定性薄层",
            "Headless Shell",
            "MasterComposition",
            "`75%`",
        ):
            self.assertNotIn(technical, zh)
        for technical in (
            "## Deterministic thin layer",
            "semantic invariants",
            "Headless Shell",
            "MasterComposition",
            "`75%`",
        ):
            self.assertNotIn(technical, en)

    def test_showcase_assets_exist_and_stay_lightweight(self):
        for relative_path in (*THEME_ASSETS, *FLOW_ASSETS.values()):
            asset = ROOT / relative_path
            self.assertTrue(asset.is_file(), relative_path)
            self.assertLess(asset.stat().st_size, 350_000, relative_path)


if __name__ == "__main__":
    unittest.main()
