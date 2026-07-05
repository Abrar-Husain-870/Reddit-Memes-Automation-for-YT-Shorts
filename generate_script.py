"""
Generate brainrot scripts for GTA V clips using Groq LLM (free tier).
Target: 70-120 words, funny + engaging brainrot style.
No emojis — clean text only for TTS compatibility.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from groq import Groq

import config

USER_SYSTEM_PROMPT = (
    "You write viral brainrot short-form video scripts. "
    "Your style: chaotic, FUNNY, relatable gamer humor. "
    "CRITICAL: Do NOT use any emojis or special unicode characters. "
    "Use ONLY plain text words and punctuation. "
    "Structure the script as a coherent MINI-STORY with: "
    "1) A setup (what's happening) "
    "2) An escalation (something goes wrong) "
    "3) A punchline (funny reaction) "
    "Use short punchy lines. Each line is 5-10 words. "
    "Total script is EXACTLY 8-15 lines (70-120 words total). "
    "This is for a 25-35 second voiceover. "
    "Use ALL CAPS for the FUNNY/IMPORTANT words. "
    "Sound like a GENUINE GAMER reacting to what's happening on screen. "
    "Examples of the style (but be original): "
    "'Bro JUST WATCH this NPC... he's about to DO something STUPID... oh NO he DID NOT just do that HAHAHA' "
    "'Me: driving NORMAL... GTA V: LETS THROW A TRASH TRUCK at your face' "
    "Be FUNNY. Be RELATABLE. Think like a gamer streaming to friends."
)


def _strip_emojis(text: str) -> str:
    """Remove emoji characters from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # misc
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def generate_brainrot_script(
    clip_description: str = "",
    style: str = "chaotic",
) -> tuple[str, str]:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not set!")
        sys.exit(1)

    client = Groq(api_key=api_key)

    user_prompt = (
        f"Write a FUNNY brainrot script for this GTA V gameplay clip.\n\n"
        f"Requirements:\n"
        f"- 8-15 short punchy lines (total 70-120 words)\n"
        f"- Tell a mini-story: setup, escalation, punchline\n"
        f"- Use ALL CAPS for dramatic/funny emphasis\n"
        f"- NO EMOJIS whatsoever - plain text only\n"
        f"- Sound like a real gamer reacting, not a robot\n"
        f"- Reference things that happen in GTA: NPCs, cops, chaos, physics glitches, etc.\n"
        f"- The funnier the better\n\n"
        f"Format EXACTLY like this:\n"
        f"NARRATION: <your 70-120 word script without any emojis>\n"
        f"TITLE: <clickbait title under 60 chars>"
    )

    print(f"🤖 Groq: generating {style} brainrot script (target 70-120 words)…")

    best_narration = ""
    best_title = "GTA V BRAINROT"
    best_wc = 0

    for attempt in range(2):
        try:
            completion = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": USER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.95,
                max_tokens=800,
                timeout=30,
            )
        except Exception as e:
            print(f"   ⚠ Groq API error (attempt {attempt+1}): {e}")
            if attempt == 1:
                best_narration = "When the GTA V physics engine decides to absolutely DESTROY your day. Like bro I was just driving NORMAL and then BOOM a trash truck spawns on my head. HAHAHA this game is PEAK chaos I love it."
                best_title = "GTA V BRAINROT"
                best_wc = len(best_narration.split())
                print(f"   ⚠ Using fallback narration ({best_wc} words)")
                break
            continue

        response = completion.choices[0].message.content.strip()

        narration = ""
        title = "GTA V BRAINROT"
        for line in response.splitlines():
            line = line.strip()
            if line.upper().startswith("NARRATION:"):
                narration = line.split(":", 1)[1].strip()
            elif line.upper().startswith("TITLE:"):
                title = line.split(":", 1)[1].strip()[:60]

        if not narration:
            narration = response
            for p in ["NARRATION:", "Narration:", "narration:"]:
                if narration.upper().startswith(p.upper()):
                    narration = narration[len(p):].strip()

        # Strip emojis and markdown formatting
        narration = _strip_emojis(narration)
        narration = narration.replace("**", "").replace("__", "").replace("*", "")
        title = _strip_emojis(title)
        title = title.replace("**", "").replace("__", "").replace("*", "")

        wc = len(narration.split())
        if wc > best_wc:
            best_narration = narration
            best_title = title
            best_wc = wc

        if wc >= 70:
            break
        user_prompt += "\n\nToo short! MUST be 70-120 words. Add more funny lines."

    print(f"   📝 {best_wc} words")
    return best_narration, best_title


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="chaotic")
    args = ap.parse_args()
    n, t = generate_brainrot_script(style=args.style)
    print(f"\n✅ {len(n.split())} words: {n[:120]}...")
    print(f"📌 {t}")