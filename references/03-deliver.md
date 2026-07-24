# 阶段 3：正式渲染、合成、包装、验收

前提：正式 MG 片段已渲染，画面检查表和 `semantic-checklist.v1.json` 全部通过。

## 1. 合成架构：保留短 MG + FFmpeg 临时干净合成片

**不要为了“统一”改成全 Remotion。** VideoToolbox只加速编码；Remotion 仍需 Chromium 抓取每一帧。包装成片只需一次全片浏览器渲染就会非常慢，因此默认使用短 MG + FFmpeg 的混合架构。

默认混合架构：

1. Remotion 只绘制真正有动画的短 MG cue；
2. FFmpeg 在 `output_dir/work/` 一次生成临时干净合成片，并从口播视频复制主音频；
3. Remotion 一次生成每章一张透明包装静帧；
4. FFmpeg 按章节给临时干净合成片叠加静态包装、动态进度条和字幕，再无损拼接章节并复制主音频；
5. 包装版完整验收通过后，删除临时干净合成片。不得把它移入 `final/`、列入交付清单或以“备份”为由长期保留。

FFmpeg 合成不得把 1920×1080 底片转为整片 RGBA，也不得让每帧串行穿过所有 cue 的 overlay 链。按完整时间线切成互斥 segment：

- 纯人像段：直接 trim；
- MG 段：当前人像底 + 当前 MG + 人像圆窗；
- 录屏段：当前人像底 + 当前录屏 + 人像圆窗；
- 每个局部 segment 用同一硬编参数输出；再用 concat demuxer `-c copy` 拼回完整时间线，最后以 `-c copy` 封入口播原音频。

这样每帧最多只经过当前 segment 的 1–2 次 overlay。底片和录屏保持 `yuv420p`；只有需要 alpha fade 的 MG 转 `yuva420p`。相邻 MG 窗口硬切；非相邻 MG 首尾可用约 8 帧 alpha fade 回到人像底。录屏从零点同步，按相同时间窗 trim，禁止平移整条录屏。

**合成陷阱（L03 实测，两个都静默失败、ffmpeg 退出码为 0）：**

- 不要在整条录屏/底片流上串接多组 fade 来圈多个窗口：`fade=in` 会把 st 之前所有帧的 alpha 强制为 0，`fade=out` 会把 st+d 之后所有帧强制为 0，串联后所有窗口的 alpha 全部归零，overlay 看似"没生效"。fade 只用于从 0 开始的短 MG 片段首尾（窗口局部时间，因此安全）。
- 不要把同一个滤镜标签（如 `[scr]`）作为多路 overlay 的第二输入：实测只有第一路 overlay 生效，其余窗口静默漏出底片。每路 overlay 用一条独立分支，显式 `split=N`。
- 这两个 bug 用 ffprobe 和退出码都查不出来；无论用哪种合成架构，每个录屏/MG 窗口都必须至少抽 1 帧全尺寸目检才算数。

人像圆窗先抽至少 3 帧确认脸位。稳定时 `crop → scale=360:360 → 静态圆形 alpha mask`，1920×1080 坐标 `1520:680`；不稳定则改方窗。非 16:9 录屏裁为 16:9，抽帧确认关键 UI 不被切。

所有固定尺寸 `scale` 都有宽高比硬约束：输入裁片必须先与目标比例一致，或显式使用 `force_original_aspect_ratio=increase/decrease` 后再 crop/pad。比如输出 1920×1080 时，禁止把 `1340×1080` 直接 `scale=1920:1080`；应先裁成 16:9（如 `1340×754`）再缩放。每个发生 crop/scale 的人像布局至少保存一组“输入原帧 + 合成帧”并排证据，确认脸宽、头身比例和圆形均未变形。仅检查输出 SAR/DAR=1:1 不足以证明内容未拉伸。

macOS CPU 完成 overlay/crop/mask，输出编码用：

```bash
-c:v h264_videotoolbox -b:v 16M -pix_fmt yuv420p
```

不要盲加输入侧 `-hwaccel videotoolbox`，CPU 滤镜会产生回传。主音频只 map 口播并 `-c:a copy`；录屏与 MG 音频不进入混音。Linux/WSL 使用明确验证的软件编码参数。

## 2. 快速包装层

输出临时干净合成片后，生成 `package-props.json`：

```json
{"src":"<temporary-composite-name>","captions":[],"topics":[],"durationInFrames":0}
```

`durationInFrames = ceil(ffprobe临时合成片时长 × 30)`。保留完整包装 composition 作为视觉规格和回退入口，但默认不要让 Chromium 逐帧读取整条临时合成片。

给包装 composition 增加 `overlayOnly` 模式：背景透明，不含 `OffthreadVideo`、字幕和动态进度填充。一次 bundle、一次 browser，在每个章节起始帧各渲染一张透明 PNG。FFmpeg 对每章执行：

