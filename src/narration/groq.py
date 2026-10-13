from typing import Tuple, List

from groq import Groq
import config
from src.logger import logger
from src.narration.base import BaseLLMProvider
from src.narration.helpers import parse_structured_response
from src.narration.prompts import SYSTEM_PROMPT_COMMENTARY, SYSTEM_PROMPT_NATURAL, get_user_prompt
from src.reddit.models import RedditPost


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider for script generation."""

    def __init__(self) -> None:
        self.api_key = config.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not configured. GroqProvider may fail.")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def generate_narration(
        self, 
        post: RedditPost, 
        mode: str = "commentary", 
        style: str = "chaotic"
    ) -> dict:
        if not self.client:
            raise ValueError("Groq client not initialized (missing API key)")

        system_prompt = SYSTEM_PROMPT_COMMENTARY if mode == "commentary" else SYSTEM_PROMPT_NATURAL
        user_prompt = get_user_prompt(post.subreddit, post.title, post.selftext)

        models_to_try = [
            config.LLM_MODEL,
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]
        seen = set()
        models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]
        
        last_err = None
        for m_name in models_to_try:
            logger.info(f"Sending request to Groq model: {m_name}")
            try:
                completion = self.client.chat.completions.create(
                    model=m_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=2048,
                    timeout=30,
                )
                response = completion.choices[0].message.content
                if not response:
                    raise ValueError("Received empty response from Groq")
                    
                return parse_structured_response(response, default_title=post.title)

            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                # Catch 404, 400, model decommissioned, or model not found
                if any(k in err_str for k in ("404", "400", "model_decommissioned", "not_found", "model_not_found", "deprecated", "does not exist")):
                    logger.warning(f"Groq model '{m_name}' unavailable ({e}). Trying next fallback model...")
                    continue
                raise e
        if last_err:
            logger.error(f"Groq API error: {last_err}")
            raise last_err

