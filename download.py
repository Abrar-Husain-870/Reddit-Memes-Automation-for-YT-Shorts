"""
Download GTA V gameplay clips from YouTube using yt-dlp.
Run this locally on your PC (YouTube blocks GitHub runners).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config


def download_clips(search_query: str = "", max_downloads: int = 2) -> list[Path]:
    """
    Download fresh GTA V gameplay clips from YouTube.
    Returns list of downloaded file paths.
    """
    query = search_query or config.YTDL_SEARCH_QUERY
    output_tpl = str(config.RAW_DIR / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--format", config.YTDL_FORMAT,
        "--output", output_tpl,
        "--max-downloads", str(max_downloads),
        "--no-playlist",
        "--print", "after_move:filepath",
        "--extractor-retries", "2",
        f"ytsearch{max_downloads}:{query}",
    ]

    print(f"🔍 Searching YouTube: {query}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("⚠ Download timed out. Try again later or use a different network.")
        return []

    if result.returncode != 0:
        print(f"⚠ Download failed: {result.stderr[:200]}")
        return []

    downloaded = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            p = Path(line)
            if p.exists():
                downloaded.append(p)
                print(f"   ✅ {p.name}")

    print(f"   Downloaded {len(downloaded)} video(s)")
    return downloaded


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="gta v funny moments gameplay 1080p")
    ap.add_argument("--count", type=int, default=2)
    args = ap.parse_args()
    download_clips(args.query, args.count)