# talking-mg-video

## 一条自拍口播，自动升级成“像请了导演 + MG 动效师”的成片

> 你负责把话说清楚，AI 负责让画面变得更抓人。

把精剪完成的口播视频交给 `talking-mg-video`，AI 会听懂整段内容、找出最值得视觉化的观点、生成 MG 分镜，再把字幕、动画、人像和录屏编排成可交付成片。

## 使用场景

### 普通模式：一支自拍口播，也能拥有 MG 分镜

适合知识分享、观点表达、课程讲解、访谈切片等已经精剪完成的自拍口播视频。AI 根据每段口播的含义设计对应的 MG 分镜动画，并在“自拍原画面 ↔ MG”之间安排节奏，不需要另外准备录屏。

### 双视频模式：录屏 + 自拍 + MG，自动丝滑切镜

适合软件教程、产品演示、工作流拆解和带操作过程的课程视频。提供从 `00:00` 同步且等长的录屏与自拍口播后，AI 会判断什么时候应该看真实操作、什么时候应该回到讲述者、什么时候应该用 MG 解释抽象关系，并在“录屏 ↔ 自拍 ↔ MG”之间自动规划切换。

两种模式都必须输入与精剪视频时间线匹配的最终 SRT。

## 成片示例

<p align="center">
  <img src="assets/readme/l00-mg-workbench.jpg" alt="L00 成片：口播人像圆窗与工作台 MG" width="49%">
  <img src="assets/readme/l00-mg-harness.jpg" alt="L00 成片：口播人像圆窗与 Harness MG" width="49%">
</p>

## 安装

把下面的 GitHub 地址直接发给 Kimi、Codex 或其他支持 Skills 的 Agent，让它代为安装：

```text
请帮我安装这个 Skill：
https://github.com/PoetCoderJun/talking-mg-video
```

## 使用方法

普通模式：

```text
使用 $talking-mg-video 处理：
- video: /data/talking-head.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

双视频模式：

```text
使用 $talking-mg-video 处理：
- video: /data/talking-head.mp4
- screen_video: /data/screen-recording.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

只有一支自拍视频，就使用普通模式；如果同时拍了录屏和自拍，就使用双视频模式，让 AI 在录屏、自拍和 MG 动画之间自动规划丝滑切换。

### 没有 SRT 怎么办？

`talking-mg-video` 必须输入最终 SRT，而且这个 Skill 本身不包含 ASR 或 SRT 制作能力。如果没有 SRT，先让 AI 使用独立的语音转写能力为精剪视频生成对应的 SRT；生成并校验完成后，再把 SRT 路径传给本 Skill 开始制作 MG。

可以直接这样告诉 AI：

```text
我还没有 SRT。
请先使用你可用的独立 AI 语音转写能力，
为 /data/talking-head.mp4 生成与视频时间线匹配的 /data/final.srt。
完成并校验字幕后，再使用 $talking-mg-video 处理：
- video: /data/talking-head.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

输入口播视频必须已经精剪完成；本 Skill 不负责删除口误、停顿或重新剪辑。提供的 SRT 必须与最终视频时间线一致。双视频模式下，录屏必须从 `00:00` 与口播视频同步且等长。
