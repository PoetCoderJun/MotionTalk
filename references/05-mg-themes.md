# 画面构成主题（mg_theme）

MG 主题指**人像与 MG 的画面构成方式**，与包装层（章节牌、进度条、字幕）无关。阶段 1 规划时与用户选定一个主题，写入导演脚本和 `mg-placement-plan.v1.json` 顶层 `mg_theme`，随导演脚本一起批准；批准后不得跨主题混排。

## 主题 A：floating-overlay（MG 悬浮在人物画面上）

人像始终全屏常驻，MG 以悬浮元素直接叠加在人物画面之上做效果：**不替换人物、不做蒙版、不开画中画窗口、不加全屏底色**。

- plan 写法：`mg_theme: "floating-overlay"`；`presenter_policy.default: "full-screen-underlay"`；每个 MG cue 的 `visual` 为 `transparent-floating-overlay-on-presenter`；配 `overlay_style`（key_color 等抠绿参数）。
- 阶段 1 先抽多帧实测人脸安全区，在 `presenter_policy.mg_allowed_zones` 声明 MG 可用区域（顶部横带 / 左右侧翼），人脸区绝对留空。
- MG 场景硬约束：整屏 `#00FF00` 背景；元素、文字、描边、阴影禁用绿色系；禁用半透明填充与模糊投影（会被 colorkey 抠穿），阴影用不透明偏移块。
- 合成走 `build_and_package.py` 的抠绿覆盖分支，不创建人像圆窗。

## 主题 B：mg-with-presenter-window（全屏 MG + 人像蒙版窗）

MG 全屏替换底画，人像以圆窗/方窗常驻右下角（本 Skill 的原始默认）。

- 每个 MG cue 的 `visual` 为全屏 MG 类取值（如 `full-screen-mg`），人像窗口参数写入 `presenter_policy`（circle_diameter_px 等）。
- 任何人像底在 `scale` 前必须先裁成目标宽高比或用 `force_original_aspect_ratio`；抽帧并排检查变换前后人脸比例。

## 主题 C：switching（人像 ↔ MG ↔ 录屏切换）

在人物口播、全屏 MG、录屏画面之间硬切切换，各段独占全屏（适合带课程录屏的项目）。

- 录屏类 cue 使用独立的 `visual` 取值并在 `source` 中登记录屏文件；切换边界与字幕逐段对齐。

## 选择原则

用户只说“MG 直接悬浮在人物画面上，不替换人物、不做蒙版”时，选 **A**；给出含录屏的课件类输入时考虑 **C**；未明确时默认 **B**。主题只决定画面构成，MG 内部的色板、字体、动效仍按 cue 语义设计。
