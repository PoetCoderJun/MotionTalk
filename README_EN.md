[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

Turn an edited talking video into a polished motion-graphics video with one Agent Skill.

![MotionTalk: talking video to packaged motion graphics](assets/readme/motiontalk-cover.png)

- Keeps the presenter when human presence matters
- Adds MG when concepts need visualization
- Switches to synchronized screen recordings for real operations
- Delivers a fully captioned and packaged final video

Give the edited talking video and its matching subtitles to `motiontalk`. The Agent reads the full content, decides when to keep the presenter, when motion graphics explain an idea better, and—when a screen recording is available—when to show the real interface. You do not need to prepare a storyboard or specify every effect.

## Use cases

### Standard mode: one selfie video with content-aware MG storyboards

Use this mode for already-edited talking videos such as knowledge sharing, opinion pieces, course explainers, and interview clips. AI designs motion-graphics scenes from the meaning of each passage and controls the rhythm between the original talking video and MG animation. No screen recording is required.

### Dual-video mode: smooth switching between screen recording, selfie, and MG

Use this mode for software tutorials, product demos, workflow breakdowns, and lessons that include on-screen operations. Provide an equal-length screen recording and talking video synchronized from `00:00`. AI decides when viewers should see the real operation, return to the presenter, or switch to MG for an abstract explanation, then plans the transitions between all three sources.

Both modes require a final SRT that matches the timeline of the edited video.

The only final video deliverable is the fully captioned and packaged cut. Any clean composite needed during production remains a temporary working file and is deleted after the packaged cut passes validation.

## Example frames

<p align="center">
  <img src="assets/readme/cover-source/01-talking-video.png" alt="Complete frame: talking video, chapter, captions, and progress bar" width="49%">
  <img src="assets/readme/cover-source/02-agent-execution.png" alt="Complete frame: Agent execution, task mask, captions, and progress bar" width="49%">
  <img src="assets/readme/cover-source/03-motion-graphics.png" alt="Complete frame: MG, chapter, captions, presenter, and progress bar" width="49%">
  <img src="assets/readme/cover-source/04-packaged-video.png" alt="Complete frame: packaged video, chapter, captions, presenter, and progress bar" width="49%">
</p>

## Installation

Send the following GitHub URL to Codex, Kimi, or another Agent that supports Skills:

```text
Please install this Skill:
https://github.com/PoetCoderJun/MotionTalk
```

## Usage

Standard mode:

```text
Use $motiontalk with:
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

Dual-video mode:

```text
Use $motiontalk with:
- video: /data/talking-video.mp4
- screen_video: /data/screen-recording.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

Use standard mode when you only have a talking video. If you recorded both your screen and yourself, use dual-video mode so AI can plan smooth switching between the screen recording, talking video, and MG animation.

### What if I do not have an SRT?

`motiontalk` requires a final SRT. This Skill does not include ASR or subtitle-generation capabilities. If you do not have an SRT, first ask AI to use an independent speech-transcription capability to generate one that matches the edited video. After the subtitles have been generated and verified, pass the SRT path to this Skill.

You can tell the Agent:

```text
I do not have an SRT yet.
First use an available independent AI transcription capability
to generate /data/final.srt for /data/talking-video.mp4.
Verify that it matches the video timeline, then use $motiontalk with:
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

The talking video must already be fully edited; this Skill does not remove mistakes, pauses, or repeated takes. The SRT must match the final video timeline. In dual-video mode, the screen recording must be equal in length and synchronized with the talking video from `00:00`.
