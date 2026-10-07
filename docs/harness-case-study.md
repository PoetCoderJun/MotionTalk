# MotionTalk：一个可审查的 Agent Harness 案例

[English](harness-case-study.en.md) · [返回项目](../README.md)

问题是：Agent 可以生成视觉方案和渲染代码，但“渲染成功”不能说明它表达了正确内容。MotionTalk 把开放式导演判断放在 Agent，把能机械检查的约束放在薄脚本里。

## 从意图到证据

| 阶段 | 留下什么 | 公开实现 |
| --- | --- | --- |
| 规划 | 人读脚本、机器计划、逐 cue 的视觉意图和验收断言 | [规划规则](../references/01-plan.md) |
| 批准 | `status=approved` 与 `approved=true`；变更后重新规划 | [阶段路由](../SKILL.md) |
| 结构检查 | 正数 render spec、帧网格、从 0 到源时长的连续 cue、非空 Prompt 与断言 | [validate_plan.py](../scripts/validate_plan.py) |
| 制作与看帧 | 当前项目唯一 composition；同一渲染入口输出成片与证据帧；Agent 写语义/视觉/包装清单 | [制作规则](../references/02-build.md)、[render_master.mjs](../scripts/render_master.mjs) |
| 交付门禁 | 成片元数据、每个断言的证据路径与时间、清单 passed 状态、最终目录只含一个 MP4 | [validate_master.mjs](../scripts/validate_master.mjs)、[交付规则](../references/03-deliver.md) |

这里的 Harness 是计划、状态、工具入口、证据与验收契约的组合。它没有把所有视觉创作变成固定参数，也没有把参考主题变成代码枚举。

## 哪些检查真正是确定性的

`validate_plan.py` 拒绝未批准计划、空视觉 Prompt、缺失断言、非帧网格时间点和 cue 缺口/重叠。它不检查源文件是否存在或可解码，也不验证实际 SRT 匹配；这些属于规划输入检查。审批字段不验证用户身份、签名或批准版本，输入也未绑定哈希。

`validate_master.mjs` 检查成片与计划/props 的尺寸、帧率、时长是否一致（时长容差三帧），codec 是否已知、音频是否存在。对于数值 proof moment，它要求记录的证据时间在一帧容差内，同时要求每条清单记录 passed 且证据文件存在。最终目录必须只有指定 MP4。

这些是记录和文件检查：验证器不读证据图片来重新判断断言，不检查图片内容与所报时间是否相符，不证明音频内容来源，也不自动调用计划验证器。因此应先运行计划检查，再制作、看帧、生成清单，最后验收。检查报告是审查线索，不是视觉正确性的数学证明。

## 可复现的最小证据

从仓库根目录运行：

```bash
python3 examples/plan-validation/run.py
python3 -m unittest discover -s tests -v
node scripts/render_master.mjs --help
node scripts/validate_master.mjs --help
```

[合成样例](../examples/plan-validation/README.md)只检查计划契约，不读取媒体、不调用模型、不下载依赖。现有测试覆盖审批、时间线、Prompt 与渲染接口等契约；它们不等于完整生产渲染或视觉质量评估。README 的四个图像是已有视觉证据，仓库没有随附对应的完整源视频与渲染工程。

## 可以迁移的工程思路

在 Work 中，可把“总结正确”拆成输入来源、断言证据与可编辑交付。在 Robotics 或 Finance 中，规划、审批与证据的分层值得探索，但还需要各自的安全约束、环境反馈与领域评估。这个媒体案例没有验证机器人部署、金融系统表现或企业 ROI。

使用与改编遵循 [CC BY-NC-SA 4.0](../LICENSE.md)；商业使用需事先获得书面许可，第三方材料保留各自权利。
