---
name: producing-course-video-mg
description: Use when one or two already-cleaned course videos and a final SRT need narration-driven MG planning, visual switching, presenter overlay, or final composition.
---

# 课程视频 MG 制作

## 核心边界

这是一个离线 MG 后期工作流，不使用 OBS，也不负责 ASR 或口播精剪。

只接受以下两种已经准备完成的输入包：

- 单视频模式：一支精剪后的人像/口播录像 + 最终 SRT；
- 双视频模式：一支精剪后的人像/口播录像 + 与其从 `00:00` 同步且等长的精剪录屏 + 最终 SRT。

单视频输入可由 `cleaning-course-video-speech` 产出；双视频输入可由 `aligning-video-by-audio` 产出。这两个 Skill 只是推荐的上游准备方式，不是本 Skill 的运行依赖：只要输入已经满足上述条件，即可独立执行本工作流。

**所有口播理解、字幕核对、MG 节拍和最终主音频只能参考人像/录像视频。禁止使用录屏音频判断内容；录屏音频只可用于输入同步抽查，并在最终合成时静音或丢弃。**

- 不重新运行 `ASR → delete → polish`，不再删除停顿或重映射字幕；
- MG 点位只根据输入的最终 SRT 判断，不根据原片粗略时间码判断；
- 先交付并确认 MG 导演脚本；未经明确确认，不制作 MG、不合成最终成片。

## 独立运行与依赖

本 Skill 不依赖任何预先存在的课程仓库、目录结构或历史工程。调用时只需要用户提供：

- `face_video`：精剪后的人像/口播视频；
- `subtitles`：与人像视频匹配的最终 SRT；
- `screen_video`：可选；从 `00:00` 与人像视频同步且等长的精剪录屏；
- `lesson_id`：用于命名输出目录与 composition 的课程标识；
- `output_dir`：本课全部中间产物与交付物的输出目录。

输入和输出都可以位于任意本地路径。若用户没有指定 `output_dir`，在当前工作目录下使用 `mg-output/<lesson_id>-<date>/`。禁止假设存在任何既有工作区、历史工程、课程素材目录或预置 Remotion 项目。

### 运行环境

工作流假设运行在 macOS、Linux 或 WSL 的 Unix shell 中。必需工具：

- Node.js `>=20` 与 npm；已验证版本为 Node `24.15.0`、npm `11.12.1`；
- FFmpeg 与 ffprobe `>=6`，且构建中包含 `libx264`、`overlay`、`fade`、`crop`、`scale`、`geq`；已验证版本为 `7.1`；
- 项目内安装的 Remotion `4.0.419`、React/React DOM `19.2.3`、TypeScript `5.6.3`。

macOS 可先安装系统依赖：

```bash
brew install node ffmpeg
```

Ubuntu/Debian/WSL 可先安装 FFmpeg；Node.js `>=20` 使用官方安装包或版本管理器安装：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

创建本课 `remotion/` 工程时，在该目录内固定安装经过验证的渲染依赖：

```bash
npm init -y
npm install --save-exact @remotion/cli@4.0.419 remotion@4.0.419 react@19.2.3 react-dom@19.2.3
npm install --save-dev --save-exact typescript@5.6.3 @types/react@18.3.12 @types/react-dom@18.3.1
```

Remotion 必须通过项目内二进制调用，例如 `npx remotion studio src/index.ts`、`npx remotion render ...`，不要假设系统已经全局安装 `remotion`。首次安装 npm 依赖及准备 Remotion 浏览器渲染环境时需要网络：

```bash
npx remotion browser ensure
```

依赖和浏览器就绪后，本工作流本身可以离线运行。

开始前运行：

```bash
node --version
npm --version
ffmpeg -version
ffprobe -version
npm ls --depth=0 @remotion/cli remotion react react-dom typescript @types/react @types/react-dom
npx remotion versions
ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264
for filter in overlay fade crop scale geq; do
  ffmpeg -hide_banner -filters 2>/dev/null | awk '{print $2}' | grep -qx "$filter" || {
    echo "Missing FFmpeg filter: $filter" >&2
    exit 1
  }
done
```

