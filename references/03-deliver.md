# 阶段 2B：正式渲染、合成、包装、验收

本文件是 [02-build.md](02-build.md) 在**同一次调用**中的强制续行部分，不是独立阶段，也不是新的用户确认边界。前提是正式 MG 片段已渲染，画面检查表和 `semantic-checklist.v1.json` 全部通过；满足后直接执行整片合成与交付，**不得再次请求确认**。

## 1. 合成架构：短 MG + 互斥 cue + 单次整片包装

**不要为了“统一”改成全 Remotion。** VideoToolbox只加速编码；Remotion 仍需 Chromium 抓取每一帧。包装成片只需一次全片浏览器渲染就会非常慢，因此默认使用短 MG + FFmpeg 的混合架构。

默认混合架构：

1. Remotion 只绘制真正有动画的短 MG cue；
2. `scripts/render_package_overlays.mjs` 一次 bundle、一次 browser，生成每章一张透明包装静帧；
3. `scripts/build_and_package.py` 按互斥 cue 生成临时无音频合成段，统一颜色元数据后无损拼成临时视频底；
4. 同一个脚本对整条视频底执行**单次整片包装**：一次叠加章节静帧、累计进度条和字幕，一次视频编码，同时从口播原片复制主音频；
5. `scripts/quality_gate.py` 完成最终门禁；通过后只删除脚本创建的精确中间片。

当批准版 `presenter_policy.default` 为 `full-screen-underlay`，且 cue 的
`visual` 为 `transparent-floating-overlay-on-presenter` 时，人物原片直接作为
全屏底画。正式 MG 片段使用 placement plan 的 `overlay_style.key_color`
纯色键背景，`build_and_package.py` 通过同一份计划里的 `key_similarity` 与
`key_blend` 抠出 MG，并按 `despill_type/despill_mix/despill_expand`
消除键色边缘污染后覆盖到底画；这一模式不创建人物圆窗，也不把 MG 当作
整屏替代画面。键色不得用于 MG 正文、图标、阴影或抗锯齿边缘。

这套路径是默认执行入口，不要把脚本复制进项目后私改。先运行各脚本的 `--help`；标准命令见下一节。

FFmpeg 合成不得把 1920×1080 底片转为整片 RGBA，也不得让每帧串行穿过所有 cue 的 overlay 链。脚本按完整时间线切成互斥 segment：

- 纯人像段：直接 trim；
- MG 段：当前人像底 + 当前 MG + 人像圆窗；
- 每个局部 segment 用同一编码、像素格式、BT.709 和 TV range 参数输出；concat demuxer 只用于拼临时无音频视频底。最终音频在单次整片包装时直接从口播原片 `-c:a copy`。

这样每帧最多只经过当前 segment 的 1–2 次 overlay。底片保持 `yuv420p`；只有需要 alpha fade 的 MG 转 `yuva420p`。相邻 MG 窗口硬切；非相邻 MG 首尾可用约 8 帧 alpha fade 回到人像底。

**合成陷阱（L03 实测，两个都静默失败、ffmpeg 退出码为 0）：**

- 不要在整条底片流上串接多组 fade 来圈多个窗口：`fade=in` 会把 st 之前所有帧的 alpha 强制为 0，`fade=out` 会把 st+d 之后所有帧强制为 0，串联后所有窗口的 alpha 全部归零，overlay 看似"没生效"。fade 只用于从 0 开始的短 MG 片段首尾（窗口局部时间，因此安全）。
- 不要把同一个滤镜标签（如 `[scr]`）作为多路 overlay 的第二输入：实测只有第一路 overlay 生效，其余窗口静默漏出底片。每路 overlay 用一条独立分支，显式 `split=N`。
- 这两个 bug 用 ffprobe 和退出码都查不出来；每个 MG 窗口都必须至少抽 1 帧全尺寸目检才算数。

人像圆窗先抽至少 3 帧确认脸位。稳定时 `crop → scale=360:360 → 静态圆形 alpha mask`，1920×1080 坐标 `1520:680`；不稳定则改方窗。

所有固定尺寸 `scale` 都有宽高比硬约束：输入裁片必须先与目标比例一致，或显式使用 `force_original_aspect_ratio=increase/decrease` 后再 crop/pad。比如输出 1920×1080 时，禁止把 `1340×1080` 直接 `scale=1920:1080`；应先裁成 16:9（如 `1340×754`）再缩放。每个发生 crop/scale 的人像布局至少保存一组“输入原帧 + 合成帧”并排证据，确认脸宽、头身比例和圆形均未变形。仅检查输出 SAR/DAR=1:1 不足以证明内容未拉伸。

macOS CPU 完成 overlay/crop/mask，输出编码用：

```bash
-c:v h264_videotoolbox -b:v 16M -pix_fmt yuv420p
```

不要盲加输入侧 `-hwaccel videotoolbox`，CPU 滤镜会产生回传。主音频只 map 口播并 `-c:a copy`；MG 音频不进入混音。Linux/WSL 使用明确验证的软件编码参数。

