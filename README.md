[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

把精剪口播自动升级成带 MG 动画、字幕包装和录屏切换的成片。它是一套 Agent Skill；安装后的兼容调用名仍是 `$talking-mg-video`。

<p align="center">
  <img src="assets/readme/motiontalk-before-after.svg" alt="同一句口播的原始相机画面与 MotionTalk MG 成片对照" width="100%">
</p>

<p align="center"><sub>真实同时间轴对照：左侧为原始口播，右侧为 MotionTalk 成片。</sub></p>

## 一套 Skill，完成画面判断与制作

- 需要建立信任和保持人物表达时，保留讲述者。
- 抽象概念需要看懂时，加入 MG 动画。
- 真实操作更重要时，切换到同步录屏。
- 最终交付带字幕与视觉包装的完整成片。

你不需要先写分镜，也不需要指定每一个特效。MotionTalk 会读完整条内容，根据语义和真实操作判断画面应该留在人、切到屏幕，还是交给 MG。

## 输入 → 输出

| 输入 | 必需 | 说明 |
| --- | --- | --- |
| 精剪口播视频 | 是 | 唯一时间线、语义和最终音频依据 |
| 最终 SRT | 是 | 必须与精剪视频时间线完全匹配 |
| 同步录屏 | 否 | 从 `00:00` 开始、与口播等长 |

输出是一条完成字幕与视觉包装的成片。MotionTalk 不做 ASR、不删口误或停顿，也不重新剪辑。

## 两种模式

### 单视频：口播 ↔ MG

适合知识分享、观点表达、课程讲解和访谈切片。MotionTalk 在原始口播与 MG 之间安排节奏，不需要录屏。

### 双视频：口播 ↔ 录屏 ↔ MG

适合软件教程、产品演示和工作流拆解。MotionTalk 会优先保护真实操作，再决定何时回到讲述者、何时用 MG 解释抽象关系。

## 安装

使用通用 Skills CLI：

```bash
npx skills add PoetCoderJun/talking-mg-video
```

也可以把仓库地址直接交给 Codex、Kimi 或其他支持 Skills 的 Agent：

```text
请帮我安装 MotionTalk：
https://github.com/PoetCoderJun/talking-mg-video
```

## 使用

只有口播视频：

```text
使用 $talking-mg-video 处理：
- video: /data/talking-head.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

同时有同步录屏：

```text
使用 $talking-mg-video 处理：
- video: /data/talking-head.mp4
- screen_video: /data/screen-recording.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

### 还没有 SRT？

请先使用独立语音转写能力，为精剪视频生成并校验最终 SRT，再运行 MotionTalk。输入视频仍需已经精剪完成。

## 更多成片画面

<p align="center">
  <img src="assets/readme/l00-mg-workbench.jpg" alt="口播人像圆窗与工作台 MG" width="49%">
  <img src="assets/readme/l00-mg-harness.jpg" alt="口播人像圆窗与 Harness MG" width="49%">
</p>
