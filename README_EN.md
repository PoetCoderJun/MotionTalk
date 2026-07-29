[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

Give MotionTalk one edited talking video and an SRT that matches it exactly. It decides when to keep the presenter on screen, when motion graphics can make an abstract idea clearer, and delivers a final video with chapter headers, captions, cumulative progress, and complete visual packaging.

It is not a random effect generator. MotionTalk packages visual direction, motion-graphics production, full-video packaging, and evidence-based quality control into one repeatable Agent Skill.

## From edited talk to packaged video

```text
Edited talking video + final SRT
  → Agent reads the full piece and drafts a director plan
  → One user approval
  → Final MG → composite → packaging → quality gates
  → Deliver only the final packaged video
```

The director-plan approval is the only interruption in the workflow. Visual theme, caption highlights, pacing, layout, and occlusion strategy are proposed in that single draft. After approval, MotionTalk builds and delivers continuously without asking for another “continue” confirmation.

## Input → output

| Input | Required | Contract |
| --- | --- | --- |
| Edited talking video | Yes | The only source of timeline, meaning, and final audio |
| Final SRT | Yes | Must match the edited video timeline exactly |

The output is a fully captioned and visually packaged final video. MotionTalk does not run ASR, remove mistakes or pauses, or recut the source video. The talking video remains the only source of timeline, meaning, and final audio.

If you only have a raw recording, run [**clean-talking-video**](https://github.com/PoetCoderJun/clean-talking-video) first to produce an edited video and a timeline-accurate SRT, then pass both outputs to MotionTalk.

## Three visual-composition themes

Each project selects one theme and freezes it in the approved director plan:

- **floating-overlay**: the presenter stays full-screen while MG floats inside measured safe zones—no replacement or presenter mask;
- **mg-with-presenter-window**: full-screen MG with the presenter in a lower-right circle or rectangle; this is the default;
- **switching**: presenter, MG, and optional screen recording switch by content, useful for courses and product explainers.

Themes control the relationship between presenter and MG. The chapter pill, 30px continuous cumulative progress track, and single caption layer are mandatory packaging elements and do not disappear when the MG style changes.

## Complete packaged-video frames

Every image below preserves the complete video frame, including chapters, captions, progress, presenter framing, and player state.

<p align="center">
  <img src="assets/readme/cover-source/01-talking-video.png" alt="Complete frame: talking video, chapter, captions, and progress bar" width="49%">
  <img src="assets/readme/cover-source/02-agent-execution.png" alt="Complete frame: Agent execution, task mask, captions, and progress bar" width="49%">
  <img src="assets/readme/cover-source/03-motion-graphics.png" alt="Complete frame: MG, chapter, captions, presenter, and progress bar" width="49%">
  <img src="assets/readme/cover-source/04-packaged-video.png" alt="Complete frame: packaged video, chapter, captions, presenter, and progress bar" width="49%">
</p>

## Install

Use the standard Skills CLI:

```bash
npx skills add PoetCoderJun/MotionTalk
```

Or send the repository URL to Codex, Kimi, or another Agent that supports Skills:

```text
Please install MotionTalk:
https://github.com/PoetCoderJun/MotionTalk
```

## Use

Use:

```text
Use $motiontalk with:
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

### No SRT yet?

First use a separate transcription capability to generate and verify the final SRT for the edited talking video. Then run MotionTalk.

```text
I do not have an SRT yet.
First use an available independent AI transcription capability
to generate /data/final.srt for /data/talking-video.mp4.
Verify that it matches the video timeline, then use $motiontalk with:
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

## Efficient execution path

The repository ships fixed execution entry points:

- `validate_plan.py`: validates approval, semantic invariants, visual theme, and packaging contract;
- `render_segments.mjs`: bundles once, opens one browser, and renders every final MG cue;
- `render_package_overlays.mjs`: renders transparent chapter overlays;
- `build_and_package.py`: composites mutually exclusive cues and performs one full-video packaging pass;
- `quality_gate.py`: checks full decode, source-audio identity, evidence frames, and visible packaging.

Final delivery stays at 60fps. When needed, an optional 1.15× global speed-up retimes video, source audio, captions, chapters, and progress together inside the single packaging encode.

## Quality gates

MotionTalk does not treat “FFmpeg exited successfully” as delivery:

- every MG semantic invariant must have an evidence frame;
- presenter proportions must survive crop/scale, and MG must not cover the face;
- chapter pill, 30px progress track, and one caption layer must be visibly present in full-size evidence frames;
- final audio must come only from the input video, with full decode and timeline checks passing;
- every required check in `quality-report.v1.json` must be `passed`.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 scripts/test_build_and_package.py
```

## License

Original repository material is available under [CC BY-NC-SA 4.0](LICENSE.md) for non-commercial use. Commercial use requires separate written permission.
