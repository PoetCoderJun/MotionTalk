#!/usr/bin/env python3
"""Validate MotionTalk approval and the mandatory packaging baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(plan: dict) -> list[str]:
    errors: list[str] = []
    if plan.get("status") != "approved" or plan.get("approved") is not True:
        errors.append("plan must be explicitly approved")
    allowed_themes = {
        "floating-overlay",
        "mg-with-presenter-window",
        "switching",
    }
    mg_theme = plan.get("mg_theme")
    if mg_theme not in allowed_themes:
        errors.append(
            "mg_theme must be floating-overlay, mg-with-presenter-window, or switching"
        )
    mg_cues = [
        cue
        for cue in plan.get("cues", [])
        if cue.get("visual") != "presenter-full-screen"
    ]
    for cue in mg_cues:
        invariants = cue.get("spec", {}).get("semantic_invariants")
        if not isinstance(invariants, list) or not invariants:
            errors.append(f"{cue.get('id', '<unknown>')}: semantic_invariants missing")

    source = plan.get("source")
    source_duration = None
    if not isinstance(source, dict):
        errors.append("source is required")
    else:
        for key in ("video", "subtitles"):
            if not source.get(key):
                errors.append(f"source.{key} is required")
        try:
            source_duration = float(source["duration_seconds"])
        except (KeyError, TypeError, ValueError):
            errors.append("source.duration_seconds must be a number (seconds)")
        try:
            width = int(source["width"])
            height = int(source["height"])
            fps = float(source["fps"])
            if (width, height) != (1920, 1080) or fps != 60:
                errors.append("source must be 1920x1080 at 60fps")
        except (KeyError, TypeError, ValueError):
            errors.append("source.width/source.height/source.fps are required numbers")

    cues = plan.get("cues", [])
    if not cues:
        errors.append("at least one cue is required")
    else:
        fps = 60
        frames = []
        for cue in cues:
            if cue.get("visual") is None:
                errors.append(f"{cue.get('id', '<unknown>')}: visual is required")
            try:
                start_seconds = float(cue["start_seconds"])
                end_seconds = float(cue["end_seconds"])
                start_frame = round(start_seconds * fps)
                end_frame = round(end_seconds * fps)
                frames.append(
                    (
                        cue.get("id", "<unknown>"),
                        start_frame,
                        end_frame,
                    )
                )
                if abs(start_seconds * fps - start_frame) > 1e-6:
                    errors.append(
                        f"{cue.get('id', '<unknown>')}: start_seconds is not on the 60fps frame grid"
                    )
                if abs(end_seconds * fps - end_frame) > 1e-6:
                    errors.append(
                        f"{cue.get('id', '<unknown>')}: end_seconds is not on the 60fps frame grid"
                    )
                if end_frame <= start_frame:
                    errors.append(
                        f"{cue.get('id', '<unknown>')}: end_seconds must be after start_seconds"
                    )
            except (KeyError, TypeError, ValueError):
                errors.append(
                    f"{cue.get('id', '<unknown>')}: start_seconds/end_seconds must be numbers"
                )
        if frames and frames[0][1] != 0:
            errors.append("cue timeline must begin at frame 0")
        for (_, _, left_end), (right_id, right_start, _) in zip(frames, frames[1:]):
            if left_end != right_start:
                errors.append(f"cue gap or overlap before {right_id} (60fps frame grid)")
        if source_duration is not None and frames:
            expected_end = round(source_duration * fps)
            if frames[-1][2] != expected_end:
                errors.append("cue timeline must end at source.duration_seconds")

    keyed_visual = "transparent-floating-overlay-on-presenter"
    if any(cue.get("visual") == keyed_visual for cue in cues):
        overlay_style = plan.get("overlay_style")
        if not isinstance(overlay_style, dict) or not overlay_style.get("key_color"):
            errors.append(f"overlay_style.key_color is required for {keyed_visual} cues")
        policy = plan.get("presenter_policy", {})
        if policy.get("default") != "full-screen-underlay":
            errors.append(
                f"presenter_policy.default must be full-screen-underlay for {keyed_visual} cues"
            )
    if mg_theme == "floating-overlay":
        invalid = [
            cue.get("id", "<unknown>")
            for cue in mg_cues
            if cue.get("visual") != keyed_visual
        ]
        if invalid:
            errors.append(
                "floating-overlay MG cues must use "
                f"{keyed_visual}: {', '.join(map(str, invalid))}"
            )
    elif any(cue.get("visual") == keyed_visual for cue in cues):
        errors.append(f"{keyed_visual} cues require mg_theme floating-overlay")

    chapters = plan.get("chapters", [])
    for chapter in chapters:
        for key in ("id", "start_seconds", "end_seconds", "title"):
            if chapter.get(key) is None:
                errors.append(f"chapter {chapter.get('id', '<unknown>')}: {key} is required")

    highlights = plan.get("caption_highlights")
    if highlights is None:
        errors.append(
            "caption_highlights is required (default-on; write enabled:false only when the user explicitly opted out before approval)"
        )
    elif not isinstance(highlights, dict):
        errors.append("caption_highlights must be an object")
    elif highlights.get("enabled") is True:
        highlight_cues = highlights.get("cues")
        if not isinstance(highlight_cues, dict):
            errors.append("caption_highlights.cues must be an object keyed by SRT index")
            highlight_cues = {}
        if not highlight_cues:
            errors.append("caption_highlights.cues must cover at least one SRT entry when enabled")
        for cue_index, keywords in highlight_cues.items():
            if not str(cue_index).isdigit():
                errors.append(f"caption_highlights.cues key {cue_index!r} is not an SRT index")
            if not isinstance(keywords, list) or not keywords:
                errors.append(f"caption_highlights.cues[{cue_index!r}] must be a non-empty list")
    elif highlights.get("enabled") is not False:
        errors.append("caption_highlights.enabled must be true or false")

    package = plan.get("package_style")
    if not isinstance(package, dict):
        return [*errors, "package_style is required"]
    if package.get("profile") != "sample-classic-v1":
        errors.append("package_style.profile must be sample-classic-v1")
    header = package.get("chapter_header", {})
    progress = package.get("progress", {})
    captions = package.get("captions", {})
    if header.get("enabled") is not True:
        errors.append("chapter header must be enabled")
    if progress.get("enabled") is not True:
        errors.append("progress must be enabled")
    try:
        if int(progress.get("height_px", 0)) < 24:
            errors.append("progress.height_px must be at least 24")
    except (TypeError, ValueError):
        errors.append("progress.height_px must be a number of at least 24")
    if progress.get("mode") != "continuous-cumulative":
        errors.append("progress.mode must be continuous-cumulative")
    if progress.get("segment_by_chapter_duration") is not True:
        errors.append("progress must segment by chapter duration")
    if progress.get("show_labels") is not True:
        errors.append("sample-classic progress labels must be enabled")
    if progress.get("label_layer") != "ass-only":
        errors.append("progress.label_layer must be ass-only")
    if captions.get("enabled") is not True or captions.get("single_layer") is not True:
        errors.append("one caption layer must be enabled")
    if not plan.get("chapters"):
        errors.append("at least one chapter is required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate approved MotionTalk plan and package contract"
    )
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = validate(plan)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("MotionTalk plan and package contract: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
