# 阶段 3：正式渲染、合成、包装、验收

前提：正式 MG 片段已渲染并通过抽帧检查。

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
- 进度条：`bottom:28`、左右 46、高 30、圆角 999；按章节时长分段，窄于 `标题字数×18+24` 时隐藏标签；底层整体进度色 `rgba(93,220,205,.36)`。

进度条结构必须与标题排版解耦。章节标题再长也不得删除、合并或跳过任何进度条分段；分段宽度只按章节时长计算，不得由标签文字的最小宽度决定。空间不足时不得隐藏整个标签：依次使用专门的短标题、单行省略号、章节编号，确保每段都有可见标识。渲染前断言 `topics` 数量等于进度条分段数量；再抽取一张完整底条截图，逐段确认边界、标识和总数，不能只检查当前章节高亮。

最终包装版仍用 VideoToolbox 16M。长视频只经过一次按章 FFmpeg 包装 pass，不再增加全片 Remotion pass。

## 3. 验收

1. 包装前用 `ffprobe` 确认临时干净合成片与输入时长一致，帧率、分辨率、音轨正确。
2. 对包装版执行 `ffprobe` 和 `ffmpeg -v error -i <file> -f null -`：时长与输入一致，帧率、分辨率、音轨正确，完整解码无错误。
3. 每个 MG/录屏窗口内至少抽 1 帧，边界前后抽帧，纯人像段抽帧；确认无黑帧、圆窗正确、切换干净、包装只有一套。
4. 音频全程连续且只来自口播；双视频确认录屏同步、无录屏音频、关键操作无遮挡。
5. 保存 Remotion 和 FFmpeg 完整日志。FFprobe 只显示 H.264 不能证明硬编；日志必须出现真实编码器证据。

最终视频只交付包装版。另交付批准版导演脚本与 placement plan、Remotion 源码、独立 MG、连续预览和输入 SRT；输入媒体保持不变。包装版验收通过后删除 `work/` 中的临时干净合成片，并确认 `final/` 中不存在 `clean-master`、`clean-composite` 或其他未包装的全片视频。
