"""
Central configuration for the GTA V Brainrot Shorts pipeline.
Reads from .env file, provides sensible defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# ── Directories ──────────────────────────────────────────────
RAW_DIR = ROOT / "data" / "raw"
CLIPS_DIR = ROOT / "data" / "clips"
OUTPUT_DIR = ROOT / "data" / "output"

for d in [RAW_DIR, CLIPS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Clip download settings ───────────────────────────────────
YTDL_SEARCH_QUERY = _env("YTDL_SEARCH_QUERY", "gta v funny moments gameplay 1080p")
YTDL_MAX_DOWNLOADS = int(_env("YTDL_MAX_DOWNLOADS", "2"))
YTDL_FORMAT = _env("YTDL_FORMAT", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]")

# ── Clip processing ──────────────────────────────────────────
SCENE_THRESHOLD = float(_env("SCENE_THRESHOLD", "0.3"))
CLIP_MIN_DURATION = float(_env("CLIP_LENGTH_MIN", "15"))
CLIP_MAX_DURATION = float(_env("CLIP_LENGTH_MAX", "40"))

# ── Groq LLM ─────────────────────────────────────────────────
GROQ_API_KEY = _env("GROQ_API_KEY")
GROQ_MODEL = _env("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Edge TTS ─────────────────────────────────────────────────
TTS_VOICE = _env("EDGE_TTS_VOICE", "en-US-EricNeural")

# ── Brainrot style ───────────────────────────────────────────
BRAINROT_STYLE = _env("BRAINROT_STYLE", "chaotic")