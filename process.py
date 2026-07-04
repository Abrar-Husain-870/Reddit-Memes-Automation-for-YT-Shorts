"""
Extract short clips from downloaded gameplay videos using FFmpeg scene detection.
Focuses on quality — keeps clips in the 15-40 second range.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config


def _get_video_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return float(result.stdout.strip())


def _detect_scenes(path: Path, threshold: float = 0.3) -> list[float]:
    cmd = [
        "ffmpeg", "-i", str(path),
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    timestamps = []
    for line in result.stderr.splitlines():
        if "pts_time:" in line:
            try:
                parts = line.split()
                for p in parts:
                    if p.startswith("pts_time:"):
                        timestamps.append(float(p.split(":")[1]))
            except (ValueError, IndexError):
                continue
    return sorted(set(timestamps))


def extract_clips(
    video_path: Path,
    min_dur: float = 15,
    max_dur: float = 40,
) -> list[Path]:
    """
    Split a video into short clips using scene detection.
    Returns paths to extracted clips.
    """
    print(f"\n🎞 Processing: {video_path.name}")
    dur = _get_video_duration(video_path)
    print(f"   Duration: {dur:.1f}s")

    scenes = _detect_scenes(video_path)
    print(f"   Detected {len(scenes)} scene changes")

    boundaries = [0.0] + scenes + [dur]
    clips = []

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        clip_dur = end - start

        if clip_dur < min_dur:
            continue
        if clip_dur > max_dur:
            end = start + max_dur

        out_path = config.CLIPS_DIR / f"{video_path.stem}_clip_{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(end - start),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(out_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if out_path.exists() and out_path.stat().st_size > 500_000:
            clips.append(out_path)
            print(f"   🎬 Clip {i:03d}: {start:.1f}s → {end:.1f}s ({end-start:.1f}s)")

    return clips


def get_random_clip() -> Path | None:
    """Pick a random clip from the clips directory."""
    clips = sorted(config.CLIPS_DIR.glob("*.mp4"))
    if not clips:
        return None
    import random
    return random.choice(clips)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?", help="Path to video file (processes all raw videos if not specified)")
    args = ap.parse_args()

    if args.video:
        clips = extract_clips(Path(args.video))
    else:
        raw_videos = sorted(config.RAW_DIR.glob("*.*"))
        if not raw_videos:
            print("No raw videos found in data/raw/")
            sys.exit(1)
        clips = []
        for v in raw_videos:
            clips.extend(extract_clips(v))

    print(f"\n✅ Extracted {len(clips)} clip(s)")