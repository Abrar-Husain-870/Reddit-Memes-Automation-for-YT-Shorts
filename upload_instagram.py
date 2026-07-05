"""
Upload rendered GTA VI brainrot shorts to Instagram Reels.
⚠ Instagram's API is currently broken for automated logins.
   Manual upload is recommended instead.
"""
from __future__ import annotations

import sys
from pathlib import Path

import config


def upload_reel(
    video_path: Path,
    caption: str = "",
) -> str:
    """
    Upload a short to Instagram Reels.
    
    Instagram's API has been blocking automated logins (CSRF error)
    even from local PCs. Manual upload via the Instagram app or
    browser is the most reliable method.
    """
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return ""

    print(f"\n📍 Your video is ready at: {video_path}")
    print(f"   Caption: {caption[:80]}...")
    print()
    print("=" * 60)
    print("📱 MANUAL UPLOAD REQUIRED")
    print("=" * 60)
    print()
    print("Instagram's API is blocking automated uploads.")
    print("Please upload the video manually:")
    print()
    print("   1. Open the Instagram app on your phone")
    print(f"   2. Upload: {video_path.name}")
    print("   3. Paste this caption:")
    print(f"      {caption}")
    print()
    print("Or use the browser:")
    print("   1. Go to instagram.com and log in")
    print("   2. Click + → Select video file")
    print(f"   3. Choose: {video_path}")
    print("   4. Add caption and post")
    print("=" * 60)
    return ""


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="Path to MP4")
    ap.add_argument("--caption", default="GTA VI BRAINROT 🎮🔥", help="Reel caption")
    args = ap.parse_args()

    upload_reel(Path(args.video), args.caption)