任一必需命令不可用时，先完成依赖安装，不要开始生成导演脚本之后的制作阶段。

## 输出目录约定

每课使用一个独立的 `output_dir`：

- `MG导演脚本.md`：人读的导演脚本；`mg-placement-plan.v1.json`：机器读的合成依据（cue id、起止秒、人像策略），时间轴 = 精剪后视频的秒。
- `remotion/`：Remotion 工程。`src/specs.ts` 定义 composition id 与时长；`src/Root.tsx` 注册；`src/scenes.tsx` / `src/components.tsx` / `src/theme.ts` 是场景与设计系统；`src/Package.tsx` 是打包层。
- `segments/` 1080p MG 片段，`previews/` 低清预览，`final/` 交付物。

## 第 1 步：检查输入

1. 记录人像视频、最终 SRT、可选录屏、参考课件和输出目录。
2. 用媒体探测工具检查可解码性、分辨率、帧率、时长和音轨；确认 SRT 时间范围落在视频内。
3. 若有录屏，在开头、中段、结尾抽查同步与等长；发现持续漂移就停止并退回双视频前处理，不要在 MG 阶段补救。
4. 不改写输入视频、SRT 或既有剪辑时间线；所有中间产物进入本课目录。
5. 输入尚未精剪时停止本工作流。若对应上游 Skill 已安装，单视频可转交 `cleaning-course-video-speech`，双视频可转交 `aligning-video-by-audio`；否则明确说明缺少的前处理并要求用户提供合规输入。

## 第 2 步：冻结输入时间线

从这里开始，字幕和时间线标记为 final。后续所有章节、MG 点位和画面切换都同时记录最终字幕 ID 范围、字幕原文、最终入点和出点。若之后又删除或恢复口播内容，当前导演脚本立即失效，必须重新映射和确认。

## 第 3 步：按语义切成大段

阅读完整最终字幕，先切成章节或语义大块，再判断每个大块的画面类型：

- `screen-demo`：正在点击、输入、拖动、看网页、代码、表格或软件结果；
- `theory`：概念、框架、因果、对比、流程、抽象判断；
- `talking-head`：个人表达、情绪、故事、强调和自然过渡；
- `transition`：章节衔接或很短的补充句。

不要只列出 MG 段；要规划整条视频在"录屏、人像、MG"之间如何切换。

## 第 4 步：决定何时使用 MG

| 内容 | 默认画面 | 规则 |
|---|---|---|
| 真实屏幕操作 | 录屏为主体，人像右下角圆形小窗 | MG 不得遮挡关键点击、菜单、代码、表格或结果 |
| 理论、框架、抽象关系 | 全屏 MG + 右下角常驻人像圆窗 | 优先把关系、变化和顺序动画化，不堆大段文字 |
| 故事、态度、情绪强调 | 人像全屏 | 不要为了密度强行加 MG |
| 章节过渡 | 人像、简短标题卡或轻量 MG | 保持节奏，不喧宾夺主 |

补充规则：

- 没有录屏时，可以提高 MG 占比、减少纯人像占比，但不能伪造并不存在的软件操作。
- 有录屏时，`screen-demo` 对全屏 MG 拥有否决权。
- 每个 MG 只解释一个核心观点，通常覆盖一个完整观点（约 8–40 秒）；多个无关观点应拆成多条。

## 第 5 步：生成 MG 导演脚本并停下确认

生成人读的 `MG导演脚本.md` 和机器读的 `mg-placement-plan.v1.json`。

导演脚本至少包含：ID/章节、字幕锚点、内容类型、画面选择、教学目的、MG 分镜（2–5 个视觉节拍、简短屏幕文案、进出场）、人像策略、录屏保护、选择理由、状态（draft/approved）。末尾汇总总时长、MG/录屏/人像各占多少、全部待确认假设。

placement plan 记录每个 cue 的 `id`、`start_seconds`、`end_seconds`、对应 spec 路径，以及 `presenter_policy`（固定为 MG 期间全程右下角圆窗，见第 7 步）。

