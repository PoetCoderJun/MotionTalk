---
name: talking-mg-video
description: Use when an already-cut selfie talking-head or spoken video needs MG animation or smooth switching among presenter, synchronized screen recording, and MG, whether or not a matching SRT already exists.
---

# Talking MG Video

## 核心边界

这是一个 AI 驱动的口播视频 MG 后期工作流，不使用 OBS，也不负责删除口误、停顿或重新精剪口播。SRT 是可选输入：如果没有与成片时间线匹配的 SRT，必须先用 AI 为精剪后口播视频生成对应的 SRT，再进入 MG 规划。

支持两种输入模式：

- **普通模式（单视频）**：一支精剪后、保留最终主音频的自拍口播视频；根据口播内容生成对应的 MG 分镜动画，并规划“自拍口播原画面 ↔ MG”的切换；
- **双视频模式**：上述自拍口播视频 + 一支从 `00:00` 同步且等长的录屏；根据语义自动规划“录屏 ↔ 自拍口播 ↔ MG”的丝滑切换。

两种模式都可额外提供与精剪视频时间线匹配的最终 SRT；未提供时先用 AI 自动生成。

此外必须指定一个明确的输出目录。

**所有口播理解、字幕核对、MG 节拍和最终主音频只能参考口播视频。录屏音频只用于同步抽查，最终必须静音或丢弃。**

- 无 SRT 时只运行 AI 转写来生成与当前精剪时间线一致的字幕，不得借机执行 `delete → polish`、删除停顿或改变口播时间线；
- MG 点位只根据已验收的工作 SRT 判断，不根据原片粗略时间码判断；
- 先交付并确认 MG 导演脚本；未经明确确认，不制作 MG、不合成最终成片。

## 独立运行与依赖

本 Skill 不依赖任何预先存在的仓库、目录结构或历史工程。调用时始终需要：

- `video`：精剪后的口播视频；
- `output_dir`：全部中间产物与交付物的独立输出目录。

可选输入：

- `subtitles`（可选）：与视频匹配的最终 SRT；缺省时使用 AI 从 `video` 生成；
- `screen_video`：双视频模式使用、与口播视频从 `00:00` 同步且等长的录屏。

项目标识 `project_id` 从 `video` 的文件名自动推导：取不含扩展名的文件名并规范化为小写连字符格式。禁止要求用户额外提供项目名。输入和输出可以位于任意本地路径；禁止假设存在任何既有工作区、素材目录或预置 Remotion 项目。

### 运行环境

工作流假设运行在 macOS、Linux 或 WSL 的 Unix shell 中。必需工具：

- Node.js `>=20` 与 npm；已验证版本为 Node `24.15.0`、npm `11.12.1`；
- FFmpeg 与 ffprobe `>=6`，且构建中包含 `libx264`、`overlay`、`fade`、`crop`、`scale`、`geq`；已验证版本为 `7.1`；
- 项目内安装的 Remotion `4.0.419`、React/React DOM `19.2.3`、TypeScript `5.6.3`。

没有输入 SRT 时，还必须有可用的 AI 语音转写能力，能够从 `video` 的主音轨输出带时间码的 SRT。可以使用当前环境中可用的本地 ASR 模型、视频转写 Skill 或云端 AI 转写服务；不得伪造字幕或只用无时间码的纯文本代替。云端转写可能需要网络，本地模型则可以离线运行。

### 性能与硬件编码策略

渲染时间分成两部分，必须分别处理：

- **Remotion 逐帧绘制**：Chromium 将 CSS/SVG/React 场景逐帧绘制成图像，主要受 CPU、内存和浏览器图形后端影响；VideoToolbox 不能跳过这一步。
- **视频编码与 FFmpeg 最终合成输出**：macOS 上必须优先使用 VideoToolbox，避免对每个 MG 片段、干净母版和打包版重复使用 `libx264` 软件编码。

在 macOS 上，正式渲染和低清预览都必须使用 `h264_videotoolbox`。Remotion `4.0.419` 的对应开关是 `--hardware-acceleration=required`；使用 `required` 而不是静默回退，确保硬编不可用时立即失败并修复环境。**硬编模式不能使用 `--crf`、`--encoding-max-rate` 或 `--encoding-buffer-size`；统一用 `--video-bitrate` 控制质量。** `--x264-preset` 对 VideoToolbox 无效，也不得作为性能方案。

