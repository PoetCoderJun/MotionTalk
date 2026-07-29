# 阶段 1：检查、规划、冻结

本阶段只交付导演脚本与机器点位表。未经用户明确批准，不创建 Remotion 工程、不制作 MG、不合成视频。

## 1. 检查输入

1. 记录 `video`、`subtitles` 和 `output_dir`，从口播文件名推导 `project_id`。
2. 用 `ffprobe` 检查视频可解码性、分辨率、帧率、时长和音轨。
3. 完整检查 SRT：序号连续、时间码递增且不重叠、最后一条不超过视频时长；抽查开头、中段和结尾的音画对齐。系统性错字、术语无法判断或持续漂移时停止。
4. 把输入时间线标为 final。后续每个点位同时记录最终字幕 ID 范围、字幕原文和起止秒。
5. 若用户给出样例视频，记录正式样例成片路径并抽取至少 5 张包装证据帧；分别识别章节牌、累计进度条、字幕、字体层级和 MG 风格。包装样式与 MG 样式分开记录，禁止把“只改 MG”误解成重做包装。

若用户没有 SRT，路由到独立转写流程，得到并核对最终 SRT 后再回来。不得在本工程实现或宣称 ASR。

## 2. 按语义规划完整画面时间线

先读完整字幕，切成章节或语义大块，再把每段标为：

- `visual-explanation`：关系、步骤、对比、数据或示意；
- `theory`：概念、框架、因果、流程、抽象判断；
- `talking-video`：个人表达、情绪、故事、强调和自然过渡；
- `transition`：章节衔接或很短的补充句。

不要只列 MG 段。完整规划“口播原画面 ↔ MG”时间线。

由 Agent 按 [05-mg-themes.md](05-mg-themes.md) 为草案选定**画面构成主题**：`floating-overlay`（MG 悬浮在人物画面上）、`mg-with-presenter-window`（全屏 MG + 人像蒙版窗，默认）或 `switching`（人像 ↔ MG ↔ 录屏切换）。主题作为草案提议的一部分随导演脚本一次批准，不单独询问用户。主题为 `floating-overlay` 时，必须先从原片抽至少 5 帧实测人脸位置，把人脸安全区和 MG 可用区域（顶部横带、左右侧翼）写成相对坐标，作为布局硬约束。

| 内容 | 默认画面 | 边界 |
|---|---|---|
| 步骤、对比、数据、关系 | 全屏 MG + 右下角人像（或 floating-overlay 主题下的侧翼悬浮 MG） | 演变化、顺序和关系，不堆长文 |
| 理论、框架、抽象关系 | 全屏 MG + 右下角人像（同上） | 视觉化关系，不做换页 PPT |
| 故事、态度、情绪 | 人像全屏 | 不为密度强行加 MG |
| 段落过渡 | 人像或轻量标题/MG | 保持节奏 |

补充规则：

- 不伪造输入里不存在的软件操作、界面、数据或事实。
- 原画面承担重要情绪或肢体表达时保留人像。
- 每个 MG 只解释一个核心观点，通常覆盖完整的 8–40 秒观点；无关观点拆开。
- 每个 MG cue 必须把核心观点写成 1–3 条可由静态证据帧判定真假的“语义验收点”。关系图明确记录数量、父子/归属、方向、顺序和分组；字幕没有给出精确数量时不要擅自补数量。
- 每条语义验收点同时写明 `proof_moment`（在哪个视觉节拍取证）和 `forbidden`（最容易出现的错误解读）。例如“两名 Agent 恰好形成两条分支；老板修改版属于 Agent A 分支后续节点；不得画成第三条分支”。

## 3. 产物

写入：

- `MG导演脚本.md`：ID、字幕锚点、内容类型、画面选择、表达目的、2–5 个视觉节拍、简短屏幕文案、语义验收点及其取证时刻/禁止误读、进出场、人像策略、选择理由和状态。
- `mg-placement-plan.v1.json`：`project_id`、源文件、总时长、每个 cue 的 `id/start_seconds/end_seconds/srt_range/spec`、人像窗口、章节、`presenter_policy` 和状态。每个 MG cue 的 `spec.semantic_invariants` 必须是对象数组，每项包含稳定 `id`、`assertion`、`proof_moment` 和 `forbidden` 字符串数组。
- `mg-placement-plan.v1.json` 还必须包含 `package_style`。默认使用 `profile: sample-classic-v1`：章节牌启用；进度条启用、左右各 46px、底部 28px、高 30px、轨道标签由 ASS 单层绘制、按章节时长分段、整片累计填充；字幕只保留一套。任何关闭章节牌/进度条或把进度条高度降到 24px 以下的方案必须在批准前明确提示，不得静默采用。

placement plan 的机器 schema 硬要求（下游脚本按此读取，缺一会直接报错）：

- 顶层同时写 `status: "approved"` 和 `approved: true`（批准后）；`mg_theme` 为主题名。
- `source` 必须含 `video/subtitles`（绝对路径）、`width/height/fps/duration_seconds`；1920×1080@60 以外走不了 2B 管线。
- `cues` 必须覆盖整条时间线：从第 0 帧开始、按 60fps 帧对齐、相邻 cue 首尾帧严格连续；每个 cue 写 `visual`（`presenter-full-screen`、`transparent-floating-overlay-on-presenter` 或全屏 MG/录屏类取值），非纯人像 cue 带 `spec`。
- `floating-overlay` 主题还需 `presenter_policy.default: "full-screen-underlay"` 和 `overlay_style`（`key_color/key_similarity/key_blend/despill_*`）。
- `chapters` 每项必须含稳定 `id`（包装覆盖层按 `id` 命名 PNG）、`start_seconds/end_seconds/title`，长标题配 `short_label`。
- 默认必须生成 `caption_highlights`：字幕关键词加大变色，规格见 [04-package-contract.md](04-package-contract.md)；强调哪些词由 Agent 自行判断（结论、转折、数字、专有名词等观看锚点），关键词必须是字幕原文片段。只有用户明确要求不要强调时才允许写 `enabled: false`，且必须在批准前明确提示。

导演脚本要单列“包装冻结项”和“MG 可变项”。字体方案也要写入：包装沿用样例层级；MG 不默认使用细字、灰字或整片同款半透明玻璃卡，允许粗体、实体色块、贴纸、描边字或其他与语义匹配的视觉语言。

批准前逐条确认语义验收点能从字幕或用户提供的课件中找到依据，并且不存在相互矛盾的 assertion。末尾汇总总时长、MG/人像占比与所有待确认假设。状态先写 `draft`，把两个文件交给用户。只有用户明确说“确认、批准、按这版执行”等同义表达后才改为 `approved`，然后停止本阶段。这次草案批准是全流程唯一的用户打断：主题、关键词强调、节奏等所有决策都必须作为草案提议一并呈现，不得拆成多次确认。
