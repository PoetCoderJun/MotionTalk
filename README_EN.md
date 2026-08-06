[简体中文](README.md) | [English](README_EN.md)

# MotionTalk

Give MotionTalk an edited talking video and a timeline-accurate final SRT. The
Agent first creates a director prompt. After one approval, it continuously
builds the project-specific Remotion composition, renders evidence frames,
produces the final video, and runs quality gates.

## Four themes

The four themes define the primary relationship between the presenter, MG,
screen recording, or PPT. They are reusable director-prompt references rather
than fixed Remotion templates. Every frame below comes from a real local
delivery.

<table>
  <tr>
    <td width="50%"><img src="assets/readme/theme-floating-overlay.webp" alt="Full-screen presenter with floating MG sample"><br><strong>1. floating-overlay</strong><br><sub>Keep the presenter or recording full-screen and add only lightweight MG in safe zones.</sub></td>
    <td width="50%"><img src="assets/readme/theme-presenter-window.webp" alt="Full-screen MG with presenter window sample"><br><strong>2. mg-with-presenter-window</strong><br><sub>Make MG, screenshots, or recordings primary while the presenter remains in a circle or rectangle.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="assets/readme/theme-switching.webp" alt="Presenter and screen recording switching sample"><br><strong>3. switching</strong><br><sub>Switch between presenter, full-screen MG, and recordings so each state stays readable.</sub></td>
    <td width="50%"><img src="assets/readme/theme-ppt-focus-portrait.webp" alt="Portrait PPT focus sample"><br><strong>4. PPT Focus Portrait</strong><br><sub>Use PPT as the portrait primary visual, with self-fitting captions below, a bottom-right presenter, and progress.</sub></td>
  </tr>
</table>

See [`references/05-mg-themes.md`](references/05-mg-themes.md) for the first
three selection rules and
[`references/04-theme-ppt-focus-portrait.md`](references/04-theme-ppt-focus-portrait.md)
for the portrait PPT proportions and evidence gates.

## Core capabilities

- **Content-aware director prompt**: understand the full narration and SRT
  before choosing composition, animation, screen/PPT timing, and semantic
  emphasis for this project instead of applying a fixed template;
- **One approval, continuous delivery**: after director-plan approval, continue
  through implementation, evidence frames, final render, and QA without repeated
  interruptions;
- **One master composition**: one `MasterComposition` packages the visuals while
  source-video audio remains the only audio track, preventing duplicate speech,
  drift, and competing timelines;
- **Efficient local Remotion rendering**: use the project's Remotion packages, a
  version-matched managed Headless Shell, and `75%` concurrency by default;
  enable hardware encoding when available and retain a portable fallback;
- **Semantic quality gates**: capture evidence against approved claims and
  forbidden states, with explicit checks for the longest subtitle, safe zones,
  layout, and final media parameters;
- **Reusable prompt themes**: preserve visual relationships, proportions, and
  evidence rules across four themes without cloning a rigid code template.

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
  available concurrency, loads Remotion from the project dependencies, uses a
  Remotion-managed browser, and keeps a portable hardware fallback;
- `validate_master.mjs` validates the final video against project data and
  approved evidence.

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
