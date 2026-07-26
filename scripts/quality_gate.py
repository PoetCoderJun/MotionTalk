#!/usr/bin/env python3
"""Run MotionTalk's final evidence-backed quality gates."""

from __future__ import annotations

import argparse
import json
import math
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


def command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def probe(path: Path) -> dict:
    return json.loads(
        command(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        ).stdout
    )


def stream_md5(path: Path) -> str:
    result = command(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-c",
            "copy",
            "-f",
            "streamhash",
            "-hash",
            "md5",
            "-",
        ]
    )
    match = re.search(r"MD5=([0-9a-fA-F]+)", result.stdout)
    if not match:
        raise RuntimeError(f"no audio stream MD5 returned for {path}")
    return match.group(1).lower()


def video_stream(data: dict) -> dict:
    return next(stream for stream in data["streams"] if stream["codec_type"] == "video")


def duration(data: dict) -> float:
    return float(data["format"]["duration"])


def frame_count(stream: dict, duration_seconds: float) -> int:
    if stream.get("nb_read_frames") not in (None, "N/A"):
        return int(stream["nb_read_frames"])
    if stream.get("nb_frames") not in (None, "N/A"):
        return int(stream["nb_frames"])
    numerator, denominator = map(int, stream["avg_frame_rate"].split("/"))
    return round(duration_seconds * numerator / denominator)


def all_passed_checklist(
    path: Path, accepted_keys: tuple[str, ...]
) -> tuple[bool, dict]:
    if not path.is_file():
        return False, {"path": str(path), "reason": "missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = (
        payload
        if isinstance(payload, list)
        else next(
            (
                payload[key]
                for key in accepted_keys
                if isinstance(payload.get(key), list)
            ),
            [],
        )
    )
    passed = bool(records) and all(record.get("status") == "passed" for record in records)
    return passed, {"path": str(path), "records": len(records), "all_passed": passed}


