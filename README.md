# producing-talking-head-video-mg

为已经精剪完成的口播视频添加字幕驱动的 MG 动画，并输出可交付成片。

## 使用场景

支持两种模式：

- **单视频模式**：口播视频 + 最终 SRT；
- **双视频模式**：口播视频 + 与其同步且等长的录屏 + 最终 SRT。

适合需要在口播原画面、录屏和 MG 之间自动规划切换，并保留说话者人像圆窗的访谈、讲解、教程和知识类视频。

## 成片示例

<p align="center">
  <img src="assets/readme/l00-mg-workbench.jpg" alt="L00 成片：口播人像圆窗与工作台 MG" width="49%">
  <img src="assets/readme/l00-mg-harness.jpg" alt="L00 成片：口播人像圆窗与 Harness MG" width="49%">
</p>

## 安装

把下面的 GitHub 地址直接发给 Kimi、Codex 或其他支持 Skills 的 Agent，让它代为安装：

```text
请帮我安装这个 Skill：
https://github.com/PoetCoderJun/producing-talking-head-video-mg
```

## 使用方法

单视频模式：

```text
使用 $producing-talking-head-video-mg 处理：
- video: /data/talking-head.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

双视频模式：

```text
使用 $producing-talking-head-video-mg 处理：
- video: /data/talking-head.mp4
- screen_video: /data/screen-recording.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

输入视频必须已经精剪完成，SRT 必须与最终视频时间线一致。双视频模式下，录屏必须从 `00:00` 与口播视频同步且等长。
