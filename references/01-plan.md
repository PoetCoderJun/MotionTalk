# 规划并冻结导演 Prompt

本阶段只写导演脚本和机器计划，不创建 Remotion 工程。

## 检查输入

1. 记录视频、SRT、输出目录和视频元数据。
2. 校验 SRT 顺序、重叠、末尾时间和开头/中段/结尾的音画匹配。
3. 完整阅读字幕并检查用户提供的样例、录屏、截图和视觉要求。
4. 输入仍需重剪、字幕不匹配或素材不可解码时停止。

## 生成草案

从内容出发写完整时间线，而不是套用固定主题：

- 每个 cue 写 `visual_prompt`，说明人物、MG、录屏、截图和转场如何共同表达
  这一段；
- 每个 cue 写 `semantic_invariants`，包含稳定 ID、可判真假的 assertion、
  proof moment 和 forbidden；
- 把人物安全区、关键 UI、裁切边界和遮挡风险写进 Prompt；
- 根据发布平台和源素材提出 `render_spec`；根据用户要求或样例提出
  `package_direction`；
- 章节、进度、字幕、字体、花字和动画均是导演决策，不使用 Skill 固定数值。

用户点名参考主题或要求快速生成相似效果时，读取
[04-reference-theme-prompt.md](04-reference-theme-prompt.md)，把相关视觉关系、比例
和风险吸收到本项目 Prompt。用户直接用自然语言描述效果时，按描述设计，不要求
先选择主题。不要复制参考文案，也不要把主题注册为验证器枚举。

## 产物

写入：

- `MG导演脚本.md`：人读版本，包含完整时间线、视觉方向、包装方向、语义验收点
  和待批准假设；
- `mg-placement-plan.v1.json`：机器版本，至少包含 `status`、`approved`、
  `source`、`render_spec`、`visual_direction`、`package_direction` 和完整
  `cues`。

草案状态写 `draft`。用户明确批准后才改为 `approved`；随后停止本阶段。