把导演脚本交给用户进行一轮或多轮修改。只有用户明确表示"确认、批准、按这版执行"等同等意思后，才标为 `approved`。用户仅说"你自行判断"只授权生成草案，不授权开始制作。

如果用户只要求 MG 导演脚本，到这里就停止，返回导演脚本与 placement plan 路径。

## 第 6 步：制作 MG（Remotion）

### 工程约定

1. 每个 cue 一个 composition，1920×1080@30fps，时长 = cue 窗口秒数；动画全部由 `useCurrentFrame` / `interpolate` / `spring` 帧驱动，禁止 wall-clock 计时；无外部图片素材，全部 CSS/SVG 绘制。
2. MG 片段静音；不含字幕、人像圆窗或角标——这些属于合成层和打包层。
3. **外壳单一来源：MG 场景不画任何进度条、章节标记、段落编号。** 并为打包层预留安全区：左上约 460×150 px（章节 pill）、底部中央约 140 px（字幕 + 进度条）、右下 400×400 px（人像圆窗常驻时）。
4. 连线、节点等需要相互对准的元素，必须共用同一套画布像素坐标（SVG viewBox 与 CSS 像素不一致会整体错位）。

### 设计原则（刻意保持少而松）

MG 的质量来自大胆和自由发挥，不来自规则：

- **按字幕内容本身大胆设计**：讲师在这段讲什么，画面就演什么。导演脚本的分镜表只是意图参考，不是施工图纸；觉得脚本的视觉比喻不好，直接换更好的。
- 每段只讲清一个核心观点；形式随内容自由发挥，不预设版式、组件库或分镜结构。
- 唯一的形式底线：不做"幻灯片换页"——画面里至少要有一个会动的关系（出现、组合、流转、变形、循环、收束）。

### 预览门禁

1. 先渲染 960×540 低清预览 + 连续预览带 + 拼贴检查表。
2. 自查：每段抽 4–6 帧（开头、各节拍点、结尾前 1 秒）逐张目检重叠/错位/出界/死时间/文字问题，至少完整迭代一轮再给用户看。
3. **必须经用户明确确认预览后，才允许渲染 1080p 正式版、合成成片。**

## 第 7 步：合成画面

- 底：人像视频统一到 30fps；每段 MG 一路输入，`format=rgba` + 首尾约 8 帧 `fade alpha=1`，`setpts=PTS-STARTPTS+<start>/TB` 后用 `overlay enable='between(t,start,end)'` 串成链。相邻两段 MG 首尾相接时硬切，不加淡入淡出。
- `setpts` 平移只用于"从 0 开始的短片段"（如 MG 段）。与主时间轴零点对齐且等长的输入（如双轨录屏）**禁止 setpts 平移**，直接 `overlay enable='between(t,start,end)'`——它的 PTS 本来就在正确位置。`overlay` 默认 `shortest=0`，按最长输入决定输出时长：任何次级流若晚于主流结束，成片都会被拉长。次级流确实需要平移时，先 `trim` 到窗口长度。
- 主音频 `-c:a copy` 只能来自人像视频，跨所有切换连续；MG 与录屏音频静音或丢弃。
- 人像圆窗：先抽 3+ 帧确认人脸位置全程稳定。稳定就用圆形（`crop` + `scale=360:360` + `geq` 圆形 alpha 蒙版），不稳定或定位失败就用方形；位置右下角（1920×1080 下 overlay 1520:680）。**MG 期间与录屏演示期间人像圆窗常驻右下角，这是固定规则，不再逐课确认。**
- 录屏不是 16:9 时裁切成 16:9，不留黑边：如 2916×1840 → 裁为 2916×1638（宽度除 16/9，向下取偶数）。裁切偏移按内容抽帧确认，保证关键 UI、菜单、按钮、代码和结果不被切掉。
- 交付两层：干净母版（无字幕无包装）+ 打包版。除非用户明确不要包装，两层都要出。

## 第 7.5 步：打包（字幕 + 章节 + 进度条）

打包层是外壳的唯一来源，是与 MG 同工程、共享坐标的 Remotion composition：以干净母版为底视频，叠加字幕、章节 pill、章节进度条，主音频随底视频通过。**打包层是固定件，不要灵活发挥，下面数值直接照抄。**

