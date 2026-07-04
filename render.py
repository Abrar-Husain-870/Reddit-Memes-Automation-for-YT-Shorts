"""
Render final 9:16 brainrot short with HIGH QUALITY.
- Lanczos upscale + unsharp for crisp 1080p
- Center-screen colorful ASS subtitles with word-by-word timing
- Cascading quality presets (slow → medium → fast)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import config

RENDER_TIMEOUT = 600
FFPROBE_TIMEOUT = 60


def _get_dur(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=FFPROBE_TIMEOUT,
    )
    return float(r.stdout.strip())


def _build_word_timings(
    words: list[str],
    audio_dur: float,
    sentence_timings: list[dict] | None = None,
) -> list[tuple[float, float, str]]:
    """Build (start_sec, end_sec, word) tuples from sentence timestamps."""
    result = []
    n = len(words)

    if sentence_timings and len(sentence_timings) > 0:
        word_idx = 0
        for sent in sentence_timings:
            s_text = sent.get("text", "")
            s_start = sent.get("offset_ms", 0) / 1000
            s_dur = sent.get("duration_ms", 1000) / 1000
            s_end = s_start + s_dur

            s_words = [w for w in s_text.split() if w.strip()]
            n_s_words = len(s_words)

            if n_s_words > 0 and word_idx < n:
                w_per = s_dur / n_s_words
                for j in range(n_s_words):
                    if word_idx >= n:
                        break
                    ws = s_start + j * w_per
                    we = min(ws + w_per, s_end)
                    result.append((ws, we, words[word_idx]))
                    word_idx += 1

        # Remaining words
        remaining = n - word_idx
        if remaining > 0:
            last_end = result[-1][1] if result else audio_dur
            time_left = audio_dur - last_end
            w_per = time_left / max(remaining, 1)
            for j in range(remaining):
                ws = last_end + j * w_per
                we = min(ws + w_per, audio_dur)
                result.append((ws, we, words[word_idx]))
                word_idx += 1
    else:
        w_per = audio_dur / max(n, 1)
        for i, w in enumerate(words):
            ws = i * w_per
            we = min((i + 1) * w_per, audio_dur)
            result.append((ws, we, w))

    return result


def render(
    clip_path: Path,
    audio_path: Path,
    narration: str,
    output_path: Path | None = None,
    sentence_timings: list[dict] | None = None,
) -> Path:
    if output_path is None:
        output_path = config.OUTPUT_DIR / "final_short.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clip_dur = _get_dur(clip_path)
    audio_dur = _get_dur(audio_path)
    print(f"🎬 {clip_dur:.0f}s clip + {audio_dur:.0f}s audio")

    # Clean narration for subtitles
    clean = narration.replace("**", "").replace("__", "").replace("*", "")
    clean = re.sub(r'[^\w\s\'",.!?;:\-]', "", clean).strip()
    if not clean:
        clean = "GTA VI BRAINROT"
    words = clean.split()

    timings = _build_word_timings(words, audio_dur, sentence_timings)
    print(f"   {len(words)} words, {audio_dur:.0f}s audio, {len(sentence_timings or [])} sentences")

    # ── Build ASS subtitles ──
    ass = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Impact,100,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,5,5,0,0,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    colors = [
        "&H00FFFFFF", "&H0000FFD7", "&H00FF69B4", "&H0000FF7F",
        "&H00FF4500", "&H00937FDC", "&H0000BFFF", "&H00FFD700",
    ]

    for i, (ts, te, w) in enumerate(timings):
        def _t(s):
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            return f"{h}:{m:02d}:{s % 60:05.2f}"
        c = colors[i % len(colors)]
        ass += f"Dialogue: 0,{_t(ts)},{_t(te)},Default,,0,0,0,,{{\\\\c{c}\\an5}}{w}\n"

    ass_path = config.OUTPUT_DIR / "captions.ass"
    ass_path.write_text(ass, encoding="utf-8")

    # ── Render with cascading quality presets ──
    ass_safe = "data/output/captions.ass"

    def _build_cmd(preset: str, crf: str, bv: str, ba: str) -> list[str]:
        return [
            "ffmpeg", "-y",
            "-i", str(clip_path),
            "-i", str(audio_path),
            "-filter_complex",
            f"[0:v]"
            f"scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"unsharp=5:5:1.0:5:5:0.0,"
            f"subtitles={ass_safe}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", preset, "-crf", crf,
            "-b:v", bv, "-maxrate", bv, "-bufsize", str(int(bv.rstrip("M")) * 2) + "M",
            "-profile:v", "high", "-level", "4.2",
            "-c:a", "aac", "-b:a", ba, "-ar", "48000",
            "-shortest", "-movflags", "+faststart",
            str(output_path),
        ]

    presets = [
        ("slow", "16", "12M", "256k"),
        ("medium", "16", "10M", "256k"),
        ("fast", "20", "6M", "192k"),
    ]

    for preset, crf, bv, ba in presets:
        cmd = _build_cmd(preset, crf, bv, ba)
        print(f"   Rendering ({preset}, {bv}, crf {crf})…")
        try:
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=RENDER_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f"   ⚠ Timed out, trying lower preset")
            continue
        if r.returncode == 0:
            break
        print(f"   ⚠ Failed (code {r.returncode}), trying lower preset")
    else:
        print("❌ All render presets failed")
        sys.exit(1)

    if output_path.exists():
        mb = output_path.stat().st_size / 1_048_576
        d = _get_dur(output_path)
        print(f"   ✅ {output_path.name} ({mb:.0f}MB, {d:.0f}s)")
    return output_path


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("--clip", required=True)
    a.add_argument("--audio", required=True)
    a.add_argument("--narration", default="GTA VI BRAINROT")
    args = a.parse_args()
    render(Path(args.clip), Path(args.audio), args.narration)