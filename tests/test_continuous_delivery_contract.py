from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class ContinuousDeliveryContractTests(unittest.TestCase):
    def test_approved_plan_runs_build_and_delivery_without_another_confirmation(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        build = (SKILL_ROOT / "references" / "02-build.md").read_text(encoding="utf-8")
        deliver = (SKILL_ROOT / "references" / "03-deliver.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("批准后连续制作与交付", skill)
        self.assertIn("02-build.md", skill)
        self.assertIn("03-deliver.md", skill)
        self.assertNotIn("一次调用只推进当前阶段", skill)
        self.assertNotIn("正式 MG 片段已完成，且画面与语义抽帧检查全部通过", skill)

        self.assertIn("立即读取并执行", build)
        self.assertIn("03-deliver.md", build)
        self.assertIn("不得停下或再次等待用户确认", build)
        self.assertNotIn("结束阶段 2", build)

        self.assertIn("同一次调用", deliver)
        self.assertIn("不得再次请求确认", deliver)

    def test_route_has_only_plan_and_continuous_delivery_states(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        route = skill.split("## 阶段路由", 1)[1].split("## 不可跨越的边界", 1)[0]
        numbered_routes = re.findall(r"(?m)^\d+\. ", route)
        self.assertEqual(numbered_routes, ["1. ", "2. "])


if __name__ == "__main__":
    unittest.main()