Linux/WSL 的本 Skill 已验证链路仍使用 `libx264`；除非当前 Remotion/FFmpeg 组合已单独验证对应硬件编码器和质量，否则不要伪造“已硬件加速”的状态。macOS 以外可继续软件编码，但必须在交付说明中标明。

默认先用 `--concurrency=75%`；它加速的是 Remotion 同时绘制的帧数，不是编码器。对每台新机器用一个含 SVG、文本和视频层的代表性 20–40 秒 cue，分别测 `50%`、`75%`、`100%`，选择总耗时最短且不发生内存压力、掉帧或浏览器崩溃的值，并把实测值写入该项目的 `remotion/README.md`。不要同时并行启动多个 `remotion render` 进程来“加速”同一项目。

`npx remotion gpu` 只用于诊断 Chromium 的画面绘制后端；不要把它与 VideoToolbox 编码混为一谈，也不要未经实测强制 `--gl` 值。默认让 Chrome 选择后端，只有 GPU 诊断和代表性渲染均证明更快、更稳定时才固定 `--gl`。

macOS 可先安装系统依赖：

```bash
brew install node ffmpeg
```

Ubuntu/Debian/WSL 可先安装 FFmpeg；Node.js `>=20` 使用官方安装包或版本管理器安装：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

创建本项目 `remotion/` 工程时，在该目录内固定安装经过验证的渲染依赖：

```bash
npm init -y
npm install --save-exact @remotion/cli@4.0.419 remotion@4.0.419 react@19.2.3 react-dom@19.2.3
npm install --save-dev --save-exact typescript@5.6.3 @types/react@18.3.12 @types/react-dom@18.3.1
```

Remotion 必须通过项目内二进制调用，例如 `npx remotion studio src/index.ts`、`npx remotion render ...`，不要假设系统已经全局安装 `remotion`。首次安装 npm 依赖及准备 Remotion 浏览器渲染环境时需要网络：

```bash
npx remotion browser ensure
```

依赖、浏览器和输入 SRT 就绪后，本工作流可以离线运行；若需要临时调用云端 AI 生成 SRT，则该转写步骤需要网络。

开始前运行：

```bash
node --version
npm --version
ffmpeg -version
ffprobe -version
npm ls --depth=0 @remotion/cli remotion react react-dom typescript @types/react @types/react-dom
npx remotion versions
ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264
if [ "$(uname -s)" = "Darwin" ]; then
  ffmpeg -hide_banner -encoders 2>/dev/null | grep -q 'h264_videotoolbox' || {
    echo "Missing macOS VideoToolbox H.264 encoder" >&2
    exit 1
  }
fi
for filter in overlay fade crop scale geq; do
  ffmpeg -hide_banner -filters 2>/dev/null | awk '{print $2}' | grep -qx "$filter" || {
    echo "Missing FFmpeg filter: $filter" >&2
    exit 1
  }
done
```

任一必需命令不可用时，先完成依赖安装，不要开始生成导演脚本之后的制作阶段。

macOS 上还必须用一个 20–40 秒代表性 cue 做一次正式渲染前的编码冒烟测试。渲染日志必须出现 `Encoder: h264_videotoolbox, hardware accelerated: true`；未出现就停止，不要继续以软件编码完成整条片子。此检查在用户确认导演脚本后、批量制作前执行。

## 输出目录约定

每个视频项目使用用户指定的独立 `output_dir`：

- `subtitles/`：无输入 SRT 时保存 AI 生成的 `<project_id>.generated.srt`；有输入 SRT 时不复制或改写原文件。
- `MG导演脚本.md`：人读的导演脚本；`mg-placement-plan.v1.json`：机器读的合成依据（cue id、起止秒、人像策略），时间轴 = 精剪后视频的秒。
- `remotion/`：Remotion 工程。`src/specs.ts` 定义 composition id 与时长；`src/Root.tsx` 注册；`src/scenes.tsx` / `src/components.tsx` / `src/theme.ts` 是场景与设计系统；`src/Package.tsx` 是打包层。
- `segments/` 1080p MG 片段，`previews/` 低清预览，`final/` 交付物。

## 第 1 步：检查输入并准备 SRT

