from typing import Tuple, List

import config
from src.logger import logger
from src.narration.base import BaseLLMProvider
from src.narration.helpers import strip_markdown, strip_emojis, extract_emphasis_from_text
from src.reddit.models import RedditPost


def get_llm_provider() -> BaseLLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    provider_name = config.LLM_PROVIDER.lower()
    
    if provider_name == "groq":
        from src.narration.groq import GroqProvider
        return GroqProvider()
    elif provider_name in ("openai", "deepseek", "openrouter", "ollama"):
        from src.narration.openai_like import OpenAILikeProvider
        return OpenAILikeProvider()
    elif provider_name == "gemini":
        from src.narration.gemini import GeminiProvider
        return GeminiProvider()
    else:
        logger.warning(f"Unknown LLM provider '{config.LLM_PROVIDER}'. Defaulting to Groq.")
        from src.narration.groq import GroqProvider
        return GroqProvider()


def generate_script_with_fallback(
    post: RedditPost, 
    mode: str = None, 
    style: str = None
) -> dict:
    """
    Generate narration script and metadata from a Reddit post.
    Falls back to a clean reading of the post if the LLM provider fails.
    
    Returns:
        Dict containing script and metadata fields.
    """
    mode = mode or config.NARRATION_MODE
    style = style or config.CAPTION_STYLE
    
    try:
        provider = get_llm_provider()
        parsed = provider.generate_narration(post, mode, style)
        
        # Verify result is valid
        if parsed and parsed.get("narration") and len(parsed["narration"].split()) >= 5:
            return parsed
        else:
            raise ValueError("Generated script is too short or empty")
            
    except Exception as e:
        logger.warning(f"LLM script generation failed ({e}). Using local meme review reaction fallback.")
        import random
        import re
        
        clean_title = strip_markdown(strip_emojis(post.title))
        # Strip any RSS metadata remnants from body if present
        clean_body = re.sub(r"submitted by\s+/u/\S+.*", "", strip_markdown(strip_emojis(post.selftext)), flags=re.IGNORECASE).strip()
        clean_body = re.sub(r"\[link\]|\[comments\]", "", clean_body, flags=re.IGNORECASE).strip()
        
        # Meme commentary hook templates for viral short-form reaction
        commentary_templates = [
            "Wait, why is this meme ACTUALLY so relatable? {title}.",
            "Okay, who AUTHORIZED this level of relatable content? {title}.",
            "I had to read this meme TWICE to get it. {title}.",
            "This represents my ENTIRE life in one single image. {title}.",
            "There is NO WAY this actually happened. {title}.",
            "Why does this meme HIT so hard though? {title}."
        ]
        
        if clean_body and len(clean_body.split()) >= 4 and "submitted by" not in clean_body.lower():
            narration = f"{clean_title}. {clean_body}"
        else:
            template = random.choice(commentary_templates)
            narration = template.format(title=clean_title)
            
        title = clean_title[:55]
        emphasis = extract_emphasis_from_text(narration, limit=4)
        
        logger.info("Local meme commentary fallback narration generated successfully")
        return {
            "title": title,
            "narration": narration,
            "emphasis": emphasis,
            "yt_title": f"{clean_title} #shorts #meme",
            "yt_hook": f"Check out this meme from r/{post.subreddit}!",
            "yt_summary": clean_title,
            "yt_category": "Entertainment",
            "yt_content_tags": ["memes", "funny", "shorts", post.subreddit]
        }