1. 叠加该章 PNG 中固定的章节 pill、分段底条和其他静态 chrome；
2. 用时间表达式绘制当前章节的动态进度填充；
3. 用 ASS 写字幕，并显式控制中英文混排行宽，不能依赖播放器自动换行；
4. 每章以同一 VideoToolbox 参数编码，concat demuxer `-c copy` 拼接；
5. 从临时干净合成片 `-c:a copy` 封入原音频。

这条路径只让 Chromium 渲染“章节数”张静帧，而不是全片数万帧。只有包装本身存在必须逐帧由 React/CSS/SVG 计算、且 FFmpeg 无法等价表达的动画时，才回退到完整 Remotion 包装。

固定 1920×1080 规格：

- 字幕：`bottom:96`，`maxWidth:68%`，字号 `max(26, height*0.049)`，700，`#f9fbff`，line-height 1.5；四正方向 `±0.035em rgba(15,23,42,.7)`、四斜角 `±0.025em rgba(15,23,42,.55)`、下方柔影。
- 章节 pill：`top:3.5%`、`left:2.2%`，深色半透明渐变、14px 圆角、5px accent 竖条；`CHAPTER i/N` 与章节标题。accent 依次为 `#8ee0ff #ffb38a #9dffc3 #c4a8ff #ffd166 #ff8ad1`。
- 进度条：固定复用稳定样片的一条连续圆角底轨，`bottom:28`、左右 46、高 30、圆角 999、`2px rgba(255,255,255,.14)` 边框、`rgba(13,18,27,.38)` 深色底；底层从整片 0 秒起累计填充 `rgba(93,220,205,.36)`。章节只在同一底轨内按时长比例分段，以 `1px rgba(255,255,255,.10)` 分隔，不得改成互相留缝的独立彩色胶囊、每章独立重置的填充或多套并列进度条。

进度条结构必须与标题排版解耦。章节标题再长也不得删除、合并或跳过任何进度条分段；分段宽度只按章节时长计算，不得由标签文字的最小宽度决定。空间不足时依次使用专门的短标题、单行省略号、章节编号，确保每段都有可见标识。渲染前断言 `topics` 数量等于进度条分段数量；再抽取开头、至少一个章节切换后和接近结尾三张完整底条截图，逐段确认边界、标识、总数和累计填充方向，不能只检查当前章节高亮。

静态包装 PNG 进入 FFmpeg `overlay` 时必须显式循环为输出帧率（例如 `-loop 1 -framerate 60 -i chapter.png`），或在滤镜中验证首帧立即可用。不得把每章开头的默认灰帧/黑帧当作正常解码延迟；逐章输出后检查每个 part 的前 0.5 秒，纯色占位连续超过 1 帧即失败。

FFmpeg 动态进度不得在 `drawbox` 的宽度表达式里把 `t` 当作时间；在 `drawbox` 中它会与 thickness 语义冲突且可能静默生成整条常亮填充。使用能按帧求值且明确提供时间变量的滤镜（例如 `scale=...:eval=frame` 的 `t`）生成动态宽度，再 overlay 到连续底轨。验收必须比较 0 秒附近、中段和结尾三帧的填充终点，要求单调向右且不在章节切换时归零。

最终包装版仍用 VideoToolbox 16M。长视频只经过一次按章 FFmpeg 包装 pass，不再增加全片 Remotion pass。

## 3. 最终质量门禁

不生成预览视频。直接对正式包装成片执行下列检查，并把结果写入 `quality-report.v1.json`：

1. **结构**：用 `ffprobe` 记录正式包装成片的时长、帧率、分辨率、视频帧数、音视频轨数量；格式总时长与输入相差不得超过 0.1 秒，视频帧数差不得超过 `ceil(0.1 × 输出 fps)`，分辨率和轨道结构必须符合批准版计划。
2. **完整解码**：运行 `ffmpeg -v error -i <packaged> -f null -`，stderr 必须为空。
3. **音频来源**：分别对输入和包装版的最终音轨执行 stream MD5；两者必须完全相同，且包装版只能有一条来自口播的音轨。
4. **窗口与边界**：每个 MG/录屏窗口内至少抽 1 帧，边界前后各抽 1 帧；每章开头前 0.5 秒检查纯灰、纯黑或冻结占位帧。
5. **比例与遮挡**：把发生 crop/scale 的输入原帧和合成帧并排检查；确认人脸、圆形和 UI 未变形，关键操作无遮挡。
6. **包装**：检查开头、中段、章节切换后和接近结尾的全尺寸帧；章节数与进度分段数相等，累计填充只向右、不归零，字幕和章节牌各只有一套。
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
