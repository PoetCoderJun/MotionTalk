---
name: talking-mg-video
description: Use when an already-cut selfie talking-head or spoken video and its final matching SRT need MG animation or smooth switching among presenter, synchronized screen recording, and MG.
---

# Talking MG Video

这是精剪完成后的口播视频 MG 后期工作流。它不做 ASR、不生成 SRT、不删口误或停顿，也不重新剪辑。最终 SRT 必须与精剪视频时间线完全匹配。

## 必填输入

- `video`：保留最终主音频的精剪口播视频；
- `subtitles`：与 `video` 匹配的最终 SRT；
- `output_dir`：独立输出目录；
- 可选 `screen_video`：从 `00:00` 与口播同步且等长的录屏。

从 `video` 文件名推导小写连字符格式的 `project_id`，不要再向用户索取项目名。口播视频是时间线、语义和最终音频的唯一依据；录屏音频只用于同步抽查，交付时必须丢弃。

## 阶段路由

先检查 `output_dir` 中的状态，然后**只读并执行一个阶段文件**：

1. 没有已批准的导演脚本：读 [references/01-plan.md](references/01-plan.md)。
2. `MG导演脚本.md` 和 `mg-placement-plan.v1.json` 已批准、每个 MG cue 都有已批准的 `semantic_invariants`，但正式 MG 片段尚未完成并通过画面与语义抽帧检查：读 [references/02-build.md](references/02-build.md)。
3. 正式 MG 片段已完成，且画面与语义抽帧检查全部通过：读 [references/03-deliver.md](references/03-deliver.md)。

一次调用只推进当前阶段。到达阶段边界时停下；不得预读后续阶段来“准备一下”。这样可避免每次把完整制作与交付规范都放进上下文。

状态必须写入人读导演脚本和机器读 placement plan。用户说“你自行判断”只授权生成草案，不等于批准。批准后若输入时间线、文案、时长、布局或遮挡策略变化，退回阶段 1 重新映射。
旧 placement plan 即使状态为 `approved`，只要任一 MG cue 缺少 `semantic_invariants`，也必须退回阶段 1 补齐并重新批准。

## 不可跨越的边界

- 没有最终 SRT、输入不可解码、录屏持续漂移或仍需重剪时停止。
- 所有中间产物只写入 `output_dir`；不修改输入视频、SRT 或录屏。
- 抽帧验收既检查画面质量，也必须用证据帧逐条证明批准版语义约束；语义未通过不得进入整片合成。
- MG 与录屏窗口期间，人像默认常驻右下角；真实屏幕操作对全屏 MG 有否决权。
- 最终视频只交付包装成片，不交付或长期保留干净母版。若包装链路需要干净合成中间片，只能写入 `output_dir/work/`，包装版验收通过后删除；主音频始终只来自 `video`。
