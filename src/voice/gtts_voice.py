from pathlib import Path
from typing import Tuple, List

from src.logger import logger
from src.voice.base import BaseVoiceProvider, SentenceTiming
from src.voice.edge import _ffprobe_duration
from src.voice.helpers import approximate_sentence_timings


class GTTSVoiceProvider(BaseVoiceProvider):
    """
    Google Translate TTS (gTTS) Provider.
    Completely free, requires no API key, and works reliably in cloud environments
    such as GitHub Actions runners without WebSocket handshake or 403 IP block issues.
    """

    def synthesize(
        self, 
        text: str, 
        output_path: Path, 
        voice: str | None = None
    ) -> Tuple[float, List[SentenceTiming]]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Synthesizing voiceover with Google TTS (gTTS fallback)")

        try:
            from gtts import gTTS
            # lang defaults to 'en', tld='com' (can use 'co.uk', 'ca', etc.)
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(str(output_path))
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            raise e

        duration = _ffprobe_duration(output_path)
        sentences = approximate_sentence_timings(text, duration)
        logger.info(f"Generated gTTS voiceover: {duration:.2f}s ({len(sentences)} sentences)")
        return duration, sentences