所有 FFmpeg 长任务必须使用 `-nostats`，避免高频进度输出把编码拖慢。局部 cue 必须使用输入侧 `-ss/-t`，禁止从零解码完整原片后才 `trim`。每个中间段都强制 `scale=in_range=auto:out_range=tv`、BT.709 和 `yuv420p`，避免 concat 边界触发颜色范围重配置。整片包装强制 `fps=60 → tpad → trim=end_frame → setpts=N/(60*TB)`，消除逐章编码拼接造成的非单调 DTS。

## 2. 快速包装层

输出临时干净合成片后，生成 `package-props.json`：

```json
{"src":"<temporary-composite-name>","captions":[],"topics":[],"durationInFrames":0}
```

`durationInFrames = ceil(ffprobe临时合成片时长 × 30)`。保留完整包装 composition 作为视觉规格和回退入口，但默认不要让 Chromium 逐帧读取整条临时合成片。

先执行包装配置门禁：

```bash
python3 <skill-root>/scripts/validate_plan.py \
  --plan "$output_dir/mg-placement-plan.v1.json"
```

默认把 `<skill-root>/assets/remotion/Package.tsx` 作为包装基线。项目可以调整章节标题和主题色，但用户只要求变化 MG 时，不得改动章节牌结构、进度条尺寸、累计填充或字幕层级。

给包装 composition 增加 `overlayOnly` 模式：背景透明，不含 `OffthreadVideo`、字幕和动态进度填充。依次执行：

```bash
node <skill-root>/scripts/render_package_overlays.mjs \
  --project-dir "$output_dir/remotion" \
  --props "$output_dir/package-props.json" \
  --output-dir "$output_dir"

python3 <skill-root>/scripts/build_and_package.py \
  --plan "$output_dir/mg-placement-plan.v1.json" \
  --output-dir "$output_dir" \
  --speed 1.15

python3 <skill-root>/scripts/quality_gate.py \
  --plan "$output_dir/mg-placement-plan.v1.json" \
  --output-dir "$output_dir" \
  --speed 1.15
```

`render_package_overlays.mjs` 在每个章节起始帧各渲染一张透明 PNG。`build_and_package.py` 会先把 1920×1080 透明图裁成小尺寸章节 pill 和进度底轨再叠加，避免整片逐帧处理全画幅 RGBA；随后用 ASS 写字幕，并显式控制中英文混排行宽。包装成片只做一次整片视频编码，不再逐章编码、逐章拼接。

`--speed` 是最后的可选节奏项，不需要提速时省略。默认防划走提速为 `1.15`；脚本以 `atempo` 同步处理口播，以同一倍率重映射字幕、章节和进度，并通过第二次 `fps=60` 采样保持固定 60fps，不会输出 120fps。

这条路径只让 Chromium 渲染“章节数”张静帧，而不是全片数万帧。只有包装本身存在必须逐帧由 React/CSS/SVG 计算、且 FFmpeg 无法等价表达的动画时，才回退到完整 Remotion 包装。

固定 1920×1080 规格：

- 字幕：`bottom:96`，`maxWidth:68%`，字号 `max(26, height*0.049)`，700，`#f9fbff`，line-height 1.5；四正方向 `±0.035em rgba(15,23,42,.7)`、四斜角 `±0.025em rgba(15,23,42,.55)`、下方柔影。
- 章节 pill：`top:3.5%`、`left:2.2%`，深色半透明渐变、14px 圆角、5px accent 竖条；`CHAPTER i/N` 与章节标题。accent 依次为 `#8ee0ff #ffb38a #9dffc3 #c4a8ff #ffd166 #ff8ad1`。
- 进度条：固定复用稳定样片的一条连续圆角底轨，`bottom:28`、左右 46、高 30、圆角 999、`2px rgba(255,255,255,.14)` 边框、`rgba(13,18,27,.38)` 深色底；内层从整片 0 秒起累计填充 `rgba(93,220,205,.36)`。章节只在同一底轨内按时长比例分段，以 `1px rgba(255,255,255,.20)` 分隔，不得改成低于 24px 的细线、互相留缝的独立彩色胶囊、每章独立重置的填充或多套并列进度条。

进度条结构必须与标题排版解耦。`sample-classic-v1` 在轨道内显示短章节标签，但标签只能由最终 ASS 单层绘制；`Package.tsx` 只画底轨和分隔线，不得重复画标签。绘制顺序固定为“底轨 → 累计填充 → 章节 pill → ASS 标签与字幕”，因此填充不会压住文字。分段宽度只按章节时长计算；标签优先读取 `short_label`，空间不足时省略，极窄分段退回章节数字。渲染前断言 `topics` 数量等于进度条分段数量；再抽取开头、至少一个章节切换后和接近结尾三张完整底条截图，逐段确认边界、标签、总数、可见高度和累计填充方向。