1. 记录口播视频、可选 SRT、可选录屏和输出目录；从口播视频文件名推导 `project_id`，并据此判断普通模式或双视频模式。
2. 用媒体探测工具检查视频的可解码性、分辨率、帧率、时长和音轨。
3. 准备唯一的工作 SRT：
   - 已提供 `subtitles`：检查格式、内容和时间范围，不改写原文件，直接把它作为工作 SRT；
   - 未提供 `subtitles`：先用可用的 AI 语音转写能力读取 `video` 的最终主音轨，生成 `output_dir/subtitles/<project_id>.generated.srt`，再把生成文件作为工作 SRT；
   - AI 生成字幕必须使用标准 SRT 序号和 `HH:MM:SS,mmm --> HH:MM:SS,mmm` 时间码；只允许修正明显错字和断句，不得删改口播内容、压缩停顿、翻译或改变视频时间线。
4. 完整检查工作 SRT：序号连续、时间码递增且不重叠、最后一条字幕不超过视频时长；结合开头、中段、结尾音频抽查对齐。出现系统性错字、术语无法判断或持续时间漂移时停止，不得带病进入 MG 规划。
5. 若有录屏，在开头、中段和结尾抽查同步与等长；发现持续漂移就停止，不在 MG 阶段补救。
6. 不改写输入视频、用户提供的 SRT 或既有剪辑时间线；所有新生成的中间产物进入 `output_dir`。

## 第 2 步：冻结输入时间线

从这里开始，把工作 SRT 和视频时间线标记为 final。后续所有章节、MG 点位和画面切换都同时记录最终字幕 ID 范围、字幕原文、最终入点和出点。若之后又删除或恢复口播内容，当前导演脚本立即失效，必须重新映射和确认。

## 第 3 步：按语义切成大段

阅读完整最终字幕，先切成章节或语义大块，再判断每个大块的画面类型：

- `screen-demo`：双视频模式中正在点击、输入、拖动、查看网页、代码、表格或软件结果；
- `visual-explanation`：适合用关系、步骤、对比、数据或示意动画解释的内容；
- `theory`：概念、框架、因果、对比、流程、抽象判断；
- `talking-head`：个人表达、情绪、故事、强调和自然过渡；
- `transition`：章节衔接或很短的补充句。

不要只列出 MG 段；普通模式规划“自拍口播原画面、MG”的切换，双视频模式规划“自拍口播原画面、录屏、MG”的切换。

## 第 4 步：决定何时使用 MG

| 内容 | 默认画面 | 规则 |
|---|---|---|
| 真实屏幕操作 | 录屏为主体，人像右下角圆形小窗 | MG 不得遮挡关键点击、菜单、代码、表格或结果 |
| 步骤、对比、数据、关系 | 全屏 MG + 右下角常驻人像圆窗 | 优先演示变化、顺序和关系，不堆大段文字 |
| 理论、框架、抽象关系 | 全屏 MG + 右下角常驻人像圆窗 | 优先把关系、变化和顺序动画化，不堆大段文字 |
| 故事、态度、情绪强调 | 人像全屏 | 不要为了密度强行加 MG |
| 段落过渡 | 人像、简短标题卡或轻量 MG | 保持节奏，不喧宾夺主 |

补充规则：

- 不伪造输入中不存在的软件操作、产品界面、数据或事实。
- 双视频模式中，`screen-demo` 对全屏 MG 拥有否决权。
- 原画面本身承担重要情绪或肢体表达时，保留口播原画面。
- 每个 MG 只解释一个核心观点，通常覆盖一个完整观点（约 8–40 秒）；多个无关观点应拆成多条。

## 第 5 步：生成 MG 导演脚本并停下确认

生成人读的 `MG导演脚本.md` 和机器读的 `mg-placement-plan.v1.json`。

导演脚本至少包含：ID/段落、字幕锚点、内容类型、画面选择、表达目的、MG 分镜（2–5 个视觉节拍、简短屏幕文案、进出场）、人像策略、录屏保护、选择理由、状态（draft/approved）。末尾汇总总时长、MG/口播原画面/录屏各占多少、全部待确认假设。

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

- **按字幕内容本身大胆设计**：说话者在这段讲什么，画面就演什么。导演脚本的分镜表只是意图参考，不是施工图纸；觉得脚本的视觉比喻不好，直接换更好的。
- 每段只讲清一个核心观点；形式随内容自由发挥，不预设版式、组件库或分镜结构。
- 唯一的形式底线：不做"幻灯片换页"——画面里至少要有一个会动的关系（出现、组合、流转、变形、循环、收束）。

