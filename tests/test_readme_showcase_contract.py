import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_ASSETS = (
    "assets/readme/theme-floating-overlay.webp",
    "assets/readme/theme-presenter-window.webp",
    "assets/readme/theme-switching.webp",
    "assets/readme/theme-ppt-focus-portrait.webp",
)


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

        for asset in SHOWCASE_ASSETS:
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

    def test_showcase_assets_exist_and_stay_lightweight(self):
        for relative_path in SHOWCASE_ASSETS:
            asset = ROOT / relative_path
            self.assertTrue(asset.is_file(), relative_path)
            self.assertLess(asset.stat().st_size, 350_000, relative_path)


if __name__ == "__main__":
    unittest.main()
