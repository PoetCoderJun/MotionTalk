# 批准后制作

前提：导演脚本和 placement plan 已批准。

## 建立项目

在 `output_dir/remotion/` 创建最小 Remotion 项目，只实现批准版 Prompt 需要的
组件。画布、帧率、包装、字体、人物布局、MG 和动画均**由批准版导演计划决定**；
不要复制 Skill 模板，也不要为未使用的构图预建代码分支。

保持以下薄接口：

- composition ID 为 `MasterComposition`；
- 入口为 `src/index.ts`，静态素材位于 `public/`；
- `master-props.json` 含 `durationInFrames`、与计划一致的 `renderSpec`，以及
  当前项目需要的字幕、章节、素材和 cue 数据；
- 输入视频承载唯一主音频；正式文字直接由 DOM/SVG 渲染。

使用相对坐标、响应式 CSS 或 `renderSpec` 计算几何。项目代码可以针对批准画面
写具体位置，但 Skill 脚本和文档中不得沉淀该项目的尺寸常量。

若批准计划引用三种基础构图之一，读取
[05-mg-themes.md](05-mg-themes.md)，只实现该项目使用的视觉关系，不创建全局
主题开关或另外两套未使用的组件。

若批准计划引用 `PPT Focus Portrait`，按
[04-theme-ppt-focus-portrait.md](04-theme-ppt-focus-portrait.md) 的比例关系实现，
再用本项目最长字幕、开场花字、人物窗和结尾 CTA 证据帧校准；不要复制另一个
项目的 Remotion component。

## 证据帧

先运行 `validate_plan.py`，再用 `render_master.mjs --still` 从同一
MasterComposition 输出：

- 开头、中段、结尾；
- 每个 cue 的 proof moment；
- 每个布局或素材切换边界。

逐帧确认语义、遮挡、人物比例、字体清晰度、字幕和批准包装。写入
`semantic-checklist.v1.json`、`aspect-occlusion-checklist.v1.json` 和
`package-checklist.v1.json`。

全部通过后立即读取并执行 [03-deliver.md](03-deliver.md)，不得停下或再次等待用户确认。
