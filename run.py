#!/usr/bin/env python3
"""
GTA V Brainrot Shorts — Local Pipeline.
1. Download gameplay clips (yt-dlp)
2. Extract short clips (FFmpeg scene detection)
3. Generate brainrot script (Groq LLM)
4. Synthesize voiceover (Edge TTS)
5. Render 9:16 short with captions (FFmpeg)

No automated uploads — you upload manually to YouTube/Instagram.
"""
from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path

import config
from download import download_clips
from process import extract_clips, get_random_clip
from script import generate
from voiceover import synthesize
from render import render

STYLES = ["chaotic", "meme", "story", "npc"]


def _pick_style(force: str | None) -> str:
    if force and force != "random":
        return force
    return random.choice(STYLES)


def main() -> None:
    ap = argparse.ArgumentParser(description="GTA V Brainrot Short — Local Pipeline")
    ap.add_argument("--skip-download", action="store_true", help="Skip downloading, use existing clips")
    ap.add_argument("--style", default="random", choices=["random", *STYLES],
                    help="Brainrot style (default: random)")
    ap.add_argument("--query", default=config.YTDL_SEARCH_QUERY,
                    help="YouTube search query for downloading clips")
    ap.add_argument("--count", type=int, default=config.YTDL_MAX_DOWNLOADS,
                    help="Number of videos to download")
    args = ap.parse_args()

    style = _pick_style(args.style)
    print("=" * 60)
    print(f"🎮 GTA V BRAINROT SHORTS  |  Style: {style.upper()}")
    print("=" * 60)

    # Step 1: Download
    if not args.skip_download:
        print(f"\n📥 Step 1/5: Downloading gameplay clips…")
        download_clips(args.query, args.count)
    else:
        print(f"\n📥 Step 1/5: Using existing clips")

    # Step 2: Process
    print(f"\n✂️  Step 2/5: Extracting short clips…")
    raw_videos = sorted(config.RAW_DIR.glob("*.*"))
    clips = []
    for v in raw_videos:
        clips.extend(extract_clips(v))
    if not clips:
        print("⚠ No clips extracted. Make sure you have videos in data/raw/")
        print("   Download first: python download.py --count 2")
        sys.exit(1)

    # Step 3: Pick clip
    print(f"\n🎲 Step 3/5: Selecting a clip…")
    clip = get_random_clip()
    if not clip:
        print("❌ No clips found in data/clips/")
        sys.exit(1)
    print(f"   Selected: {clip.name}")

    # Step 4: Generate script
    print(f"\n🧠 Step 4/5: Generating {style} script…")
    narration, title = generate(style=style)

    # Step 5: Voiceover
    print(f"\n🔊 Step 5/5: Synthesizing voiceover…")
    audio_path = config.OUTPUT_DIR / "voiceover.mp3"
    audio_dur, sentence_timings = synthesize(narration, output_path=audio_path)

    # Step 6: Render
    print(f"\n🎬 Rendering final short…")
    video_path = config.OUTPUT_DIR / "final_short.mp4"
    render(clip, audio_path, narration, output_path=video_path,
           sentence_timings=sentence_timings)

    print(f"\n{'=' * 60}")
    print(f"✅ DONE!  ({style.upper()} style)")
    print(f"   Video: {video_path}")
    print(f"   Title: {title}")
    print(f"{'=' * 60}")
    print(f"\n📤 Upload manually to YouTube/Instagram when ready!")


if __name__ == "__main__":
    main()