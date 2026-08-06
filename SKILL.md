---
name: motiontalk
description: Use when an already-cut talking video and its final matching SRT need content-aware MG, presenter composition, screen-recording integration, subtitles, or final visual packaging.
---

# MotionTalk

MotionTalk 是一个 **prompt-first** 的口播视频后期工作流。它不做 ASR、不删
口误、不重新剪辑；精剪视频及其最终 SRT 是时间线、语义和主音频的唯一依据。

## 输入

- `video`：保留最终主音频的精剪视频；
- `subtitles`：与视频时间线完全匹配的最终 SRT；
- `output_dir`：独立输出目录。

从视频文件名推导 `project_id`，不要再询问项目名。

## 阶段路由

流程只有“规划”和“批准后连续制作与交付”两个状态：

1. 没有批准版导演计划：读取并执行
   [references/01-plan.md](references/01-plan.md)。
2. `MG导演脚本.md` 与 `mg-placement-plan.v1.json` 已批准：读取并执行
   [references/02-build.md](references/02-build.md)，证据帧通过后在同一次调用
   立即执行 [references/03-deliver.md](references/03-deliver.md)。

导演计划批准是全流程唯一一次用户确认。用户说“你自行判断”只授权生成草案，
不等于批准。批准后若输入、时间线、文案或已冻结的视觉方向变化，退回规划阶段。

## Prompt 驱动边界

- 用户点名 `floating-overlay`、`mg-with-presenter-window`、`switching`、
  `PPT Focus Portrait`，或要求快速生成相似效果时，读取
  [references/04-reference-theme-prompt.md](references/04-reference-theme-prompt.md)。
  这是独立的参考 Prompt，只用于帮助快速理解相似效果，**不是代码枚举或必选项**。
- 用户没有选主题时，直接根据自然语言、素材和样例设计；不得要求四选一。自然语言
  要求与参考主题冲突时，以用户当前要求为准。
- 分辨率、帧率、字幕样式、章节、进度、字体比例、位置、动画和安全区全部由
  当次素材、平台、样例及用户要求决定，并写入批准版计划。
- Skill 不携带 Remotion 工程模板。批准后在 `output_dir/remotion/` 创建只服务
  当前计划的最小项目；不得把项目视觉差异反向膨胀成 Skill 参数体系。
- 主题参考保存构图意图、比例关系与验收规则，**不是代码模式**；仍需按当次
  画布、字幕、人物和录屏/PPT 素材重算布局。
- 同一项目只保留一个 `MasterComposition`。底片、唯一主音频、字幕、MG 和
  包装在同一 Remotion 时间线中渲染；文字直接使用 DOM/SVG。
- 使用相对布局、画布尺寸或计划传入的数据计算几何；禁止把某个项目的尺寸、
  进度条高度或人物位置写成 Skill 的全局常量。

## 固定入口

代码只承担需要确定性的薄层：

- `validate_plan.py`：验证批准状态、项目 render spec、完整 cue 时间线、视觉
  Prompt 和语义验收点；
- `render_master.mjs`：以跨平台可回退的默认配置调用 Remotion 官方入口完成
  正式渲染和抽帧，从项目 `package.json` 加载 Remotion 并使用其自管浏览器，
  同时允许按当前机器显式覆盖并发、硬件策略和码率；
- `validate_master.mjs`：按项目 render spec、批准的语义清单和证据帧验收成片。

不要为单个项目修改这些入口。视觉实现写在该项目的 Remotion 工程中。

## 不可跨越的边界

- 没有最终 SRT、输入不可解码或仍需重剪时停止。
- 所有产物只写入 `output_dir`，不修改输入视频或 SRT。
- 不生成低清整片或 `*-preview.mp4`；使用正式 composition 的 `renderStill`
  证据帧判断画面。
- 每个 cue 都必须有 `visual_prompt` 和可由证据帧判断的
  `semantic_invariants`。
- 人像、录屏和素材必须保持原始宽高比；不得拉伸。
- 主音频只来自输入 `video`；最终目录只交付一个包装成片。
- `quality-report.v1.json` 所有必检项通过后才能宣称完成。
