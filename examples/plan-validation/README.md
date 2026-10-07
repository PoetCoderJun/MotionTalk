# 合成计划验证 / Synthetic plan validation

从仓库根目录运行 / Run from the repository root:

```bash
python3 examples/plan-validation/run.py
```

Expected output:

```text
PASS: synthetic approved plan
REJECT: unapproved draft
REJECT: timeline gap
```

这是新写的合成契约输入，不包含真实录音、客户数据或媒体。`plan.json` 的批准字段仅模拟测试状态，不能用作真实项目的用户批准。音频与字幕路径是不存在的占位符；验证器不检查文件存在，因此这个样例通过也不能用于成片交付。

This newly authored synthetic fixture contains no real recordings, customer data or media. Approval flags simulate a test state and must never substitute for user approval in a real project. Media paths are nonexistent placeholders: this validator does not check file existence, so passing this example does not qualify a video for delivery.

Requires only Python 3; no network, API keys, model calls, paid services or rendering dependencies. This demonstrates the plan validator only, not end-to-end production or a cost / performance benchmark.

[中文案例](../../docs/harness-case-study.md) · [English case study](../../docs/harness-case-study.en.md) · [License](../../LICENSE.md)
