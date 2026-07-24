[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

输入一条已经精剪好的口播自拍视频和匹配字幕；如果你同时录了讲解操作，也可以再上传一条从 `00:00` 同步的录屏。MotionTalk 会自动判断什么时候保留你本人、什么时候切到真实操作、什么时候用 MG 把抽象概念讲清楚，最后生成一条带章节、字幕、进度条和任务蒙版的“百万博主同款” fancy 动画视频。

![MotionTalk：从 talking video 到完整 MG 成片](assets/readme/motiontalk-cover.png)

## 一套 Skill，完成画面判断与制作

- 需要建立信任和保持人物表达时，保留讲述者。
- 抽象概念需要看懂时，加入 MG 动画。
- 真实操作更重要时，切换到同步录屏。
- 最终交付带章节、字幕、进度条、任务蒙版和视觉包装的完整成片。

你不需要先写分镜，也不需要指定每一个特效。MotionTalk 会读完整条内容，根据语义和真实操作判断画面应该留在人、切到屏幕，还是交给 MG。

## 输入 → 输出

| 输入 | 必需 | 说明 |
| --- | --- | --- |
| 精剪 talking video | 是 | 唯一时间线、语义和最终音频依据 |
| 最终 SRT | 是 | 必须与精剪视频时间线完全匹配 |
| 同步录屏 | 否 | 从 `00:00` 开始、与 talking video 等长 |

输出是一条完成字幕与视觉包装的成片。MotionTalk 不做 ASR、不删口误或停顿，也不重新剪辑。

## 两种模式

### 单视频：talking video ↔ MG

适合知识分享、观点表达、课程讲解和访谈切片。MotionTalk 在原始 talking video 与 MG 之间安排节奏，不需要录屏。

### 双视频：talking video ↔ 录屏 ↔ MG

适合软件教程、产品演示和工作流拆解。MotionTalk 会优先保护真实操作，再决定何时回到讲述者、何时用 MG 解释抽象关系。

## 完整成片画面

下面四张图均保留完整视频画面，没有裁掉章节、字幕、进度条、任务蒙版、人物或播放器状态。

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

只有 talking video：

```text
使用 $motiontalk 处理：
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

同时有同步录屏：

```text
使用 $motiontalk 处理：
- video: /data/talking-video.mp4
- screen_video: /data/screen-recording.mp4
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

## 仓库边界

本仓库只分发 Skill 说明与展示素材，不携带 JavaScript、TypeScript、Python 或 Shell 执行代码。制作过程中需要的 Remotion 工程和临时批量渲染入口只创建在用户指定的 `output_dir` 内。
