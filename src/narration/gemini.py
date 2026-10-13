from typing import Tuple, List

import config
from src.logger import logger
from src.narration.base import BaseLLMProvider
from src.narration.helpers import parse_structured_response
from src.narration.prompts import SYSTEM_PROMPT_COMMENTARY, SYSTEM_PROMPT_NATURAL, get_user_prompt
from src.reddit.models import RedditPost


class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider for script generation."""

    def __init__(self) -> None:
        self.api_key = config.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not configured. GeminiProvider may fail.")

    def generate_narration(
        self, 
        post: RedditPost, 
        mode: str = "commentary", 
        style: str = "chaotic"
    ) -> dict:
        if not self.api_key:
            raise ValueError("Gemini client not initialized (missing API key)")

        system_prompt = SYSTEM_PROMPT_COMMENTARY if mode == "commentary" else SYSTEM_PROMPT_NATURAL
        user_prompt = get_user_prompt(post.subreddit, post.title, post.selftext)

        models_to_try = [config.LLM_MODEL, "gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        seen = set()
        models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        # Try google.genai first
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            last_err = None
            for m_name in models_to_try:
                logger.info(f"Sending request to google.genai model: {m_name}")
                try:
                    response = client.models.generate_content(
                        model=m_name,
                        contents=[user_prompt],
                        config=dict(
                            system_instruction=system_prompt,
                            temperature=0.8,
                            max_output_tokens=600,
                        )
                    )
                    response_text = response.text
                    if response_text:
                        return parse_structured_response(response_text, default_title=post.title)
                except Exception as e:
                    last_err = e
                    logger.warning(f"google.genai model '{m_name}' failed ({e}). Trying fallback model...")
                    continue
            if last_err:
                raise last_err
        except ImportError:
            pass

        # Fallback to google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            last_err = None
            for m_name in models_to_try:
                logger.info(f"Sending request to Gemini model: {m_name}")
                try:
                    model = genai.GenerativeModel(
                        model_name=m_name,
                        system_instruction=system_prompt
                    )
                    response = model.generate_content(
                        user_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.8,
                            max_output_tokens=600,
                        )
                    )
                    response_text = response.text
                    if response_text:
                        return parse_structured_response(response_text, default_title=post.title)
                except Exception as e:
                    last_err = e
                    logger.warning(f"Gemini model '{m_name}' failed ({e}). Trying fallback model...")
                    continue
            if last_err:
                raise last_err
        except ImportError:
            raise ImportError(
                "Neither 'google-genai' nor 'google-generativeai' is installed."
            )

