[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

把一条已经精剪好的口播视频和与它严格匹配的 SRT 交给 MotionTalk。Agent
完整理解内容后，先生成导演 Prompt；用户一次批准后，连续完成项目专属的
Remotion 制作、证据抽帧、正式渲染和质量验收。

## Prompt-first

MotionTalk 不附带一套沉重的 Remotion 模板，也不把构图、尺寸、进度条高度、
字体比例或动画写成全局代码模式。

人物全屏叠加 MG、全屏 MG 配人物窗、人物与录屏切换，都只是导演 Prompt 可选
的表达方式。每个项目只实现自己批准的画面，不预建另外两套分支。

```text
精剪视频 + 最终 SRT
  → Agent 生成导演 Prompt 与语义验收点
  → 用户一次批准
  → 项目专属 Remotion 工程
  → 正式渲染 + renderStill 证据 + 质量门禁
  → 最终包装成片
```

MotionTalk 不做 ASR、不删口误或停顿，也不重新剪辑。输入视频始终是时间线、
语义和最终音频的唯一依据。

## 安装

```bash
npx skills add PoetCoderJun/MotionTalk
```

## 使用

```text
使用 $motiontalk 处理：
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

导演脚本批准是全流程唯一一次打断。分辨率、帧率、字幕、章节、进度、布局、
安全区和动画都在该项目的草案中一次冻结。

## 确定性薄层

- `validate_plan.py`：验证批准状态、项目 render spec、完整 cue 时间线、视觉
  Prompt 和语义验收点；
- `render_master.mjs`：通过 Remotion 官方入口正式渲染并抽帧；默认使用 75%
  的可用并发，从项目依赖加载 Remotion 并使用 Remotion 自管浏览器，在硬件
  编码不可用时保持跨平台回退；
- `validate_master.mjs`：按项目 render spec 和批准的证据清单验收成片。

## 渲染性能

默认命令适用于 macOS、Windows 和 Linux：并发为 `75%`，硬件编码策略为
`if-possible`。设备或执行环境无法访问硬件编码器时会自动使用软件编码，不把
任何平台专属编码器作为安装或交付前提。

渲染入口使用项目本机安装的 `@remotion/bundler` 与 `@remotion/renderer`，并由
Remotion 自管与当前版本匹配的 Headless Shell。首次运行可能自动下载兼容版本；
不要传入系统 Chrome 路径，也不要把浏览器版本管理交给外部 Chrome。

## 可复用主题

`PPT Focus Portrait` 是一套 Prompt 主题参考：PPT 位于画面视觉中心偏上，字幕
紧接 PPT 且严格最多两行，人物位于右下，左下使用轻量花字或结论，底部保留章节
进度。它保存比例和验收规则，不提供固定 Remotion 模板。详见
[`references/04-theme-ppt-focus-portrait.md`](references/04-theme-ppt-focus-portrait.md)。

### macOS 性能建议（可选）

Apple Silicon 用户可以先确认 FFmpeg 是否能看到 VideoToolbox：

```bash
ffmpeg -hide_banner -encoders | grep h264_videotoolbox
```

确认当前终端有权访问系统编码服务后，可选择强制硬件编码并设置码率：

```bash
node scripts/render_master.mjs \
  --project-dir "$output_dir/remotion" \
  --props "$output_dir/master-props.json" \
  --output "$output_dir/final/video-packaged.mp4" \
  --concurrency 75% \
  --offthread-video-threads 4 \
  --hardware-acceleration required \
  --video-bitrate 16M
```

`required` 只适合已经验证硬件编码器与权限的 macOS 环境。其他平台、受限沙箱
或未完成预检的机器应保留默认 `if-possible`，不要照搬这组可选参数。

## 开发验证

```bash
python3 -m unittest discover -s tests -v
node scripts/render_master.mjs --help
node scripts/validate_master.mjs --help
```

## 许可

仓库原创内容采用 [CC BY-NC-SA 4.0](LICENSE.md)，仅限非商业使用；商业使用需
另行获得书面许可。
