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
    mg_cues = [
        cue
        for cue in plan.get("cues", [])
        if cue.get("visual") != "presenter-full-screen"
    ]
    for cue in mg_cues:
        invariants = cue.get("spec", {}).get("semantic_invariants")
        if not isinstance(invariants, list) or not invariants:
            errors.append(f"{cue.get('id', '<unknown>')}: semantic_invariants missing")

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
    if int(progress.get("height_px", 0)) < 24:
        errors.append("progress.height_px must be at least 24")
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
