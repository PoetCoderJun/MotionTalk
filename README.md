[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

把一条已经精剪好的口播视频和与它严格匹配的 SRT 交给 MotionTalk。Agent
完整理解内容后，先生成导演 Prompt；用户一次批准后，连续完成项目专属的
Remotion 制作、证据抽帧、正式渲染和质量验收。

## 参考主题

下面四个效果是独立参考 Prompt 中提供的起点。点名其中一个，可以
**快速生成相似视频**；它们不是四选一，也不是 MotionTalk 的能力边界。实际想要
什么布局、字幕、人物、录屏或动画效果，都可以直接用自然语言和 AI 说。以下均为
真实交付样片。

<table>
  <tr>
    <td width="50%"><img src="assets/readme/theme-floating-overlay.webp" alt="人物全屏与悬浮 MG 样片"><br><strong>1. floating-overlay</strong><br><sub>人物或录屏全屏常驻，MG 只在安全区做轻量强调。</sub></td>
    <td width="50%"><img src="assets/readme/theme-presenter-window.webp" alt="全屏 MG 与人物窗样片"><br><strong>2. mg-with-presenter-window</strong><br><sub>MG、截图或录屏成为主画面，人物以圆窗或方窗陪伴。</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="assets/readme/theme-switching.webp" alt="人物与录屏切换样片"><br><strong>3. switching</strong><br><sub>人物、全屏 MG 与录屏按内容切换，各自获得完整阅读空间。</sub></td>
    <td width="50%"><img src="assets/readme/theme-ppt-focus-portrait.webp" alt="竖屏 PPT 主视觉样片"><br><strong>4. PPT Focus Portrait</strong><br><sub>竖屏 PPT 主视觉，PPT 下自适应双行字幕，右下人物与底部进度。</sub></td>
  </tr>
</table>

四个效果的参考指引统一放在
[`references/04-reference-theme-prompt.md`](references/04-reference-theme-prompt.md)。
它只帮助 AI 快速理解方向；最终导演计划仍由当前素材和自然语言要求决定。

## 核心能力

- **内容驱动的导演 Prompt**：先完整理解口播与字幕，再为当前项目决定构图、
  动画、录屏/PPT 出场时机和语义高亮，不套固定模板；
- **一次批准，连续交付**：导演计划确认后，不再反复打断，连续完成工程、证据
  抽帧、正式成片和质量验收；
- **单一主合成**：一个 `MasterComposition` 完成画面包装，源视频音频是唯一
  音轨，避免重复人声、漂移和多时间线；
- **本机 Remotion 高效渲染**：使用项目安装的 Remotion、版本匹配的自管
  Headless Shell 和默认 `75%` 并发；硬件编码可用时启用，不可用时跨平台回退；
- **语义级质量门禁**：按批准的论点与禁区抽取证据帧，并重点检查最长字幕、
  安全区、布局和最终媒体参数；
- **参考主题 Prompt**：用四个真实效果快速对齐方向，也可以完全跳过主题，直接
  用自然语言设计当前项目。

## Prompt-first

MotionTalk 不附带一套沉重的 Remotion 模板，也不把构图、尺寸、进度条高度、
字体比例或动画写成全局代码模式。

人物全屏叠加 MG、全屏 MG 配人物窗、人物与录屏切换，都只是导演 Prompt 可选
的表达方式。每个项目只实现自己批准的画面，不预建其他主题分支。

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

## 开发验证

```bash
python3 -m unittest discover -s tests -v
node scripts/render_master.mjs --help
node scripts/validate_master.mjs --help
```

## 许可

仓库原创内容采用 [CC BY-NC-SA 4.0](LICENSE.md)，仅限非商业使用；商业使用需
另行获得书面许可。
