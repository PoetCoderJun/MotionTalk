#!/usr/bin/env python3
"""Contract tests for caption keyword emphasis in build_and_package.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("build_and_package.py")
spec = importlib.util.spec_from_file_location("build_and_package", MODULE_PATH)
bap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bap
spec.loader.exec_module(bap)


class AssColorTest(unittest.TestCase):
    def test_hex_to_bgr(self):
        self.assertEqual(bap.ass_bgr_color("#FFD166"), "66D1FF")
        self.assertEqual(bap.ass_bgr_color("ff6b35"), "356BFF")

    def test_rejects_invalid(self):
        with self.assertRaises(ValueError):
            bap.ass_bgr_color("red")
        with self.assertRaises(ValueError):
            bap.ass_bgr_color("#FFF")


class FontScaleTest(unittest.TestCase):
    def test_softened_and_clamped(self):
        self.assertEqual(bap.softened_font_scale(1.0), 1.0)
        self.assertAlmostEqual(bap.softened_font_scale(1.2), 1.17)
        self.assertEqual(bap.softened_font_scale(1.05), 1.16)
        self.assertEqual(bap.softened_font_scale(2.0), 1.3)


class EmphasisTest(unittest.TestCase):
    def emphasize(self, wrapped, keywords):
        return bap.apply_caption_emphasis(wrapped, keywords, 53, "#FFD166", 1.2)

    def test_no_keywords_passthrough(self):
        self.assertEqual(self.emphasize(" plain ", []), " plain ")

    def test_single_keyword_wrapped_with_tags(self):
        out = self.emphasize("AI 是怎么百分之百接管我的全部收入的", [{"text": "百分之百"}])
        self.assertIn(r"{\fs62\1c&H66D1FF&}百分之百{\r}", out)
        self.assertTrue(out.endswith("接管我的全部收入的"))

    def test_per_keyword_color_and_scale(self):
        out = self.emphasize(
            "每月投入超过三千块钱",
            [{"text": "三千块钱", "color": "#FF6B35", "scale": 1.3}],
        )
        self.assertIn(r"{\fs67\1c&H356BFF&}三千块钱{\r}", out)

    def test_string_keyword_shorthand_via_write_ass(self):
        entries = [(0.0, 2.0, "代码会变得越来越 cheap，真正有价值的部分是对业务的理解。")]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.ass"
            bap.write_ass(
                path,
                entries,
                [],
                137.35,
                1.15,
                show_progress_labels=False,
                caption_highlights={"enabled": True, "cues": {"1": ["cheap"]}},
            )
            content = path.read_text(encoding="utf-8")
        self.assertIn(r"{\fs62\1c&H66D1FF&}cheap{\r}", content)

    def test_keyword_split_across_lines(self):
        wrapped = r"结尾是百分\N之百接管"
        out = self.emphasize(wrapped, [{"text": "百分之百"}])
        self.assertIn(r"{\fs62\1c&H66D1FF&}百分{\r}", out)
        self.assertIn(r"{\fs62\1c&H66D1FF&}之百{\r}", out)

    def test_unmatched_keyword_ignored(self):
        out = self.emphasize("一些普通文本", [{"text": "不存在"}])
        self.assertEqual(out, "一些普通文本")

    def test_disabled_highlights_leave_text_untouched(self):
        entries = [(0.0, 2.0, "普通一句话。")]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.ass"
            bap.write_ass(
                path,
                entries,
                [],
                100.0,
                1.0,
                show_progress_labels=False,
                caption_highlights={"enabled": False, "cues": {"1": ["普通"]}},
            )
            content = path.read_text(encoding="utf-8")
        self.assertNotIn(r"\1c&H", content)
        self.assertIn("普通一句话。", content)


if __name__ == "__main__":
    unittest.main()
