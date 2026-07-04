"""
Upload rendered GTA VI brainrot shorts to Instagram Reels.
Uses instagrapi (unofficial but free) for posting.
All API calls have timeouts to prevent indefinite hangs on CI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import config

IG_TIMEOUT = 60  # 1 minute timeout for Instagram operations


def _challenge_handler(username, challenge_type):
    """Handle Instagram login challenges (verification code, etc.)."""
    print(f"\n⚠ Instagram requires account verification for {username}")
    print(f"   Challenge type: {challenge_type}")
    code = input("   Enter the verification code sent to your email/phone: ").strip()
    return code


def _login_with_retry(cl, username, password, settings_path, max_retries=2):
    """Attempt login with challenge handling and retry logic."""
    for attempt in range(max_retries):
        try:
            cl.login(username, password)
            cl.dump_settings(str(settings_path))
            return True
        except Exception as e:
            err_str = str(e)
            if "challenge" in err_str.lower() or "Challenge" in err_str:
                print(f"   ⚠ Challenge required (attempt {attempt + 1})")
                # Try to resolve the challenge
                try:
                    # instagrapi stores challenge info internally
                    cl.challenge_code_handler = _challenge_handler
                    # Some challenge types need manual resolution
                    if "redirect" in err_str or "STEP_NAME" in err_str:
                        print("   ⚠ Instagram requires a security check on their website.")
                        print("   📱 Open Instagram on your phone and follow the security prompt,")
                        print("      or log in at instagram.com on a browser and approve the login.")
                        print("   🔄 Then re-run the pipeline.")
                        return False
                except Exception:
                    pass
            else:
                print(f"   ⚠ Login error: {e}")
                if attempt < max_retries - 1:
                    print("   Retrying...")
                else:
                    return False
    return False


def upload_reel(
    video_path: Path,
    caption: str = "",
) -> str:
    """
    Upload a short to Instagram Reels using instagrapi.
    
    Args:
        video_path: Path to the rendered MP4.
        caption: Reel caption with hashtags.
    
    Returns:
        Media ID on success, empty string on failure.
    """
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return ""

    if not config.IG_USERNAME or not config.IG_PASSWORD:
        print("⚠ IG_USERNAME / IG_PASSWORD not set — skipping Instagram upload")
        return ""

    print(f"📱 Instagram: logging in as {config.IG_USERNAME}…")

    try:
        from instagrapi import Client
        from instagrapi.exceptions import ChallengeError, LoginRequired, ClientError

        cl = Client()
        # Use a persistent settings file so Instagram recognizes this device across runs
        settings_path = config.CACHE_DIR / "ig_settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)

        if settings_path.exists():
            try:
                cl.load_settings(str(settings_path))
                print("   Loaded saved session")
            except Exception:
                print("   Session expired, logging in fresh")

        # Set a realistic user agent to avoid detection
        cl.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
        cl.set_country_code(1)
        cl.set_locale("en_US")

        # Set a timeout on IG requests
        import socket
        socket.setdefaulttimeout(IG_TIMEOUT)
        cl.delay_range = [1, 3]  # Respect rate limits

        # Try login
        logged_in = _login_with_retry(cl, config.IG_USERNAME, config.IG_PASSWORD, settings_path)
        if not logged_in:
            print("⚠ Instagram login failed — skipping upload")
            return ""

        print("   ✅ Logged in")

        # Build caption with hashtags
        hashtags = (
            "#GTAVI #GTA6 #GamingShorts #Brainrot #GTA6Gameplay "
            "#GamingMemes #Reels #GTA6Moment #RockstarGames"
        )
        full_caption = f"{caption}\n.\n{hashtags}" if caption else hashtags

        print("   📤 Uploading Reel…")
        result = cl.clip_upload(str(video_path), full_caption)
        media_id = result.id
        print(f"   ✅ Uploaded! Media ID: {media_id}")
        return str(media_id)

    except ImportError:
        print("⚠ instagrapi not installed. Install with: pip install instagrapi")
        return ""
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}")
        return ""


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="Path to MP4")
    ap.add_argument("--caption", default="GTA VI BRAINROT 🎮🔥", help="Reel caption")
    args = ap.parse_args()

    upload_reel(Path(args.video), args.caption)