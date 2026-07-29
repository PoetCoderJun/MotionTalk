[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

把一条已经精剪好的口播视频和与它严格匹配的 SRT 交给 MotionTalk。它会判断什么时候保留讲述者、什么时候用 MG 把抽象概念讲清楚，并交付带章节牌、字幕、累计进度条和完整视觉包装的成片。

它做的不是随机堆特效，而是把画面判断、MG 制作、整片包装和质量验收收进一条可重复执行的 Agent Skill 链路。

## 从精剪口播到包装成片

```text
精剪口播视频 + 最终 SRT
  → Agent 阅读完整内容并生成导演脚本
  → 用户一次批准
  → 正式 MG → 整片合成 → 包装 → 质量门禁
  → 只交付最终包装成片
```

导演脚本批准是全流程唯一一次打断。画面主题、字幕关键词强调、节奏、布局和遮挡策略都会写进同一份草案；批准后连续制作与交付，不再要求第二次“继续”确认。

## 输入 → 输出

| 输入 | 必需 | 说明 |
| --- | --- | --- |
| 精剪 talking video | 是 | 唯一时间线、语义和最终音频依据 |
| 最终 SRT | 是 | 必须与精剪视频时间线完全匹配 |

输出是一条完成字幕、章节与视觉包装的成片。MotionTalk 不做 ASR、不删口误或停顿，也不重新剪辑；口播视频始终是时间线、语义和最终音频的唯一依据。

如果你只有原始口播，可以先用 [**clean-talking-video**](https://github.com/PoetCoderJun/clean-talking-video) 生成精剪视频和精准 SRT，再把这两个结果交给 MotionTalk。

## 三种画面构成主题

每个项目只选择一种主题，并随导演脚本一起批准：

- **floating-overlay**：人物全屏常驻，MG 悬浮在安全区，不替换人物、不做蒙版；
- **mg-with-presenter-window**：全屏 MG + 右下角圆窗或方窗人物，默认主题；
- **switching**：人物、MG 和可选录屏按内容切换，适合课程或产品讲解。

主题只决定人物与 MG 的关系。章节牌、30px 连续累计进度轨道和单套字幕属于不可省略的包装层，不会因为更换 MG 风格而被弱化或删除。

## 完整成片画面

下面四张图均保留完整视频画面，没有裁掉章节、字幕、进度条、人物或播放器状态。

<p align="center">
  <img src="assets/readme/cover-source/01-talking-video.png" alt="完整画面：talking video、章节、字幕与进度条" width="49%">
  <img src="assets/readme/cover-source/02-agent-execution.png" alt="完整画面：Agent 执行、任务蒙版、字幕与进度条" width="49%">
  <img src="assets/readme/cover-source/03-motion-graphics.png" alt="完整画面：MG、章节、字幕、人物与进度条" width="49%">
  <img src="assets/readme/cover-source/04-packaged-video.png" alt="完整画面：包装成片、章节、字幕、人物与进度条" width="49%">
</p>

## 安装

使用通用 Skills CLI：

```bash
npx skills add PoetCoderJun/MotionTalk
```

也可以把仓库地址直接交给 Codex、Kimi 或其他支持 Skills 的 Agent：

```text
请帮我安装 MotionTalk：
https://github.com/PoetCoderJun/MotionTalk
```

## 使用

使用方式：

```text
使用 $motiontalk 处理：
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

### 还没有 SRT？

请先使用独立语音转写能力，为精剪 talking video 生成并校验最终 SRT，再运行 MotionTalk。

```text
我还没有 SRT。
请先使用你可用的独立 AI 语音转写能力，
为 /data/talking-video.mp4 生成与视频时间线匹配的 /data/final.srt。
完成并校验字幕后，再使用 $motiontalk 处理：
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

## 高效执行链路

本仓库随 Skill 分发固定执行入口：

- `validate_plan.py`：验证批准状态、语义约束、画面主题和包装契约；
- `render_segments.mjs`：一次 bundle、一次 browser，批量渲染正式 MG；
- `render_package_overlays.mjs`：渲染章节透明覆盖层；
- `build_and_package.py`：互斥 cue 合成与单次整片包装；
- `quality_gate.py`：完整解码、音频同源、证据帧和包装可见性门禁。

最终输出固定为 60fps。需要时可在唯一一次整片包装中统一 1.15× 提速，视频、主音频、字幕、章节和进度条会一起重映射。

## 质量门禁

MotionTalk 不把“FFmpeg 成功”当成交付完成。正式成片必须通过：

- 每条 MG 语义约束都有对应证据帧；
- 人像裁切前后比例一致，MG 不遮挡人脸；
- 章节牌、30px 进度条和单套字幕在全尺寸证据帧中肉眼可见；
- 主音频只来自输入视频，完整解码和时间线检查通过；
- `quality-report.v1.json` 的所有必检项均为 `passed`。

## 开发与验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/test_build_and_package.py
```

## 许可

仓库原创内容采用 [CC BY-NC-SA 4.0](LICENSE.md)，仅限非商业使用；商业使用需另行获得书面许可。
