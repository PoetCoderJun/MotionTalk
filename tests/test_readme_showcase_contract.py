import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_ASSETS = (
    "assets/readme/ppt-focus-opening.webp",
    "assets/readme/ppt-focus-subtitle.webp",
    "assets/readme/ppt-focus-ending.webp",
)


class ReadmeShowcaseContractTests(unittest.TestCase):
    def test_bilingual_readmes_lead_with_capabilities_and_real_sample_frames(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README_EN.md").read_text(encoding="utf-8")

        self.assertIn("## 核心能力", zh)
        self.assertIn("## 样片截图", zh)
        self.assertIn("## Core capabilities", en)
        self.assertIn("## Sample frames", en)

        for asset in SHOWCASE_ASSETS:
            self.assertIn(asset, zh)
            self.assertIn(asset, en)

    def test_showcase_assets_exist_and_stay_lightweight(self):
        for relative_path in SHOWCASE_ASSETS:
            asset = ROOT / relative_path
            self.assertTrue(asset.is_file(), relative_path)
            self.assertLess(asset.stat().st_size, 350_000, relative_path)


if __name__ == "__main__":
    unittest.main()
