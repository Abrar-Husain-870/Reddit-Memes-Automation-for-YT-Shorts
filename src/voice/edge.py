import asyncio
import subprocess
from pathlib import Path
from typing import Tuple, List

import config
from src.logger import logger
from src.voice.base import BaseVoiceProvider, SentenceTiming

# Timeout settings
TTS_TIMEOUT = 120
FFPROBE_TIMEOUT = 30


def _ffprobe_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
            timeout=FFPROBE_TIMEOUT,
        ).strip()
        return float(out)
    except Exception as e:
        logger.error(f"ffprobe failed to read audio duration: {e}")
        return 0.0


async def _synthesize_with_timing(
    text: str,
    out_path: Path,
    voice: str,
) -> List[SentenceTiming]:
    """Synthesize speech with sentence-level timestamps using edge-tts."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    sentences: List[SentenceTiming] = []

    with open(out_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sentences.append(
                    SentenceTiming(
                        text=chunk["text"],
                        offset_ms=int(chunk["offset"]) // 10_000,
                        duration_ms=int(chunk["duration"]) // 10_000,
                    )
                )

    return sentences


class EdgeVoiceProvider(BaseVoiceProvider):
    """Microsoft Edge TTS Voice Provider with male preference and female fallback."""

    PREFERRED_MALE_VOICES = [
        "en-US-AndrewNeural",
        "en-US-GuyNeural",
        "en-US-ChristopherNeural",
        "en-US-EricNeural",
        "en-GB-RyanNeural",
    ]

    FALLBACK_FEMALE_VOICES = [
        "en-US-AvaNeural",
        "en-US-EmmaNeural",
        "en-US-JennyNeural",
    ]

    def synthesize(
        self, 
        text: str, 
        output_path: Path, 
        voice: str | None = None
    ) -> Tuple[float, List[SentenceTiming]]:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build candidate voice order:
        # 1. Configured/requested voice (if male) or default male voices
        # 2. Remaining preferred male voices
        # 3. Fallback female voices
        candidate_voices: List[str] = []
        preferred = voice or config.TTS_VOICE or "en-US-AndrewNeural"
        if preferred:
            candidate_voices.append(preferred)

        for mv in self.PREFERRED_MALE_VOICES:
            if mv not in candidate_voices:
                candidate_voices.append(mv)

        for fv in self.FALLBACK_FEMALE_VOICES:
            if fv not in candidate_voices:
                candidate_voices.append(fv)

        last_error = None
        for v in candidate_voices:
            is_female = v in self.FALLBACK_FEMALE_VOICES
            if is_female:
                logger.warning(f"Male voices unavailable or failed. Falling back to female voice: {v}")
            else:
                logger.info(f"Synthesizing voiceover with Edge TTS (male voice: {v})")

            try:
                sentences = asyncio.run(
                    asyncio.wait_for(
                        _synthesize_with_timing(text, output_path, v),
                        timeout=TTS_TIMEOUT,
                    )
                )
                duration = _ffprobe_duration(output_path)
                if duration > 0.1:
                    voice_type = "female fallback" if is_female else "male"
                    logger.info(
                        f"Generated Edge TTS voiceover using {voice_type} voice '{v}': "
                        f"{duration:.2f}s ({len(sentences)} sentences)"
                    )
                    return duration, sentences
            except Exception as e:
                logger.warning(f"Edge TTS voice '{v}' failed: {e}. Trying next available voice...")
                last_error = e

        if last_error:
            raise last_error
        raise RuntimeError("All candidate Edge TTS voices failed to synthesize audio.")