静态包装 PNG 进入 FFmpeg `overlay` 时必须显式循环为输出帧率；固定脚本已经加入 `-loop 1 -framerate 60`。不得把每章开头的默认灰帧/黑帧当作正常解码延迟；最终门禁会抽取每章开头 0.5 秒内的证据帧，纯色占位连续超过 1 帧即失败。

FFmpeg 动态进度不得在 `drawbox` 的宽度表达式里把 `t` 当作时间；在 `drawbox` 中它会与 thickness 语义冲突且可能静默生成整条常亮填充。使用能按帧求值且明确提供时间变量的滤镜（例如 `scale=...:eval=frame` 的 `t`）生成动态宽度，再 overlay 到连续底轨。验收必须比较 0 秒附近、中段和结尾三帧的填充终点，要求单调向右且不在章节切换时归零。

最终包装版仍用 VideoToolbox 16M。长视频只经过一次 FFmpeg 整片包装 pass，不再增加全片 Remotion pass，也不再用逐章编码 + concat 制造时间戳风险。

## 3. 最终质量门禁

不生成预览视频。运行 `scripts/quality_gate.py` 前，必须先基于正式成片的全尺寸证据帧人工写好三份检查表（`quality_gate.py` 只认 `checks`/`items`/`invariants` 键下的记录数组，且全部记录为 `passed` 才计通过）：

- `semantic-checklist.v1.json`（阶段 2A 已写，确认证据帧仍对应最终包装成片）；
- `aspect-occlusion-checklist.v1.json`：每个发生 crop/scale 的人像布局一条记录，或（`floating-overlay` 主题）确认人像全屏底画无变换、MG 未压脸的记录；
- `package-checklist.v1.json`：章节牌可读且仅一套、30px 进度轨道肉眼可见且累计填充单调向右、字幕仅一套、章节开头无灰帧/黑帧/冻结占位。

然后使用 `scripts/quality_gate.py` 直接对正式包装成片执行下列检查，并把结果写入 `quality-report.v1.json`：

1. **结构**：用 `ffprobe` 记录正式包装成片的时长、帧率、分辨率、视频帧数、音视频轨数量；格式总时长与输入相差不得超过 0.1 秒，视频帧数差不得超过 `ceil(0.1 × 输出 fps)`，分辨率和轨道结构必须符合批准版计划。
2. **完整解码**：运行 `ffmpeg -v error -i <packaged> -f null -`，stderr 必须为空。
3. **音频来源**：未提速时分别对输入和包装版的最终音轨执行 stream MD5，两者必须完全相同；启用 `--speed` 时验证唯一音轨、目标时长和 `atempo` 证据。包装版始终只能有一条来自口播的音轨。
4. **窗口与边界**：每个 MG 窗口内至少抽 1 帧，边界前后各抽 1 帧；每章开头前 0.5 秒检查纯灰、纯黑或冻结占位帧。
5. **比例与遮挡**：把发生 crop/scale 的输入原帧和合成帧并排检查；确认人脸、圆形和 UI 未变形，关键操作无遮挡。
6. **包装**：检查开头、中段、每个章节切换后和接近结尾的全尺寸帧；章节数与进度分段数相等，章节 pill 始终可读，30px 进度轨道肉眼可见，累计填充只向右、不归零，字幕和章节牌各只有一套。不得用裁剪过小的联系表替代全尺寸检查。
7. **语义**：`semantic-checklist.v1.json` 中每条 invariant 都为 `passed`，证据帧仍对应最终包装成片。
8. **编码证据**：保存 Remotion 和 FFmpeg 完整日志；macOS 日志必须出现真实 `h264_videotoolbox` 编码器证据。
9. **交付清洁度**：`final/` 只能包含正式包装成片，不得包含 `preview`、`540p`、`clean-master`、`clean-composite` 或其他整片副本。

`quality-report.v1.json` 至少包含：

```json
{
  "schema_version": "motiontalk.quality-report.v1",
  "packaged_video": "final/<project-id>-packaged.mp4",
  "checks": {
    "structure": "passed",
    "full_decode": "passed",
    "audio_identity": "passed",
    "window_boundaries": "passed",
    "aspect_and_occlusion": "passed",
    "package_progress": "passed",
    "semantic_invariants": "passed",
    "encoder_evidence": "passed",
    "delivery_cleanliness": "passed"
  },
  "evidence": {},
  "status": "passed"
}
```

每个 `evidence` 项记录实际命令结果、日志或证据帧路径，不得只写主观结论。只有全部 `checks` 为 `passed` 且顶层 `status` 为 `passed` 才能交付；否则修复受影响环节并重新执行完整门禁。

最终只交付包装成片、批准版导演脚本与 placement plan、`quality-report.v1.json`、Remotion 源码、独立 MG、证据帧和输入 SRT；输入媒体保持不变。门禁通过后删除 `work/` 中的临时干净合成片，并再次确认 `final/` 只有一个视频文件。
