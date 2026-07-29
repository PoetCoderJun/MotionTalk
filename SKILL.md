---
name: motiontalk
description: Use when an already-cut talking video and its final matching SRT need MG animation or smooth switching between the presenter and MG.
---

# MotionTalk

这是精剪完成后的口播视频 MG 后期工作流。它不做 ASR、不生成 SRT、不删口误或停顿，也不重新剪辑。最终 SRT 必须与精剪视频时间线完全匹配。

## 必填输入

- `video`：保留最终主音频的精剪口播视频；
- `subtitles`：与 `video` 匹配的最终 SRT；
- `output_dir`：独立输出目录。

从 `video` 文件名推导小写连字符格式的 `project_id`，不要再向用户索取项目名。口播视频是时间线、语义和最终音频的唯一依据。

## 阶段路由

先检查 `output_dir` 中的状态。流程只有“规划”和“批准后连续制作与交付”两个状态：

1. 没有已批准的导演脚本：读 [references/01-plan.md](references/01-plan.md)。
2. `MG导演脚本.md` 和 `mg-placement-plan.v1.json` 已批准、每个 MG cue 都有已批准的 `semantic_invariants`：先读并执行 [references/02-build.md](references/02-build.md)；正式片段门禁通过后，在**同一次调用**里立即读并执行 [references/03-deliver.md](references/03-deliver.md)，直到正式包装成片通过最终质量门禁并交付。

唯一需要用户确认的边界是阶段 1 导演脚本批准，这也是**全流程唯一的一次打断**。画面构成主题、字幕关键词强调、节奏判断、布局与遮挡策略等所有需要决策的点，都由 Agent 做成提议写进草案，随草案一次批准；不得为这些决策单独停下来询问。批准后不得在正式片段完成、语义抽帧通过或整片合成前停下，不得再次请求“继续制作”“继续交付”或同义确认。质量门禁失败时在同一次调用中修复受影响环节并重验；只有真实外部阻塞或需要改变已批准时间线、文案、布局、遮挡策略时才停止。

状态必须写入人读导演脚本和机器读 placement plan。用户说“你自行判断”只授权生成草案，不等于批准。批准后若输入时间线、文案、时长、布局或遮挡策略变化，退回阶段 1 重新映射。
旧 placement plan 即使状态为 `approved`，只要任一 MG cue 缺少 `semantic_invariants`，也必须退回阶段 1 补齐并重新批准。

## 包装与 MG 分层

把章节牌、累计进度条和字幕视为不可省略的“包装层”，把中段动画视为可变的“MG 层”。用户只要求更换 MG 风格时，不得顺手重设计、弱化或删除包装层。

- 默认复制 [assets/remotion/Package.tsx](assets/remotion/Package.tsx) 到项目 `remotion/src/Package.tsx`，并按 [references/04-package-contract.md](references/04-package-contract.md) 写入 `package_style`。
- 画面构成（人像与 MG 的关系）按 [references/05-mg-themes.md](references/05-mg-themes.md) 选定主题：MG 悬浮在人物画面上、全屏 MG + 人像蒙版窗、或人像 ↔ MG ↔ 录屏切换；主题写入批准版 plan 的 `mg_theme`，批准后不得跨主题混排。
- 样例视频存在时，先从正式样例成片抽取章节开头、中段、结尾帧；锁定它的章节牌、进度条、字幕和字体层级，只让 MG 场景变化。
- 默认包装必须同时包含：左上章节 pill、底部 30px 连续累计进度轨道、单套字幕。细到视觉上近似消失的进度线不是合格替代。
- MG 字体、色块、透明度和构图可以按内容变化；避免把“同一套半透明卡片”误当成统一风格。优先使用粗字重、清晰轮廓、实体色块和有语义的运动关系。

## 固定执行入口

批准后优先直接调用本 Skill 的 `scripts/`，不要为每个项目重写批量渲染、合成包装或质量门禁脚本：

- `render_segments.mjs`：一次 bundle、一次 browser，顺序渲染全部正式 MG；
- `validate_plan.py`：在渲染前验证批准状态、包装完整性和进度条最低可见规格；
- `render_package_overlays.mjs`：一次 bundle、一次 browser，渲染章节透明静帧；
- `build_and_package.py`：互斥 cue 合成后执行单次整片包装；
- `quality_gate.py`：完整解码、音频同源、证据帧、清洁度等最终门禁。

只有批准版 plan 的输入规格或视觉结构超出脚本支持范围时才修改脚本；先把新增能力做成通用参数并补契约测试，禁止只在单个项目里复制一份私有实现。

## 最后的可选节奏优化

正式包装前做一次“用户此刻是否会因啰嗦、重复或停留过久而划走”的节奏检查。默认可用 `build_and_package.py --speed 1.15` 对整片统一提速；脚本会同步重映射视频、口播音频、字幕、章节牌和进度条，输出仍固定为 60fps，并把提速融入唯一一次整片包装编码。

只有少数明确拖沓窗口需要不同速度时，才在 placement plan 增加已批准的速度区间并同步重映射所有时间依赖产物；不得只加速画面或只加速音频，也不得在已经交付后无理由再编码一遍整片。节奏优化是可选项，不得改变原话、删减信息或让语速影响理解。

## 不可跨越的边界

- 没有最终 SRT、输入不可解码或仍需重剪时停止。
- 所有中间产物只写入 `output_dir`；不修改输入视频或 SRT。
- 不生成单独的预览视频、低清整片或 `*-preview.mp4`。需要判断画面时直接检查正式 MG 片段、正式包装成片和证据帧，不为验收重复编码同一内容。
- 抽帧验收既检查画面质量，也必须用证据帧逐条证明批准版语义约束；语义未通过不得进入整片合成。
- MG 窗口期间，人像按批准版 `mg_theme` 常驻：`mg-with-presenter-window` 主题默认右下角圆窗/方窗；`floating-overlay` 主题人像全屏常驻，MG 只悬浮叠加，不做蒙版或替换。
- 任何人像底、圆窗或方窗在 `scale` 前都必须先裁成目标宽高比，或使用 `force_original_aspect_ratio`；禁止把非目标比例画面直接拉伸到固定宽高。抽帧验收必须把变换前后的人脸比例并排检查。
- 最终视频只交付包装成片，不交付或长期保留干净母版。若包装链路需要干净合成中间片，只能写入 `output_dir/work/`，包装版验收通过后删除；主音频始终只来自 `video`。
- 交付前必须完成连续制作与交付阶段的最终质量门禁并写出 `quality-report.v1.json`；任何必检项不是 `passed` 都不得宣称完成。
- 不得因为 FFmpeg 成功、源码中存在组件或质量报告字段为 `passed`，就推断章节牌和进度条肉眼可见；必须检查正式成片全尺寸证据帧。
