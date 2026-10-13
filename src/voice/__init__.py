from pathlib import Path
from typing import Tuple, List

import config
from src.logger import logger
from src.voice.base import BaseVoiceProvider, SentenceTiming


def get_voice_provider() -> BaseVoiceProvider:
    """Factory function to instantiate the configured TTS provider."""
    provider_name = config.TTS_PROVIDER.lower()
    
    if provider_name == "edge":
        from src.voice.edge import EdgeVoiceProvider
        return EdgeVoiceProvider()
    elif provider_name == "elevenlabs":
        from src.voice.elevenlabs import ElevenLabsVoiceProvider
        return ElevenLabsVoiceProvider()
    elif provider_name == "openai":
        from src.voice.openai_tts import OpenAITTSVoiceProvider
        return OpenAITTSVoiceProvider()
    elif provider_name in ("gtts", "google"):
        from src.voice.gtts_voice import GTTSVoiceProvider
        return GTTSVoiceProvider()
    else:
        logger.warning(f"Unknown/unsupported voice provider '{config.TTS_PROVIDER}'. Defaulting to Edge.")
        from src.voice.edge import EdgeVoiceProvider
        return EdgeVoiceProvider()


def synthesize_voiceover_with_fallback(
    text: str, 
    output_path: Path | None = None, 
    voice: str | None = None
) -> Tuple[float, List[SentenceTiming]]:
    """
    Synthesize voiceover from text, saving to output_path.
    Tries configured TTS provider first, with multi-stage fallback (Edge TTS -> gTTS).
    """
    if output_path is None:
        output_path = config.OUTPUT_DIR / "voiceover.mp3"
        
    configured_provider_name = config.TTS_PROVIDER.lower()
    
    # 1. Try configured provider
    try:
        provider = get_voice_provider()
        duration, timings = provider.synthesize(text, output_path, voice)
        return duration, timings
    except Exception as e:
        logger.warning(f"Configured TTS provider '{config.TTS_PROVIDER}' failed: {e}.")

    # 2. Try Edge TTS if it wasn't already the failing provider
    if configured_provider_name != "edge":
        logger.info("Attempting fallback to Edge TTS...")
        try:
            from src.voice.edge import EdgeVoiceProvider
            fallback_provider = EdgeVoiceProvider()
            fallback_voice = "en-US-AndrewNeural"
            duration, timings = fallback_provider.synthesize(text, output_path, fallback_voice)
            return duration, timings
        except Exception as fe:
            logger.warning(f"Fallback Edge TTS failed: {fe}")

    # 3. Fallback to gTTS (Google Translate TTS - cloud-friendly, zero credentials required)
    logger.info("Attempting fallback to Google TTS (gTTS)...")
    try:
        from src.voice.gtts_voice import GTTSVoiceProvider
        gtts_provider = GTTSVoiceProvider()
        duration, timings = gtts_provider.synthesize(text, output_path)
        return duration, timings
    except Exception as ge:
        logger.error(f"Fallback gTTS also failed: {ge}")

    # 4. Final attempt: OpenAI TTS if API key is present
    if config.OPENAI_API_KEY:
        try:
            logger.info("Attempting fallback to OpenAI TTS...")
            from src.voice.openai_tts import OpenAITTSVoiceProvider
            openai_provider = OpenAITTSVoiceProvider()
            duration, timings = openai_provider.synthesize(text, output_path)
            return duration, timings
        except Exception as oe:
            logger.error(f"Fallback OpenAI TTS failed: {oe}")

    raise RuntimeError("All TTS providers (configured, Edge TTS, gTTS) failed to synthesize audio.")

