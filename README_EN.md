[English home](README.md) · [简体中文](README.zh-CN.md)

# MotionTalk

**From your audio recording to a complete social video.**

Bring an audio file, optionally a folder of materials. MotionTalk handles transcription and matching subtitles internally, asks whether you want selective breath-gap trimming, develops the visual story with you, and produces an MP4 through Hyperframes. No presenter video or user-prepared SRT is required.

[Get started](#quickstart) · [Creator work](#creator-work) · [工程案例](docs/harness-case-study.md)

Non-commercial use under [CC BY-NC-SA 4.0](LICENSE.md). Commercial use requires prior written permission. Third-party materials keep their own licenses.

## Quickstart

Install the Skill in an Agent that can read local files/images and run commands:

```bash
npx skills add PoetCoderJun/MotionTalk
```

```text
Use $motiontalk with /data/my-audio.wav.
I want a complete social video explaining the ideas in my recording.
Optional materials: /data/materials.
```

If you have not said whether to trim breath gaps, the Agent asks first. If yes, it listens and selects suitable gaps, compressing only those gaps to 0.25 seconds by default. If no, it preserves the original timeline. Word gaps are not automatically classified as breaths; fillers, mistakes and retakes are not removed without separate instructions.

The Agent progressively resolves the publishing format, creative idea, optional materials, visual style and optional reference videos. None of the optional inputs is required. Review the director plan before production, or explicitly authorize an unattended run. Publishing remains your action.

## What you get

- A complete MP4 with the spoken story, visual explanation and pacing designed together.
- Prepared audio and matching internal SRT, with a sample-based edit report.
- A reviewable director plan, editable HTML/CSS/GSAP project and technical delivery report.

The initializer creates a scaffold; the Agent still has to produce and inspect the visual story. A few title cards or a successful render do not establish creative quality.

## Creator work

### Vibe Working: visual explanations and screen demonstrations

![Existing creator video showing animated workflow diagrams, a presenter and a screen demonstration at 6× speed](assets/examples/vibe-working-6x.gif)

00:39–01:27 from Jun’s existing Vibe Working video, condensed to about 8 seconds at **6× speed**.

### Embodied AI: diagrams that follow the argument

![Existing embodied-AI explainer showing progressive diagrams, captions and a presenter at 6× speed](assets/examples/embodied-correction-6x.gif)

The final 30 seconds of Jun’s existing embodied-AI explainer, condensed to about 5 seconds at **6× speed**.

These silent GIFs are excerpts from the author’s existing finished videos, not end-to-end validation of this audio-first version.

**[More example videos · 诗人程序员Jun.AI on Xiaohongshu](https://www.xiaohongshu.com/user/profile/5b40fe744eacab72c9f480ef)**

## Setup and data path

Python 3.10+, FFmpeg/ffprobe, Node >=22 and a local full Google Chrome are required. In the installed Skill directory, install the reviewed dependencies:

```bash
python3 -m pip install -r requirements.txt
npm ci
```

The lockfile pins Hyperframes 0.8.30 and GSAP 3.14.2. The built-in DashScope ASR needs service configuration (including DASHSCOPE_API_KEY) and explicit upload/charge authorization. It uploads an audio proxy to the service, polls an asynchronous task and retrieves the result; it is not offline ASR. Local rendering does not make the entire workflow local. The selected Agent’s own data handling also applies. See [audio preparation](references/00-audio.md).

Hardware H.264 and one worker are the default. An explicit software mode is available when hardware support is unsuitable; runtime and browser downloads are not automatic. Optional external assets/components need source and license checks.

## Checks and limitations

Transcription can mishear words or timestamps. Selective gap edits depend on listening review and usable word timings; they are not an automatic breath detector. Direct splicing can need manual boundary refinement. The no-trim path preserves timing while normalizing the audio container/sample rate.

Technical scripts check structure, sample-based editing, subtitle remapping, dimensions, codecs and audio/video duration. Continuous visual review and actual listening are separate. Approval/state fields are workflow records, not authenticated signatures. The renderer checks the recorded review state, not the truth of the evidence. No customers, deployment metrics, timing or cost savings are claimed.

## Engineering and local checks

Read the [Harness case study](docs/harness-case-study.en.md) for the code’s current gates and limits. Run after installing the pinned dependencies:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/plan-validation/run.py
```

Tests use synthetic input/mock service results and do not call cloud models. A synthetic audio-only rendering smoke test is documented in [the example](examples/audio-only-smoke/README.md); it is a technical check, not a creator showcase.

## Compatibility and licenses

[clean-talking-video](https://github.com/PoetCoderJun/clean-talking-video) remains operational for the existing video-editing workflow. [dingtalk-style-minutes](https://github.com/PoetCoderJun/dingtalk-style-minutes) keeps its existing clean-talking-video dependency. Neither repository is archived or removed by this integration.

See [migration notes](docs/audio-first-migration.md) and [third-party notices](THIRD_PARTY_NOTICES.md). The root license is unchanged; commercial use requires separate prior written permission.

<!-- Compatibility anchors for previously published links. -->
<a id="checks-and-limitations"></a>
<a id="core-capabilities"></a>
<a id="development"></a>
<a id="first-run"></a>
<a id="install"></a>
<a id="just-tell-the-agent-what-you-want"></a>
<a id="license"></a>
<a id="reference-themes"></a>
<a id="参考主题"></a>
<a id="和-ai-说几句话就行"></a>
<a id="安装"></a>
<a id="开发验证"></a>
<a id="核心能力"></a>
<a id="检查与限制"></a>
<a id="第一次使用"></a>
<a id="许可"></a>
