"""
Synthesize voiceover audio using Edge TTS (free, no API key needed).
Returns sentence-level timings for word-by-word captions.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import config

TTS_TIMEOUT = 120
FFPROBE_TIMEOUT = 30


class SentenceTiming(TypedDict):
    text: str
    offset_ms: int
    duration_ms: int


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True, timeout=FFPROBE_TIMEOUT,
    ).strip()
    return float(out)


async def _synthesize(text: str, out_path: Path, voice: str) -> list[SentenceTiming]:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    sentences: list[SentenceTiming] = []

    with open(out_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sentences.append(SentenceTiming(
                    text=chunk["text"],
                    offset_ms=int(chunk["offset"]) // 10_000,
                    duration_ms=int(chunk["duration"]) // 10_000,
                ))
    return sentences


def synthesize(
    narration: str,
    output_path: Path | None = None,
    voice: str | None = None,
) -> tuple[float, list[SentenceTiming]]:
    if output_path is None:
        output_path = config.OUTPUT_DIR / "voiceover.mp3"
    voice = voice or config.TTS_VOICE
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🔊 Edge TTS: synthesizing voiceover ({voice})…")
    try:
        sentences = asyncio.run(
            asyncio.wait_for(
                _synthesize(narration, output_path, voice),
                timeout=TTS_TIMEOUT,
            )
        )
    except asyncio.TimeoutError:
        print(f"   ⚠ TTS timed out. Check your internet connection.")
        sys.exit(1)

    total_dur = _ffprobe_duration(output_path)
    print(f"   Audio: {total_dur:.1f}s ({len(sentences)} sentences)")
    return total_dur, sentences


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="GTA V BRAINROT")
    args = ap.parse_args()
    dur, timings = synthesize(args.text)
    print(f"\n✅ Voiceover: {dur:.1f}s")
    for t in timings:
        print(f"   [{t['offset_ms'] / 1000:.1f}s] {t['text']}")