### 数据流

1. 解析最终 SRT → `captions: [{start, end, text}]`（剪辑后时间轴秒）；章节表 `topics: [{title, start, end}]`（边界行 ID 查 SRT 换算成秒；补剪后同步重映射；标题以用户修订为准）。
2. 生成 `src/package-props.json`：`{src, captions, topics, durationInFrames}`，`durationInFrames = ceil(母版时长 × 30)`；母版实体拷贝到 `remotion/public/`（Remotion 打 bundle 不跟随 symlink）。
3. 注册 composition：1920×1080@30fps，defaultProps = package-props.json。
4. 渲染：`npx remotion render src/index.ts <lesson_id>-package ../final/<lesson_id>_final.mp4 --codec=h264 --crf=18`。

### 视觉规格（1920×1080，全部帧驱动，t = frame/fps）

- 底视频：`OffthreadVideo src={staticFile(src)}` 全幅。
- 字幕：取 `t` 命中的 caption；底部居中（`bottom: 96`，在进度条上方），`maxWidth: 屏宽×0.68`，字号 `max(26, 屏高×0.049)`≈53px，weight 700，颜色 `#f9fbff`，lineHeight 1.5，`whiteSpace: pre-line`；描边用多层 text-shadow：四正方向 `±0.035em rgba(15,23,42,.7)` + 四斜角 `±0.025em rgba(15,23,42,.55)` + `0 0.05em 0.14em rgba(2,6,23,.35)`。
- 章节 pill：`top: 屏高×0.035`、`left: 屏宽×0.022`；深色卡片 `linear-gradient(135deg, rgba(37,43,58,.66), rgba(13,18,27,.5))`，圆角 14，左缘 5px accent 竖条，投影；上行 `CHAPTER i/N`（字号 `屏高×0.0165`，letterSpacing 0.14em，accent 色），下行章节标题（字号 `屏高×0.036`，weight 800，`#f9fbff`）。accent 色板按章节序号取：`#8ee0ff #ffb38a #9dffc3 #c4a8ff #ffd166 #ff8ad1`。当前章 = `t >= topic.start` 的最后一个 topic。
- 进度条：`bottom: 28`，左右 inset 46，高 30，圆角 999，边框 `2px rgba(255,255,255,.14)`，底 `rgba(13,18,27,.38)`；每章一段、段宽 = 章节时长/总时长；当前章段底 `rgba(255,255,255,.07)`、标签 15px weight 750 `rgba(255,255,255,.92)`，其余段底 `.018`、weight 650 `rgba(244,248,255,.72)`；段宽（px）< 标题字数×18+24 时隐藏该段标签；最底层整体进度填充 `width: t/total`，颜色 `rgba(93,220,205,.36)`。

## 第 8 步：验收与交付

1. 时长校验：成片时长 == 精剪视频时长（ffprobe 比对）。
2. 完整解码：`ffmpeg -v error -i 成片 -f null -` 无输出。
3. 抽帧目检：每个 MG 窗口内至少 1 帧 + 边界前后帧 + 纯人像段 1 帧，确认无黑帧、无遮挡关键内容、圆窗取景正确、切换干净、外壳只出现一套。
4. 双视频模式还要确认两条视频始终同步、录屏音频未进入混音、操作段未被 MG 或圆窗遮挡。

交付：批准版 MG 导演脚本与 placement plan、MG 源码与独立片段、连续预览、干净母版、打包版和输入 SRT。输入的人像视频与可选录屏保持不变。

## 必须停止的情况

- 人像视频、主音轨或最终 SRT 不可用；
- 双视频输入并未真正同步或时长不一致；
- 输入仍需删除口播或重映射字幕，此时退回对应前处理 Skill；
- 最终字幕仍有系统性错误或时间漂移，且尚未由前处理 Skill 修复；
- MG 导演脚本尚未明确批准，或低清预览尚未经用户确认；
- 批准后又发生会改变点位、文案、时长、布局或遮挡策略的修改。
