#!/usr/bin/env python3
"""Build MotionTalk's clean cue composite and one-pass packaged final video."""

from __future__ import annotations

import argparse
import json
import math
import platform
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


FPS = 60
WIDTH = 1920
HEIGHT = 1080


@dataclass(frozen=True)
class Cue:
    cue_id: str
    start: float
    end: float
    presenter_full: bool
    visual: str

    @property
    def start_frame(self) -> int:
        return round(self.start * FPS)

    @property
    def end_frame(self) -> int:
        return round(self.end * FPS)

    @property
    def frames(self) -> int:
        return self.end_frame - self.start_frame

    @property
    def duration(self) -> float:
        return self.frames / FPS


def run(command: list[str], log: Path, dry_run: bool) -> None:
    if command[0] == "ffmpeg" and "-nostats" not in command:
        command = ["ffmpeg", "-nostats", *command[1:]]
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"$ {shlex.join(command)}\n")
        if dry_run:
            return
        result = subprocess.run(command, stdout=handle, stderr=handle)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}); see {log}")


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip())
    entries: list[tuple[float, float, str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing = next((line for line in lines if "-->" in line), None)
        if timing is None:
            continue
        index = lines.index(timing)
        start, end = [item.strip() for item in timing.split("-->", 1)]
        entries.append((parse_srt_time(start), parse_srt_time(end), " ".join(lines[index + 1 :])))
    return entries


def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, centiseconds = divmod(centiseconds, 360_000)
    minutes, centiseconds = divmod(centiseconds, 6_000)
    secs, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def display_width(character: str) -> float:
    return 0.55 if ord(character) < 128 else 1.0


def ass_bgr_color(value: str) -> str:
    """#RRGGBB -> BBGGRR for ASS \\1c override tags."""
    value = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise ValueError(f"invalid emphasis color: {value!r}")
    red, green, blue = value[0:2], value[2:4], value[4:6]
    return f"{blue}{green}{red}".upper()


def softened_font_scale(requested: float) -> float:
    """Emphasis scale, softened and clamped to [1.16, 1.3] (1.0 keeps base size)."""
    if requested <= 1:
        return 1.0
    return max(1.16, min(1.3, 1 + (requested - 1) * 0.85))


def apply_caption_emphasis(
    wrapped: str,
    keywords: list[dict],
    base_font_size: int,
    default_color: str,
    default_scale: float,
) -> str:
    """Wrap keyword occurrences in ASS size/colour override tags.

    `wrapped` is wrap_caption() output (lines joined by \\N, braces already
    escaped). A keyword split across a line break is emphasised part by part;
    unmatched keywords are ignored silently.
    """
    if not keywords:
        return wrapped
    lines = wrapped.split(r"\N")
    for item in keywords:
        text = str(item.get("text", ""))
        if not text:
            continue
        color = ass_bgr_color(str(item.get("color") or default_color))
        size = round(base_font_size * softened_font_scale(float(item.get("scale", default_scale))))
        open_tag = rf"{{\fs{size}\1c&H{color}&}}"
        remaining = text
        index = 0
        while remaining and index < len(lines):
            line = lines[index]
            pos = line.find(remaining)
            if pos != -1:
                part = remaining
            else:
                part = ""
                for length in range(min(len(remaining), len(line)), 0, -1):
                    candidate = remaining[:length]
                    if line.endswith(candidate):
                        part = candidate
                        pos = len(line) - length
                        break
                if not part:
                    index += 1
                    continue
            lines[index] = line[:pos] + open_tag + part + r"{\r}" + line[pos + len(part) :]
            remaining = remaining[len(part) :]
            index += 1
    return r"\N".join(lines)


def wrap_caption(text: str, max_units: float = 23) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    lines: list[str] = []
    current = ""
    width = 0.0
    for character in text:
        unit = display_width(character)
        if current and width + unit > max_units:
            split = max(current.rfind("，"), current.rfind("。"), current.rfind(" "))
            if split >= max(1, len(current) - 7):
                lines.append(current[: split + 1].strip())
                current = current[split + 1 :].strip()
                width = sum(display_width(item) for item in current)
            else:
                lines.append(current)
                current = ""
                width = 0
        current += character
        width += unit
    if current:
        lines.append(current)
    return r"\N".join(lines[:3])


def truncate_label(text: str, max_units: float) -> str:
    text = re.sub(r"\s+", "", text).strip()
    if sum(display_width(item) for item in text) <= max_units:
        return text
    result = ""
    width = 0.0
    for character in text:
        unit = display_width(character)
        if width + unit + 1 > max_units:
            break
        result += character
        width += unit
    return f"{result}…" if result else ""


def validate_package_contract(plan: dict) -> dict:
    package = plan.get("package_style")
    if not isinstance(package, dict):
        raise ValueError("package_style is required")
    if package.get("profile") != "sample-classic-v1":
        raise ValueError("package_style.profile must be sample-classic-v1")
    header = package.get("chapter_header", {})
    progress = package.get("progress", {})
    captions = package.get("captions", {})
    if header.get("enabled") is not True:
        raise ValueError("chapter header must be enabled")
    if progress.get("enabled") is not True:
        raise ValueError("progress must be enabled")
    if int(progress.get("height_px", 0)) < 24:
        raise ValueError("progress.height_px must be at least 24")
    if progress.get("mode") != "continuous-cumulative":
        raise ValueError("progress.mode must be continuous-cumulative")
    if progress.get("segment_by_chapter_duration") is not True:
        raise ValueError("progress must segment by chapter duration")
    if progress.get("show_labels") is not True:
        raise ValueError("sample-classic progress labels must be enabled")
    if progress.get("label_layer") != "ass-only":
        raise ValueError("progress.label_layer must be ass-only")
    if captions.get("enabled") is not True or captions.get("single_layer") is not True:
        raise ValueError("one caption layer must be enabled")
    return package


def write_ass(
    path: Path,
    entries: list[tuple[float, float, str]],
    chapters: list[dict],
    source_duration: float,
    speed: float,
    show_progress_labels: bool = True,
    caption_highlights: dict | None = None,
) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MotionTalk,PingFang SC,53,&H00FFFBF9,&H00FFFBF9,&H4D2A170F,&H731B120F,-1,0,0,0,100,100,0,0,1,3,2,2,307,307,96,1
Style: Progress,PingFang SC,20,&H00FFFFFF,&H00FFFFFF,&H66000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    base_font_size = 53
    highlights = caption_highlights or {}
    emphasis_enabled = bool(highlights.get("enabled"))
    default_color = str(highlights.get("color", "#FFD166"))
    default_scale = float(highlights.get("font_scale", 1.2))
    cue_keywords = highlights.get("cues", {}) if isinstance(highlights.get("cues"), dict) else {}
    for index, (start, end, text) in enumerate(entries, start=1):
        safe = wrap_caption(text).replace("{", r"\{").replace("}", r"\}")
        if emphasis_enabled:
            raw_keywords = cue_keywords.get(str(index)) or cue_keywords.get(index) or []
            keywords = [
                item if isinstance(item, dict) else {"text": str(item)}
                for item in raw_keywords
            ]
            safe = apply_caption_emphasis(
                safe, keywords, base_font_size, default_color, default_scale
            )
        events.append(
            f"Dialogue: 0,{ass_time(start / speed)},{ass_time(end / speed)},"
            f"MotionTalk,,0,0,0,,{safe}"
        )
    if show_progress_labels:
        delivery_duration = source_duration / speed
        for index, chapter in enumerate(chapters, start=1):
            start = float(chapter["start_seconds"])
            end = float(chapter["end_seconds"])
            segment_width = 1828 * (end - start) / source_duration
            max_units = max(2, segment_width / 22)
            raw_label = str(
                chapter.get("short_label")
                or chapter.get("short_title")
                or chapter.get("title")
                or f"CH{index}"
            )
            label = (
                str(index)
                if segment_width < 65
                else truncate_label(raw_label, max_units) or f"CH{index}"
            )
            x = 46 + 1828 * ((start + end) / 2) / source_duration
            tag = rf"{{\pos({x:.1f},1037)\an5}}"
            events.append(
                f"Dialogue: 2,0:00:00.00,{ass_time(delivery_duration)},"
                f"Progress,,0,0,0,,{tag}{label}"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def filter_escape(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'")


def concat_escape(path: Path) -> str:
    return str(path).replace("'", r"'\''")


def encoder_args(name: str) -> list[str]:
    if name == "videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", "16M", "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]


def color_args() -> list[str]:
    return [
        "-color_range",
        "tv",
        "-colorspace",
        "bt709",
        "-color_trc",
        "bt709",
        "-color_primaries",
        "bt709",
    ]


def make_circle_assets(
    work: Path,
    diameter: int,
    border: int,
    color: str,
    log: Path,
    dry_run: bool,
) -> tuple[Path, Path]:
    inner = diameter - border * 2
    mask = work / f"circle-mask-{inner}.png"
    border_png = work / f"circle-border-{diameter}.png"
    inner_radius = inner / 2
    outer_radius = diameter / 2
    if not mask.exists() or dry_run:
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=black:s={inner}x{inner}:r=1",
                "-vf",
                "format=gray,"
                "geq=lum='if(lte((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2),"
                f"{inner_radius ** 2:.3f}),255,0)'",
                "-frames:v",
                "1",
                str(mask),
            ],
            log,
            dry_run,
        )
    if not border_png.exists() or dry_run:
        normalized_color = color.replace("#", "0x")
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={normalized_color}:s={diameter}x{diameter}:r=1",
                "-f",
                "lavfi",
                "-i",
                f"color=black:s={diameter}x{diameter}:r=1",
                "-filter_complex",
                "[0:v]format=rgba[c];"
                "[1:v]format=gray,"
                "geq=lum='if(lte((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2),"
                f"{outer_radius ** 2:.3f}),255,0)'[m];"
                "[c][m]alphamerge[v]",
                "-map",
                "[v]",
                "-frames:v",
                "1",
                str(border_png),
            ],
            log,
            dry_run,
        )
    return mask, border_png