def extract_frame(video: Path, at: float, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = command(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{max(0, at):.6f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(destination),
        ],
        check=False,
    )
    return result.returncode == 0 and destination.is_file() and destination.stat().st_size > 0


def find_semantic_checklist(output_dir: Path) -> Path:
    candidates = (
        output_dir / "semantic-checklist.v1.json",
        output_dir / "proof-frames" / "checklists" / "semantic-checklist.v1.json",
    )
    return next((path for path in candidates if path.is_file()), candidates[0])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a packaged MotionTalk video and write quality-report.v1.json"
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--final", type=Path, help="Override packaged video path")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Pacing multiplier used during packaging",
    )
    args = parser.parse_args()
    if not 1.0 <= args.speed <= 2.0:
        raise ValueError("--speed must be between 1.0 and 2.0")

    output_dir = args.output_dir.resolve()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    project_id = plan["project_id"]
    final_path = (
        args.final.resolve()
        if args.final
        else output_dir / "final" / f"{project_id}-packaged.mp4"
    )
    source_path = Path(plan["source"]["video"])
    report_path = output_dir / "quality-report.v1.json"
    evidence_root = output_dir / "proof-frames" / "final"
    evidence_root.mkdir(parents=True, exist_ok=True)
    checks: dict[str, str] = {}
    evidence: dict[str, object] = {}

    try:
        source_probe = probe(source_path)
        final_probe = probe(final_path)
        source_v = video_stream(source_probe)
        final_v = video_stream(final_probe)
        source_duration = duration(source_probe)
        final_duration = duration(final_probe)
        source_frames = frame_count(source_v, source_duration)
        final_frames = frame_count(final_v, final_duration)
        fps_num, fps_den = map(int, final_v["avg_frame_rate"].split("/"))
        fps = fps_num / fps_den
        final_audio = sum(s["codec_type"] == "audio" for s in final_probe["streams"])
        expected_duration = source_duration / args.speed
        expected_frames = round(source_frames / args.speed)
        structure_ok = (
            abs(expected_duration - final_duration) <= 0.1
            and abs(expected_frames - final_frames) <= math.ceil(0.1 * fps)
            and int(final_v["width"]) == int(plan["source"]["width"])
            and int(final_v["height"]) == int(plan["source"]["height"])
            and final_audio == 1
            and sum(s["codec_type"] == "video" for s in final_probe["streams"]) == 1
        )
        checks["structure"] = "passed" if structure_ok else "failed"
        evidence["structure"] = {
            "source_duration": source_duration,
            "speed": args.speed,
            "expected_packaged_duration": expected_duration,
            "packaged_duration": final_duration,
            "source_frames": source_frames,
            "expected_packaged_frames": expected_frames,
            "packaged_frames": final_frames,
            "fps": fps,
            "resolution": [final_v["width"], final_v["height"]],
            "packaged_audio_tracks": final_audio,
            "ffprobe": final_probe,
        }
    except Exception as exc:
        checks["structure"] = "failed"
        evidence["structure"] = {"error": str(exc)}

    decode = command(
        ["ffmpeg", "-v", "error", "-i", str(final_path), "-f", "null", "-"],
        check=False,
    )
    decode_ok = decode.returncode == 0 and not decode.stderr.strip()
    checks["full_decode"] = "passed" if decode_ok else "failed"
    evidence["full_decode"] = {
        "returncode": decode.returncode,
        "stderr": decode.stderr,
        "command": f"ffmpeg -v error -i {final_path} -f null -",
    }

    try:
        if args.speed == 1.0:
            source_hash = stream_md5(source_path)
            final_hash = stream_md5(final_path)
            checks["audio_identity"] = (
                "passed" if source_hash == final_hash else "failed"
            )
            evidence["audio_identity"] = {
                "mode": "packet-copy",
                "source_stream_md5": source_hash,
                "packaged_stream_md5": final_hash,
            }
        else:
            final_probe = probe(final_path)
            audio_streams = [
                item for item in final_probe["streams"] if item["codec_type"] == "audio"
            ]
            audio_duration = float(audio_streams[0].get("duration", 0))
            expected = float(plan["source"]["duration_seconds"]) / args.speed
            audio_ok = len(audio_streams) == 1 and abs(audio_duration - expected) <= 0.1
            checks["audio_identity"] = "passed" if audio_ok else "failed"
            evidence["audio_identity"] = {
                "mode": "source-audio-atempo",
                "speed": args.speed,
                "expected_duration": expected,
                "packaged_audio_duration": audio_duration,
                "audio_tracks": len(audio_streams),
            }
    except Exception as exc:
        checks["audio_identity"] = "failed"
        evidence["audio_identity"] = {"error": str(exc)}

    window_frames: list[dict] = []
    window_ok = True
    for cue in plan["cues"]:
        if cue["visual"] == "presenter-full-screen":
            continue
        start = float(cue["start_seconds"]) / args.speed
        end = float(cue["end_seconds"]) / args.speed
        delivery_duration = float(plan["source"]["duration_seconds"]) / args.speed
        moments = {
            "before": max(0, start - 0.05),
            "inside": (start + end) / 2,
            "after": min(delivery_duration - 0.001, end + 0.05),
        }
        for label, moment in moments.items():
            destination = evidence_root / "windows" / f"{cue['id']}-{label}.jpg"
            ok = extract_frame(final_path, moment, destination)
            window_ok &= ok
            window_frames.append(
                {
                    "cue_id": cue["id"],
                    "kind": label,
                    "time": moment,
                    "path": str(destination),
                    "created": ok,
                }
            )
    checks["window_boundaries"] = (
        "passed" if window_ok and bool(window_frames) else "failed"
    )
    evidence["window_boundaries"] = {"frames": window_frames}

    aspect_ok, aspect_evidence = all_passed_checklist(
        output_dir / "aspect-occlusion-checklist.v1.json", ("checks", "items")
    )
    checks["aspect_and_occlusion"] = "passed" if aspect_ok else "failed"
    evidence["aspect_and_occlusion"] = aspect_evidence

    package_frames: list[dict] = []
    package_ok = bool(plan.get("chapters"))
    package_times = {
        "opening": 0.15,
        "middle": float(plan["source"]["duration_seconds"]) / args.speed / 2,
        "near-end": float(plan["source"]["duration_seconds"]) / args.speed - 0.25,
    }
    for chapter in plan.get("chapters", []):
        chapter_start = float(chapter["start_seconds"]) / args.speed
        package_times[f"{chapter['id']}-start-02"] = chapter_start + 0.02
        package_times[f"{chapter['id']}-start-15"] = chapter_start + 0.15
        package_times[f"{chapter['id']}-start-35"] = chapter_start + 0.35
    for label, moment in package_times.items():
        destination = evidence_root / "package" / f"{label}.jpg"
        ok = extract_frame(final_path, moment, destination)
        package_ok &= ok
        package_frames.append(
            {"kind": label, "time": moment, "path": str(destination), "created": ok}
        )
    package_manual_ok, package_manual = all_passed_checklist(
        output_dir / "package-checklist.v1.json", ("checks", "items")
    )
    package_ok &= package_manual_ok
    checks["package_progress"] = "passed" if package_ok else "failed"
    evidence["package_progress"] = {
        "chapter_count": len(plan.get("chapters", [])),
        "progress_segment_count": len(plan.get("chapters", [])),
        "frames": package_frames,
        "visual_checklist": package_manual,
    }

    semantic_ok, semantic_evidence = all_passed_checklist(
        find_semantic_checklist(output_dir), ("checks", "items", "invariants")
    )
    checks["semantic_invariants"] = "passed" if semantic_ok else "failed"
    evidence["semantic_invariants"] = semantic_evidence

    log_files = sorted((output_dir / "logs").glob("*.log"))
    encoder_hits: list[str] = []
    for log_path in log_files:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        if re.search(
            r"encoder\s*:\s*[^\n]*h264_videotoolbox", text, re.IGNORECASE
        ):
            encoder_hits.append(str(log_path))
    encoder_ok = bool(encoder_hits) if platform.system() == "Darwin" else bool(log_files)
    checks["encoder_evidence"] = "passed" if encoder_ok else "failed"
    evidence["encoder_evidence"] = {
        "required_encoder": (
            "h264_videotoolbox" if platform.system() == "Darwin" else "logged encoder"
        ),
        "matching_logs": encoder_hits,
        "scanned_logs": [str(path) for path in log_files],
    }

    final_entries = sorted((output_dir / "final").iterdir())
    forbidden = [
        item
        for item in final_entries
        if not item.is_file()
        or item.suffix.lower() != ".mp4"
        or any(
            token in item.name.lower()
            for token in ("preview", "540p", "clean-master", "clean-composite")
        )
    ]
    cleanliness_ok = (
        len(final_entries) == 1
        and final_entries[0].resolve() == final_path.resolve()
        and final_entries[0].is_file()
        and not forbidden
    )
    checks["delivery_cleanliness"] = "passed" if cleanliness_ok else "failed"
    evidence["delivery_cleanliness"] = {
        "final_entries": [str(item) for item in final_entries],
        "forbidden_entries": [str(item) for item in forbidden],
    }

    passed = all(value == "passed" for value in checks.values())
    report = {
        "schema_version": "motiontalk.quality-report.v1",
        "packaged_video": str(final_path.relative_to(output_dir)),
        "checks": checks,
        "evidence": evidence,
        "status": "passed" if passed else "failed",
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if passed:
        for candidate in (
            output_dir / "work" / f"{project_id}-clean-composite.mp4",
            output_dir / "work" / f"{project_id}-clean-video-only.mp4",
            output_dir / "work" / f"{project_id}-packaged-video-only.mp4",
        ):
            candidate.unlink(missing_ok=True)
        shutil.rmtree(output_dir / "work" / "composite-segments", ignore_errors=True)
        shutil.rmtree(output_dir / "work" / "package-chapters", ignore_errors=True)
    print(report_path)
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
