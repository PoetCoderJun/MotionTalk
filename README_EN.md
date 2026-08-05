[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

Give MotionTalk an edited talking video and a timeline-accurate final SRT. The
Agent first creates a director prompt. After one approval, it continuously
builds the project-specific Remotion composition, renders evidence frames,
produces the final video, and runs quality gates.

## Prompt-first

MotionTalk does not ship a heavy Remotion template or encode composition,
dimensions, progress height, typography ratios, or animation as global modes.

Presenter overlays, full-screen MG with a presenter window, and switching
between presenter and screen recording are prompt-level visual choices. Each
project implements only its approved direction.

```text
Edited video + final SRT
  → Director prompt and semantic invariants
  → One user approval
  → Project-specific Remotion composition
  → Final render + renderStill evidence + quality gates
  → Final packaged video
```

MotionTalk does not run ASR, remove mistakes or pauses, or recut the source.
The input video remains the sole timeline, semantic, and final-audio source.

## Install

```bash
npx skills add PoetCoderJun/MotionTalk
```

## Use

```text
Use $motiontalk with:
- video: /data/talking-video.mp4
- subtitles: /data/final.srt
- output_dir: /work/mg/output
```

Director-plan approval is the only interruption. Render spec, captions,
chapters, progress, layout, safe zones, and animation are frozen in that
project's plan.

## Deterministic thin layer

- `validate_plan.py` validates approval, project render spec, cue coverage,
  visual prompts, and semantic invariants;
- `render_master.mjs` uses official Remotion entry points, defaults to 75% of
  available concurrency, and keeps a portable fallback when hardware encoding
  is unavailable;
- `validate_master.mjs` validates the final video against project data and
  approved evidence.

## Render performance

The default command is portable across macOS, Windows, and Linux. It uses
`75%` concurrency and `if-possible` hardware acceleration. If the device or
execution environment cannot access a hardware encoder, Remotion falls back to
software encoding instead of treating a platform-specific encoder as a
prerequisite.

### macOS performance recommendation (optional)

Apple Silicon users can first confirm that FFmpeg exposes VideoToolbox:

```bash
ffmpeg -hide_banner -encoders | grep h264_videotoolbox
```

After verifying that the current terminal can access the system encoder
service, hardware encoding can be made fail-fast with an explicit bitrate:

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

Use `required` only on a macOS environment where the encoder and permissions
have already been verified. Other platforms, restricted sandboxes, and
unverified machines should keep the default `if-possible` behavior.

## Development

```bash
python3 -m unittest discover -s tests -v
node scripts/render_master.mjs --help
node scripts/validate_master.mjs --help
```

## License

Original repository material is available under
[CC BY-NC-SA 4.0](LICENSE.md) for non-commercial use. Commercial use requires
separate written permission.