def load_plan(path: Path, output_dir: Path) -> tuple[dict, Path, Path, list[Cue]]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("status") != "approved" or plan.get("approved") is not True:
        raise ValueError("placement plan must be approved")
    source = plan["source"]
    if int(source["width"]) != WIDTH or int(source["height"]) != HEIGHT:
        raise ValueError("bundled stage 2B pipeline requires 1920x1080")
    if round(float(source["fps"])) != FPS:
        raise ValueError("bundled stage 2B pipeline requires a 60fps source")
    video = Path(source["video"])
    subtitles = Path(source["subtitles"])
    if not video.is_file() or not subtitles.is_file():
        raise FileNotFoundError("source video or final SRT is missing")
    cues = [
        Cue(
            cue_id=item["id"],
            start=float(item["start_seconds"]),
            end=float(item["end_seconds"]),
            presenter_full=item["visual"] == "presenter-full-screen",
            visual=str(item["visual"]),
        )
        for item in plan["cues"]
    ]
    if not cues or cues[0].start_frame != 0:
        raise ValueError("cue timeline must begin at frame 0")
    for left, right in zip(cues, cues[1:]):
        if left.end_frame != right.start_frame:
            raise ValueError(f"cue gap or overlap: {left.cue_id}/{right.cue_id}")
    for cue in cues:
        if not cue.presenter_full and not (output_dir / "segments" / f"{cue.cue_id}.mp4").is_file():
            raise FileNotFoundError(f"missing formal segment: segments/{cue.cue_id}.mp4")
    return plan, video, subtitles, cues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Efficient MotionTalk cue composition and one-pass packaging"
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overlay-dir", type=Path)
    parser.add_argument(
        "--encoder",
        choices=("auto", "videotoolbox", "libx264"),
        default="auto",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Optional final pacing multiplier, e.g. 1.15; output remains 60fps",
    )
    parser.add_argument(
        "--reuse-composite",
        action="store_true",
        help="Reuse frame-count-matched cue composites when only packaging changed",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1.0 <= args.speed <= 2.0:
        raise ValueError("--speed must be between 1.0 and 2.0")

    output_dir = args.output_dir.resolve()
    plan, source_video, subtitle_path, cues = load_plan(args.plan, output_dir)
    project_id = plan["project_id"]
    work = output_dir / "work"
    composite_dir = work / "composite-segments"
    logs = output_dir / "logs"
    final_dir = output_dir / "final"
    overlay_dir = (args.overlay_dir or output_dir / "package-overlays").resolve()
    for directory in (work, composite_dir, logs, final_dir):
        directory.mkdir(parents=True, exist_ok=True)

    chapters = plan.get("chapters", [])
    if not chapters:
        raise ValueError("plan has no chapters")
    package_style = validate_package_contract(plan)
    progress_style = package_style["progress"]
    progress_left = int(progress_style.get("left_px", 46))
    progress_right = int(progress_style.get("right_px", 46))
    progress_width = WIDTH - progress_left - progress_right
    progress_height = int(progress_style.get("height_px", 30))
    progress_bottom = int(progress_style.get("bottom_px", 28))
    progress_x = progress_left
    progress_y = HEIGHT - progress_bottom - progress_height
    show_progress_labels = bool(progress_style.get("show_labels", True))
    overlays = [overlay_dir / f"{chapter['id']}.png" for chapter in chapters]
    missing = [str(path) for path in overlays if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing package overlays: {missing}")

    encoder = args.encoder
    if encoder == "auto":
        encoder = "videotoolbox" if platform.system() == "Darwin" else "libx264"
    encode = encoder_args(encoder)
    log = logs / "ffmpeg-build-and-package.log"
    cropped_overlay_dir = work / "package-overlays-cropped"
    cropped_overlay_dir.mkdir(parents=True, exist_ok=True)
    pill_overlays: list[Path] = []
    for overlay in overlays:
        pill = cropped_overlay_dir / f"{overlay.stem}-pill.png"
        pill_overlays.append(pill)
        if not pill.is_file() or args.dry_run:
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(overlay),
                    "-vf",
                    "crop=700:180:0:0,format=rgba",
                    "-frames:v",
                    "1",
                    str(pill),
                ],
                log,
                args.dry_run,
            )
    track_overlay = cropped_overlay_dir / "progress-track.png"
    if not track_overlay.is_file() or args.dry_run:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(overlays[0]),
                "-vf",
                f"crop={progress_width}:{progress_height}:{progress_x}:{progress_y},format=rgba",
                "-frames:v",
                "1",
                str(track_overlay),
            ],
            log,
            args.dry_run,
        )
    presenter = plan.get("presenter_policy", {})
    overlay_style = plan.get("overlay_style", {})
    keyed_overlay_visual = "transparent-floating-overlay-on-presenter"
    needs_legacy_circle = any(
        not cue.presenter_full and cue.visual != keyed_overlay_visual for cue in cues
    )
    diameter = int(presenter.get("circle_diameter_px", 360))
    border = int(presenter.get("circle_border_px", 8))
    border_color = str(presenter.get("circle_border_color", "#245B9E"))
    bottom_margin = int(presenter.get("circle_bottom_margin_px", 100))
    x = WIDTH - diameter - 40
    y = HEIGHT - diameter - bottom_margin
    mask = None
    border_png = None
    if needs_legacy_circle:
        mask, border_png = make_circle_assets(
            work, diameter, border, border_color, log, args.dry_run
        )

    segment_paths: list[Path] = []
    inner = diameter - border * 2
    for cue in cues:
        destination = composite_dir / f"{cue.cue_id}.mp4"
        segment_paths.append(destination)
        if args.reuse_composite and destination.is_file():
            existing = probe(destination)
            stream = next(
                item for item in existing["streams"] if item["codec_type"] == "video"
            )
            if stream.get("nb_frames") not in (None, "N/A") and int(
                stream["nb_frames"]
            ) == cue.frames:
                continue
        source_seek = ["-ss", f"{cue.start:.6f}", "-t", f"{cue.duration:.6f}"]
        if cue.presenter_full:
            command = [
                "ffmpeg",
                "-y",
                *source_seek,
                "-i",
                str(source_video),
                "-map",
                "0:v:0",
                "-an",
                "-vf",
                f"fps={FPS},trim=end_frame={cue.frames},setpts=PTS-STARTPTS,"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1,"
                "scale=in_range=auto:out_range=tv,format=yuv420p",
                "-frames:v",
                str(cue.frames),
                *encode,
                *color_args(),
                str(destination),
            ]
        elif cue.visual == keyed_overlay_visual:
            overlay_segment = output_dir / "segments" / f"{cue.cue_id}.mp4"
            key_color = str(overlay_style.get("key_color", "#00FF00")).replace(
                "#", "0x"
            )
            key_similarity = float(overlay_style.get("key_similarity", 0.08))
            key_blend = float(overlay_style.get("key_blend", 0.035))
            despill_type = str(overlay_style.get("despill_type", "green"))
            despill_mix = float(overlay_style.get("despill_mix", 0.45))
            despill_expand = float(overlay_style.get("despill_expand", 0.08))
            command = [
                "ffmpeg",
                "-y",
                "-i",
                str(overlay_segment),
                *source_seek,
                "-i",
                str(source_video),
                "-filter_complex",
                f"[1:v]fps={FPS},trim=end_frame={cue.frames},setpts=PTS-STARTPTS,"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1[base];"
                f"[0:v]fps={FPS},trim=end_frame={cue.frames},setpts=PTS-STARTPTS,"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1,format=rgba,"
                f"colorkey={key_color}:{key_similarity:.4f}:{key_blend:.4f},"
                f"despill=type={despill_type}:mix={despill_mix:.4f}:"
                f"expand={despill_expand:.4f}[mg];"
                "[base][mg]overlay=0:0:shortest=1,"
                "scale=in_range=auto:out_range=tv,format=yuv420p[v]",
                "-map",
                "[v]",
                "-an",
                "-frames:v",
                str(cue.frames),
                *encode,
                *color_args(),
                str(destination),
            ]
        else:
            assert mask is not None and border_png is not None
            background = output_dir / "segments" / f"{cue.cue_id}.mp4"
            command = [
                "ffmpeg",
                "-y",
                "-i",
                str(background),
                *source_seek,
                "-i",
                str(source_video),
                "-loop",
                "1",
                "-framerate",
                str(FPS),
                "-t",
                f"{cue.duration:.6f}",
                "-i",
                str(mask),
                "-loop",
                "1",
                "-framerate",
                str(FPS),
                "-t",
                f"{cue.duration:.6f}",
                "-i",
                str(border_png),
                "-filter_complex",
                f"[0:v]fps={FPS},trim=end_frame={cue.frames},setpts=PTS-STARTPTS,"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1[bg];"
                f"[1:v]fps={FPS},trim=end_frame={cue.frames},setpts=PTS-STARTPTS,"
                "crop='min(iw,ih)':'min(iw,ih)':"
                "'(iw-min(iw,ih))/2':'(ih-min(iw,ih))/2',"
                f"scale={inner}:{inner}:flags=lanczos,format=rgba[face];"
                "[2:v]format=gray[mask];"
                "[face][mask]alphamerge[roundface];"
                "[3:v]format=rgba[roundborder];"
                f"[roundborder][roundface]overlay={border}:{border}:shortest=1[circle];"
                f"[bg][circle]overlay={x}:{y}:shortest=1,"
                "scale=in_range=auto:out_range=tv,format=yuv420p[v]",
                "-map",
                "[v]",
                "-an",
                "-frames:v",
                str(cue.frames),
                *encode,
                *color_args(),
                str(destination),
            ]
        run(command, log, args.dry_run)

    concat_file = work / "composite-segments.ffconcat"
    concat_file.write_text(
        "ffconcat version 1.0\n"
        + "".join(f"file '{concat_escape(path)}'\n" for path in segment_paths),
        encoding="utf-8",
    )
    clean_video = work / f"{project_id}-clean-video-only.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-map",
            "0:v:0",
            "-c",
            "copy",
            str(clean_video),
        ],
        log,
        args.dry_run,
    )

    source_probe = probe(source_video)
    source_stream = next(
        item for item in source_probe["streams"] if item["codec_type"] == "video"
    )
    raw_frames = source_stream.get("nb_frames")
    target_frames = (
        int(raw_frames)
        if raw_frames not in (None, "", "N/A")
        else round(float(plan["source"]["duration_seconds"]) * FPS)
    )
    if cues[-1].end_frame != target_frames:
        if abs(cues[-1].end_frame - target_frames) > math.ceil(0.1 * FPS):
            raise ValueError("cue timeline and source frame count differ by more than 0.1s")
        target_frames = cues[-1].end_frame
    source_duration = float(plan["source"]["duration_seconds"])
    total_duration = source_duration / args.speed
    delivery_frames = round(target_frames / args.speed)
    ass_path = work / "captions.ass"
    write_ass(
        ass_path,
        parse_srt(subtitle_path),
        chapters,
        source_duration,
        args.speed,
        show_progress_labels,
        caption_highlights=plan.get("caption_highlights"),
    )
    pill_concat = work / "package-pills.ffconcat"
    pill_concat_lines = ["ffconcat version 1.0"]
    for pill, chapter in zip(pill_overlays, chapters):
        duration_seconds = (
            float(chapter["end_seconds"]) - float(chapter["start_seconds"])
        ) / args.speed
        pill_concat_lines.append(f"file '{concat_escape(pill)}'")
        pill_concat_lines.append(f"duration {duration_seconds:.9f}")
    pill_concat_lines.append(f"file '{concat_escape(pill_overlays[-1])}'")
    pill_concat.write_text(
        "\n".join(pill_concat_lines) + "\n",
        encoding="utf-8",
    )
    pill_video = work / "package-pills-qtrle.mov"
    pill_video_ok = False
    if args.reuse_composite and pill_video.is_file() and not args.dry_run:
        pill_probe = probe(pill_video)
        pill_stream = next(
            item for item in pill_probe["streams"] if item["codec_type"] == "video"
        )
        pill_video_ok = (
            int(pill_stream["width"]) == 700
            and int(pill_stream["height"]) == 180
            and pill_stream.get("nb_frames") not in (None, "N/A")
            and int(pill_stream["nb_frames"]) == delivery_frames
        )
    if not pill_video_ok:
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(pill_concat),
                "-vf",
                f"fps={FPS},tpad=stop_mode=clone:stop_duration=0.2,"
                f"trim=end_frame={delivery_frames},setpts=N/(60*TB),format=argb",
                "-frames:v",
                str(delivery_frames),
                "-an",
                "-c:v",
                "qtrle",
                str(pill_video),
            ],
            log,
            args.dry_run,
        )

    command = [
        "ffmpeg",
        "-y",
        "-filter_complex_threads",
        "2",
        "-i",
        str(clean_video),
        "-i",
        str(source_video),
        "-i",
        str(pill_video),
    ]
    pill_index = 2
    track_index = 3
    command.extend(
        [
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(track_overlay),
        ]
    )
    progress_index = track_index + 1
    command.extend(
        [
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x5DDCCD@0.36:s={progress_width}x{max(1, progress_height - 4)}:r={FPS}",
        ]
    )

    speed_filter = (
        "setpts=N/(60*TB),"
        if args.speed == 1.0
        else (
            f"setpts=(PTS-STARTPTS)/{args.speed:.8f},fps={FPS},"
            "tpad=stop_mode=clone:stop_duration=0.2,"
            f"trim=end_frame={delivery_frames},setpts=N/(60*TB),"
        )
    )
    filters = [
        f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration=0.2,"
        f"trim=end_frame={target_frames},{speed_filter}"
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,"
        "scale=in_range=auto:out_range=tv,format=yuv420p[base]",
        f"[{track_index}:v]format=rgba[track]",
        f"[{pill_index}:v]setpts=PTS-STARTPTS,format=rgba[pill]",
        f"[base][track]overlay={progress_x}:{progress_y}:shortest=1[withtrack]",
    ]
    fill_expr = (
        f"max(2,2*trunc(({progress_width}*min(1,t/{total_duration:.6f}))/2))"
    )
    filters.extend(
        [
            f"[{progress_index}:v]format=rgba,"
            f"scale=w='{fill_expr}':h={max(1, progress_height - 4)}:eval=frame,"
            f"pad={progress_width}:{max(1, progress_height - 4)}:0:0:color=black@0[progress]",
            f"[withtrack][progress]overlay={progress_x}:{progress_y + 2}:shortest=1[withprogress]",
            "[withprogress][pill]overlay=0:0:shortest=1[withchapter]",
            f"[withchapter]subtitles='{filter_escape(ass_path)}',"
            "format=yuv420p[v]",
        ]
    )

    final_path = final_dir / f"{project_id}-packaged.mp4"
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[v]",
            *encode,
            *color_args(),
        ]
    )
    if args.speed == 1.0:
        command.extend(["-map", "1:a:0", "-c:a", "copy"])
    else:
        command.extend(
            [
                "-filter:a",
                f"atempo={args.speed:.8f}",
                "-map",
                "1:a:0",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
            ]
        )
    command.extend(
        [
            "-r",
            str(FPS),
            "-fps_mode",
            "cfr",
            "-movflags",
            "+faststart",
            str(final_path),
        ]
    )
    run(command, log, args.dry_run)
    if not args.dry_run:
        probe(final_path)
    print(final_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
