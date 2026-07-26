---
name: motiontalk
description: Use when an already-cut talking video and its final matching SRT need MG animation or smooth switching among presenter, synchronized screen recording, and MG.
---

# MotionTalk

这是精剪完成后的口播视频 MG 后期工作流。它不做 ASR、不生成 SRT、不删口误或停顿，也不重新剪辑。最终 SRT 必须与精剪视频时间线完全匹配。

## 必填输入

- `video`：保留最终主音频的精剪口播视频；
- `subtitles`：与 `video` 匹配的最终 SRT；
- `output_dir`：独立输出目录；
- 可选 `screen_video`：从 `00:00` 与口播同步且等长的录屏。

从 `video` 文件名推导小写连字符格式的 `project_id`，不要再向用户索取项目名。口播视频是时间线、语义和最终音频的唯一依据；录屏音频只用于同步抽查，交付时必须丢弃。

## 阶段路由

先检查 `output_dir` 中的状态。流程只有“规划”和“批准后连续制作与交付”两个状态：

1. 没有已批准的导演脚本：读 [references/01-plan.md](references/01-plan.md)。
2. `MG导演脚本.md` 和 `mg-placement-plan.v1.json` 已批准、每个 MG cue 都有已批准的 `semantic_invariants`：先读并执行 [references/02-build.md](references/02-build.md)；正式片段门禁通过后，在**同一次调用**里立即读并执行 [references/03-deliver.md](references/03-deliver.md)，直到正式包装成片通过最终质量门禁并交付。

唯一需要用户确认的边界是阶段 1 导演脚本批准。批准后不得在正式片段完成、语义抽帧通过或整片合成前停下，不得再次请求“继续制作”“继续交付”或同义确认。质量门禁失败时在同一次调用中修复受影响环节并重验；只有真实外部阻塞或需要改变已批准时间线、文案、布局、遮挡策略时才停止。

状态必须写入人读导演脚本和机器读 placement plan。用户说“你自行判断”只授权生成草案，不等于批准。批准后若输入时间线、文案、时长、布局或遮挡策略变化，退回阶段 1 重新映射。
旧 placement plan 即使状态为 `approved`，只要任一 MG cue 缺少 `semantic_invariants`，也必须退回阶段 1 补齐并重新批准。

## 固定执行入口

批准后优先直接调用本 Skill 的 `scripts/`，不要为每个项目重写批量渲染、合成包装或质量门禁脚本：

- `render_segments.mjs`：一次 bundle、一次 browser，顺序渲染全部正式 MG；
- `render_package_overlays.mjs`：一次 bundle、一次 browser，渲染章节透明静帧；
- `build_and_package.py`：互斥 cue 合成后执行单次整片包装；
- `quality_gate.py`：完整解码、音频同源、证据帧、清洁度等最终门禁。

只有批准版 plan 的输入规格或视觉结构超出脚本支持范围时才修改脚本；先把新增能力做成通用参数并补契约测试，禁止只在单个项目里复制一份私有实现。

## 最后的可选节奏优化

正式包装前做一次“用户此刻是否会因啰嗦、重复或停留过久而划走”的节奏检查。默认可用 `build_and_package.py --speed 1.15` 对整片统一提速；脚本会同步重映射视频、口播音频、字幕、章节牌和进度条，输出仍固定为 60fps，并把提速融入唯一一次整片包装编码。

只有少数明确拖沓窗口需要不同速度时，才在 placement plan 增加已批准的速度区间并同步重映射所有时间依赖产物；不得只加速画面或只加速音频，也不得在已经交付后无理由再编码一遍整片。节奏优化是可选项，不得改变原话、删减信息或让语速影响理解。

## 不可跨越的边界

- 没有最终 SRT、输入不可解码、录屏持续漂移或仍需重剪时停止。
- 所有中间产物只写入 `output_dir`；不修改输入视频、SRT 或录屏。
- 不生成单独的预览视频、低清整片或 `*-preview.mp4`。需要判断画面时直接检查正式 MG 片段、正式包装成片和证据帧，不为验收重复编码同一内容。
- 抽帧验收既检查画面质量，也必须用证据帧逐条证明批准版语义约束；语义未通过不得进入整片合成。
- MG 与录屏窗口期间，人像默认常驻右下角；真实屏幕操作对全屏 MG 有否决权。
- 任何人像底、圆窗、方窗或录屏画中画在 `scale` 前都必须先裁成目标宽高比，或使用 `force_original_aspect_ratio`；禁止把非目标比例画面直接拉伸到固定宽高。抽帧验收必须把变换前后的人脸比例并排检查。
- 最终视频只交付包装成片，不交付或长期保留干净母版。若包装链路需要干净合成中间片，只能写入 `output_dir/work/`，包装版验收通过后删除；主音频始终只来自 `video`。
- 交付前必须完成连续制作与交付阶段的最终质量门禁并写出 `quality-report.v1.json`；任何必检项不是 `passed` 都不得宣称完成。
