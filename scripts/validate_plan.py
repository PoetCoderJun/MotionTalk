#!/usr/bin/env python3
"""Validate an approved prompt-first MotionTalk placement plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _positive_number(container: dict, key: str, prefix: str, errors: list[str]):
    try:
        value = float(container[key])
        if value <= 0:
            raise ValueError
        return value
    except (KeyError, TypeError, ValueError):
        errors.append(f"{prefix}.{key} must be a positive number")
        return None


def _required_prompt(plan: dict, key: str, errors: list[str]) -> None:
    value = plan.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty approved prompt")


def _validate_invariants(cue: dict, errors: list[str]) -> None:
    cue_id = cue.get("id", "<unknown>")
    invariants = cue.get("spec", {}).get("semantic_invariants")
    if not isinstance(invariants, list) or not invariants:
        errors.append(f"{cue_id}: semantic_invariants missing")
        return
    for invariant in invariants:
        invariant_id = invariant.get("id", "<unknown>")
        for key in ("id", "assertion", "proof_moment"):
            if invariant.get(key) in (None, ""):
                errors.append(f"{cue_id}/{invariant_id}: {key} is required")
        if not isinstance(invariant.get("forbidden"), list):
            errors.append(f"{cue_id}/{invariant_id}: forbidden must be a list")


def validate(plan: dict) -> list[str]:
    errors: list[str] = []
    if plan.get("status") != "approved" or plan.get("approved") is not True:
        errors.append("plan must be explicitly approved")

    source = plan.get("source")
    if not isinstance(source, dict):
        errors.append("source is required")
        source = {}
    for key in ("video", "subtitles"):
        if not source.get(key):
            errors.append(f"source.{key} is required")
    for key in ("width", "height", "fps"):
        _positive_number(source, key, "source", errors)
    source_duration = _positive_number(
        source, "duration_seconds", "source", errors
    )

    render_spec = plan.get("render_spec")
    if not isinstance(render_spec, dict):
        errors.append("render_spec is required")
        render_spec = {}
    render_fps = None
    for key in ("width", "height", "fps"):
        value = _positive_number(render_spec, key, "render_spec", errors)
        if key == "fps":
            render_fps = value

    _required_prompt(plan, "visual_direction", errors)
    _required_prompt(plan, "package_direction", errors)

    cues = plan.get("cues")
    if not isinstance(cues, list) or not cues:
        errors.append("at least one cue is required")
        return errors

    frame_ranges = []
    for cue in cues:
        cue_id = cue.get("id", "<unknown>")
        visual_prompt = cue.get("visual_prompt")
        if not isinstance(visual_prompt, str) or not visual_prompt.strip():
            errors.append(f"{cue_id}: visual_prompt is required")
        _validate_invariants(cue, errors)
        try:
            start_seconds = float(cue["start_seconds"])
            end_seconds = float(cue["end_seconds"])
            if render_fps is None:
                continue
            start_frame = round(start_seconds * render_fps)
            end_frame = round(end_seconds * render_fps)
            frame_ranges.append((cue_id, start_frame, end_frame))
            if abs(start_seconds * render_fps - start_frame) > 1e-6:
                errors.append(f"{cue_id}: start_seconds is not on render fps frame grid")
            if abs(end_seconds * render_fps - end_frame) > 1e-6:
                errors.append(f"{cue_id}: end_seconds is not on render fps frame grid")
            if end_frame <= start_frame:
                errors.append(f"{cue_id}: end_seconds must be after start_seconds")
        except (KeyError, TypeError, ValueError):
            errors.append(f"{cue_id}: start_seconds/end_seconds must be numbers")

    if frame_ranges and frame_ranges[0][1] != 0:
        errors.append("cue timeline must begin at frame 0")
    for (_, _, left_end), (right_id, right_start, _) in zip(
        frame_ranges, frame_ranges[1:]
    ):
        if left_end != right_start:
            errors.append(f"cue gap or overlap before {right_id}")
    if source_duration is not None and render_fps is not None and frame_ranges:
        if frame_ranges[-1][2] != round(source_duration * render_fps):
            errors.append("cue timeline must end at source.duration_seconds")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an approved prompt-first MotionTalk plan"
    )
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(json.loads(args.plan.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("MotionTalk prompt-first plan: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