### 预览门禁

1. 先渲染 960×540 低清预览 + 连续预览带 + 拼贴检查表。macOS 预览命令固定为：

   ```bash
   npx remotion render src/index.ts <cue_id> ../previews/<cue_id>.preview.mp4 \
     --codec=h264 --hardware-acceleration=required --video-bitrate=4M \
     --scale=0.5 --concurrency=75% --overwrite
   ```

   禁止在这条命令或对应脚本中添加 `--crf`。非 macOS 删除 `--hardware-acceleration=required`，并在项目 README 标明软件编码。
2. 自查：每段抽 4–6 帧（开头、各节拍点、结尾前 1 秒）逐张目检重叠/错位/出界/死时间/文字问题，至少完整迭代一轮再给用户看。
3. **必须经用户明确确认预览后，才允许渲染 1080p 正式版、合成成片。**
4. 1080p MG 片段命令固定为：

   ```bash
   npx remotion render src/index.ts <cue_id> ../segments/<cue_id>.mp4 \
     --codec=h264 --hardware-acceleration=required --video-bitrate=16M \
     --concurrency=75% --overwrite
   ```

   每个项目应把这两套参数封装在 `remotion/scripts/` 的单一渲染脚本中，预览与正式版只允许分辨率、码率和输出路径不同，避免后续重新引入 CRF 或软编码。

## 第 7 步：合成画面

- 底：输入视频统一到 30fps；每段 MG 一路输入，`format=rgba` + 首尾约 8 帧 `fade alpha=1`，`setpts=PTS-STARTPTS+<start>/TB` 后用 `overlay enable='between(t,start,end)'` 串成链。相邻两段 MG 首尾相接时硬切，不加淡入淡出。
- 双视频模式中，录屏与主时间轴零点对齐且等长，禁止 `setpts` 平移；按 `screen-demo` 窗口直接 overlay。录屏音频不得进入最终混音。
- `setpts` 平移只用于从 0 开始的短 MG 片段。`overlay` 默认 `shortest=0`，按最长输入决定输出时长；每段 MG 必须先 `trim` 到 cue 窗口长度，避免成片被次级流拉长。
- 主音频 `-c:a copy` 只能来自口播视频，并跨所有画面切换连续；MG 与录屏音频必须静音或丢弃。
- macOS 上，含 `overlay` / `crop` / `geq` 的 FFmpeg 合成滤镜仍在 CPU 完成；最终输出必须明确指定 `-c:v h264_videotoolbox -b:v 16M -pix_fmt yuv420p`。不要为这条滤镜链盲加输入侧 `-hwaccel videotoolbox`：这些 CPU 滤镜通常会引入不必要的硬件帧回传，不能替代最终硬编。Linux/WSL 保持 `-c:v libx264`，并显式写出码率或 CRF。
- 人像圆窗：先抽 3+ 帧确认人脸位置全程稳定。稳定就用圆形（`crop` + `scale=360:360` + `geq` 圆形 alpha 蒙版），不稳定或定位失败就用方形；位置右下角（1920×1080 下 overlay 1520:680）。**MG 与录屏演示期间人像圆窗常驻右下角。**
- 录屏不是 16:9 时裁切成 16:9，不留黑边；裁切偏移必须抽帧确认，保证关键 UI、菜单、代码和结果不被切掉。
- 交付两层：干净母版（无字幕无包装）+ 打包版。除非用户明确不要包装，两层都要出。

## 第 7.5 步：打包（字幕 + 章节 + 进度条）

打包层是外壳的唯一来源，是与 MG 同工程、共享坐标的 Remotion composition：以干净母版为底视频，叠加字幕、章节 pill、章节进度条，主音频随底视频通过。**打包层是固定件，不要灵活发挥，下面数值直接照抄。**

### 数据流

