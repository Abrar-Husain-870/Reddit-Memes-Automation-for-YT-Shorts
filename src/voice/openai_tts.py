import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Tuple, List

import config
from src.logger import logger
from src.voice.base import BaseVoiceProvider, SentenceTiming
from src.voice.edge import _ffprobe_duration
from src.voice.helpers import approximate_sentence_timings


class OpenAITTSVoiceProvider(BaseVoiceProvider):
    """OpenAI TTS Provider using standard REST API."""

    def __init__(self) -> None:
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not configured. OpenAITTSVoiceProvider will fail.")

    def synthesize(
        self, 
        text: str, 
        output_path: Path, 
        voice: str | None = None
    ) -> Tuple[float, List[SentenceTiming]]:
        voice_name = voice or config.TTS_VOICE or "onyx"
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        candidate_voices = []
        preferred = voice or config.TTS_VOICE or "onyx"
        if preferred:
            candidate_voices.append(preferred)
        for mv in ["onyx", "echo", "fable"]:
            if mv not in candidate_voices:
                candidate_voices.append(mv)
        for fv in ["nova", "shimmer", "alloy"]:
            if fv not in candidate_voices:
                candidate_voices.append(fv)

        last_error = None
        for voice_name in candidate_voices:
            is_female = voice_name in ["nova", "shimmer", "alloy"]
            voice_type = "female fallback" if is_female else "male"
            logger.info(f"Synthesizing voiceover with OpenAI TTS ({voice_type} voice: {voice_name})")
            
            data = {
                "model": config.OPENAI_TTS_MODEL,
                "input": text,
                "voice": voice_name
            }
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode("utf-8"), 
                headers=headers, 
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(response.read())
                    break
            except Exception as e:
                logger.warning(f"OpenAI TTS voice '{voice_name}' failed: {e}. Trying next...")
                last_error = e
        else:
            if last_error:
                raise last_error
            raise RuntimeError("All OpenAI TTS candidate voices failed.")
            
        duration = _ffprobe_duration(output_path)
        sentences = approximate_sentence_timings(text, duration)
        return duration, sentences