1. 解析已冻结的工作 SRT → `captions: [{start, end, text}]`（剪辑后时间轴秒）；章节表 `topics: [{title, start, end}]`（边界行 ID 查 SRT 换算成秒；补剪后同步重映射；标题以用户修订为准）。
2. 生成 `src/package-props.json`：`{src, captions, topics, durationInFrames}`，`durationInFrames = ceil(母版时长 × 30)`；母版实体拷贝到 `remotion/public/`（Remotion 打 bundle 不跟随 symlink）。
3. 注册 composition：1920×1080@30fps，defaultProps = package-props.json。
4. macOS 渲染：

   ```bash
   npx remotion render src/index.ts <project_id>-package ../final/<project_id>_final.mp4 \
     --codec=h264 --hardware-acceleration=required --video-bitrate=16M \
     --concurrency=75% --overwrite
   ```

   禁止传 `--crf`。非 macOS 使用已验证的软件编码参数，并在项目 README 记录该例外。

### 视觉规格（1920×1080，全部帧驱动，t = frame/fps）

- 底视频：`OffthreadVideo src={staticFile(src)}` 全幅。
- 字幕：取 `t` 命中的 caption；底部居中（`bottom: 96`，在进度条上方），`maxWidth: 屏宽×0.68`，字号 `max(26, 屏高×0.049)`≈53px，weight 700，颜色 `#f9fbff`，lineHeight 1.5，`whiteSpace: pre-line`；描边用多层 text-shadow：四正方向 `±0.035em rgba(15,23,42,.7)` + 四斜角 `±0.025em rgba(15,23,42,.55)` + `0 0.05em 0.14em rgba(2,6,23,.35)`。
- 章节 pill：`top: 屏高×0.035`、`left: 屏宽×0.022`；深色卡片 `linear-gradient(135deg, rgba(37,43,58,.66), rgba(13,18,27,.5))`，圆角 14，左缘 5px accent 竖条，投影；上行 `CHAPTER i/N`（字号 `屏高×0.0165`，letterSpacing 0.14em，accent 色），下行章节标题（字号 `屏高×0.036`，weight 800，`#f9fbff`）。accent 色板按章节序号取：`#8ee0ff #ffb38a #9dffc3 #c4a8ff #ffd166 #ff8ad1`。当前章 = `t >= topic.start` 的最后一个 topic。
- 进度条：`bottom: 28`，左右 inset 46，高 30，圆角 999，边框 `2px rgba(255,255,255,.14)`，底 `rgba(13,18,27,.38)`；每章一段、段宽 = 章节时长/总时长；当前章段底 `rgba(255,255,255,.07)`、标签 15px weight 750 `rgba(255,255,255,.92)`，其余段底 `.018`、weight 650 `rgba(244,248,255,.72)`；段宽（px）< 标题字数×18+24 时隐藏该段标签；最底层整体进度填充 `width: t/total`，颜色 `rgba(93,220,205,.36)`。

## 第 8 步：验收与交付

1. 时长校验：成片时长 == 精剪视频时长（ffprobe 比对）。
2. 完整解码：`ffmpeg -v error -i 成片 -f null -` 无输出。
3. 抽帧目检：每个 MG 窗口内至少 1 帧 + 边界前后帧 + 纯人像段 1 帧，确认无黑帧、圆窗取景正确、切换干净、外壳只出现一套。
4. 音轨校验：成片只保留输入视频的主音频，且全程连续。
5. 双视频模式还要确认录屏始终同步、录屏音频未进入混音、关键操作未被 MG 或圆窗遮挡。
6. macOS 性能校验：保存每次 Remotion 渲染日志；低清预览、1080p MG 片段和打包版都必须可在日志中确认 `h264_videotoolbox`。若使用 FFmpeg 合成，保存完整命令，确认包含 `-c:v h264_videotoolbox`。仅用 `ffprobe` 看到 `h264` 不足以证明使用了硬件编码。

交付：批准版 MG 导演脚本与 placement plan、MG 源码与独立片段、连续预览、干净母版、打包版，以及最终采用的工作 SRT（用户原始文件或 AI 生成文件）。口播视频、可选录屏和用户提供的 SRT 保持不变。

## 必须停止的情况

- 输入视频、主音轨或 `output_dir` 不可用；
- 未提供 SRT，且当前环境无法用 AI 成功生成与视频对齐的 SRT；
- 双视频模式的录屏未真正同步或时长不一致；
- 输入仍需删除口播、重剪视频或重映射字幕；
- 最终字幕仍有系统性错误或时间漂移；
- MG 导演脚本尚未明确批准，或低清预览尚未经用户确认；
- 批准后又发生会改变点位、文案、时长、布局或遮挡策略的修改。
